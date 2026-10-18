# Refatoração Arquitetural Automatizada com Skills — `refactor-arch`

Solução do desafio **Criação de Skills — Refatoração Arquitetural Automatizada** (enunciado original no [repositório base](https://github.com/devfullcycle/mba-ia-refactor-projects-skill)).

A skill `refactor-arch` (Claude Code) analisa uma codebase de backend, audita-a contra um catálogo de anti-patterns, gera um relatório por severidade e — **após confirmação humana** — refatora o projeto para MVC, validando que a aplicação continua funcionando. Ela foi executada nos 3 projetos legados deste repositório (Python/Flask × 2 e Node.js/Express).

| Entregável | Local |
|---|---|
| Skill (idêntica nos 3 projetos) | `*/.claude/skills/refactor-arch/` |
| Código refatorado | `code-smells-project/`, `ecommerce-api-legacy/`, `task-manager-api/` |
| Relatórios de auditoria (Fases 1 e 2) | [reports/audit-project-1.md](reports/audit-project-1.md), [reports/audit-project-2.md](reports/audit-project-2.md), [reports/audit-project-3.md](reports/audit-project-3.md) (+ 2ª execução: [audit-project-3-rerun.md](reports/audit-project-3-rerun.md)) |

---

## A) Análise Manual

Antes de escrever a skill, os três projetos foram lidos arquivo a arquivo. Os problemas abaixo são os de maior impacto encontrados em cada um. Eles viraram a base do catálogo de anti-patterns. Valores de segredos encontrados no código são omitidos propositalmente.

### Projeto 1 — `code-smells-project` (Python/Flask, E-commerce)

| Severidade | Problema | Onde | Por que é relevante |
|---|---|---|---|
| CRITICAL | **SQL Injection** em praticamente todas as queries (concatenação de strings com dados do request) | `models.py:28, 47-50, 109-111, 289-299…` | Permite bypass de login (`' OR '1'='1`) e leitura/destruição arbitrária do banco |
| CRITICAL | **Endpoint `/admin/query` executa SQL arbitrário** e `/admin/reset-db` apaga tudo, ambos sem autenticação | `app.py:47-78` | É um backdoor: qualquer cliente anônimo controla o banco |
| CRITICAL | **Senhas em texto puro** (gravação, comparação no `WHERE` e seed) e devolvidas em `GET /usuarios` | `models.py:83, 99, 109-129`; `database.py:75-83` | Vazamento direto de credenciais de todos os usuários |
| CRITICAL | **`SECRET_KEY` hardcoded** e exposta no `/health` junto de `debug` e `db_path` | `app.py:7`; `controllers.py:285-289` | Segredo no repositório e entregue a qualquer cliente |
| CRITICAL | **God File**: `models.py` mistura SQL, regras de negócio (desconto, estoque) e formatação de 4 domínios | `models.py:1-314` | Nada é testável em isolamento; qualquer mudança afeta tudo |
| HIGH | **Conexão SQLite global** compartilhada entre threads (`check_same_thread=False`) | `database.py:4-11` | Estado global mutável: corridas e transações vazando entre requisições |
| HIGH | Pedido grava pedido + itens + estoque **sem transação** | `models.py:133-169` | Falha parcial deixa o banco inconsistente |
| MEDIUM | **N+1**: uma query por pedido e outra por item | `models.py:171-233` | Listagens degradam com pedidos × itens |
| MEDIUM | Validação duplicada entre criar/atualizar produto e sem checagem de tipo (string em `preco` → 500) | `controllers.py:24-90` | Regras divergem e entradas inválidas derrubam a requisição |
| MEDIUM | `try/except Exception` em todo handler devolvendo `str(e)` | `controllers.py` (16 handlers) | Vaza detalhes internos; nenhum tratamento central |
| LOW | **Magic numbers** nas faixas de desconto (10000/0.1, 5000/0.05, 1000/0.02) | `models.py:256-262` | Regra de negócio escondida em literais |
| LOW | Imports não usados (`sqlite3`, `os`) e `id` sombreando o builtin | `models.py:2`; `database.py:2`; `controllers.py:14…` | Ruído e risco de bugs sutis |

### Projeto 2 — `ecommerce-api-legacy` (Node.js/Express, LMS com checkout)

| Severidade | Problema | Onde | Por que é relevante |
|---|---|---|---|
| CRITICAL | **Credenciais de produção hardcoded** (senha do banco, chave `pk_live_` do gateway, usuário SMTP) | `src/utils.js:1-7` | Segredos de produção expostos no repositório |
| CRITICAL | **"Criptografia" caseira** (`badCrypto`: base64 repetido e truncado) e senha padrão `123456` | `src/utils.js:17-23`; `src/AppManager.js:68` | Senhas triviais de recuperar e contas com senha conhecida |
| CRITICAL | **Número completo do cartão e chave do gateway em log** | `src/AppManager.js:45` | Violação direta de PCI-DSS |
| CRITICAL | **God Class `AppManager`**: conexão, schema, seeds, rotas e regras de checkout | `src/AppManager.js:4-139` | Monólito impossível de testar ou evoluir |
| HIGH | Checkout grava matrícula, pagamento e auditoria **sem transação**; deleção de usuário **deixa órfãos** (a própria resposta admite) | `src/AppManager.js:50-63, 131-137` | Dados financeiros inconsistentes |
| HIGH | Relatório financeiro e deleção de usuários **sem autenticação** | `src/AppManager.js:80, 131` | Qualquer cliente vê dados financeiros e apaga usuários |
| MEDIUM | **N+1** no relatório (query por curso, por matrícula, por pagamento) | `src/AppManager.js:83-128` | 1 + C + 2·M queries |
| MEDIUM | **Callback hell** com contadores manuais (ordem do relatório não determinística) | `src/AppManager.js:37-77, 83-128` | Fluxo ilegível; resposta varia entre chamadas |
| MEDIUM | Erros de callback ignorados (`enrollments.length` com `err` → crash do processo) | `src/AppManager.js:92, 133` | Uma falha de banco derruba a API |
| LOW | Nomes de 1–3 letras (`u`, `e`, `p`, `cc`, `cid`) e nomes enganosos | `src/AppManager.js:29-33` | Leitura difícil |
| LOW | Código morto: `totalRevenue`, `globalCache` (só escrito), `dbUser`/`dbPass` nunca usados | `src/utils.js:2-25` | Ruído e falsa dependência |

### Projeto 3 — `task-manager-api` (Python/Flask + SQLAlchemy, Task Manager)

| Severidade | Problema | Onde | Por que é relevante |
|---|---|---|---|
| CRITICAL | **MD5 sem salt** para senhas | `models/user.py:27-32` | Hashes quebráveis em segundos |
| CRITICAL | **Hash da senha devolvido** em `/users/<id>`, `POST /users`, `PUT /users`, `/login` | `models/user.py:16-25` | Entrega o hash (fraco) de qualquer usuário |
| CRITICAL | `SECRET_KEY` e **senha SMTP hardcoded** | `app.py:13`; `services/notification_service.py:7-10` | Segredos versionados |
| HIGH | **Rotas fazem papel de controller**: validação, queries ORM e estatísticas nos handlers (200–300 linhas por arquivo) | `routes/*.py` | A organização em pastas esconde a falta de camadas |
| HIGH | **Token falso** `'fake-jwt-token-' + id` | `routes/user_routes.py:210` | Qualquer cliente forja autenticação |
| MEDIUM | **APIs deprecated**: `Query.get()` (16×, `LegacyAPIWarning`) e `datetime.utcnow()` (22×) | `routes/*.py`, `models/*.py` | Quebra em versões futuras do SQLAlchemy/Python |
| MEDIUM | **N+1** em `GET /tasks` (usuário e categoria por task) e 12 `count()` no relatório | `routes/task_routes.py:41-57`; `routes/report_routes.py:15-28` | Performance degrada com o volume |
| MEDIUM | Regra "atrasada" **duplicada 6×** enquanto `Task.is_overdue()` existe sem uso | `routes/task_routes.py:30-39…` | Mudanças precisam ser replicadas |
| MEDIUM | `except:` genérico em 12 pontos | `routes/*.py`; `utils/helpers.py` | Esconde erros reais |
| LOW | Imports e dependências não usados (`os, sys, json, time`, `marshmallow`, `requests`); `NotificationService` nunca usado | `app.py:7`; `requirements.txt` | Superfície de dependências desnecessária |
| LOW | Magic numbers/strings (status, roles, limites 3/200, prioridade `<= 2`) repetidos nas rotas | `routes/*.py` | Regras espalhadas e inconsistentes |

---

## B) Construção da Skill

### Estrutura

```
.claude/skills/refactor-arch/
├── SKILL.md                          # orquestração das 3 fases + regras invioláveis
└── references/
    ├── project-analysis.md           # Fase 1: heurísticas de linguagem, framework, banco, domínio, arquitetura
    ├── anti-patterns-catalog.md      # Fase 2: 24 anti-patterns com sinais de detecção e severidade
    ├── report-template.md            # Fase 2: formato obrigatório do relatório
    ├── mvc-guidelines.md             # Fase 3: camadas, estruturas alvo por stack, regras de compatibilidade
    ├── refactoring-playbook.md       # Fase 3: 16 transformações com código antes/depois
    └── validation.md                 # Fase 3: baseline, boot, smoke test e re-auditoria
```

| Área de conhecimento exigida | Arquivo |
|---|---|
| Análise de projeto | `project-analysis.md` |
| Catálogo de anti-patterns | `anti-patterns-catalog.md` |
| Template de relatório | `report-template.md` |
| Guidelines de arquitetura MVC | `mvc-guidelines.md` |
| Playbook de refatoração | `refactoring-playbook.md` |
| *(extra)* Protocolo de validação | `validation.md` |

### Decisões de design

- **`SKILL.md` como orquestrador enxuto.** O SKILL.md diz *o que* fazer e *quando* ler cada referência. O conhecimento de domínio fica nos arquivos de referência, carregados sob demanda em cada fase (*progressive disclosure*). Assim o contexto fica pequeno e cada fase tem instruções focadas.
- **Regras invioláveis no topo**: as Fases 1–2 são somente leitura; nenhum segredo é reproduzido (o relatório usa `<redacted>`); cada finding precisa de arquivo:linha conferidos; o contrato da API é preservado; nunca se declara sucesso sem executar a validação.
- **Ponto de parada explícito**: a Fase 2 termina com `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]`, e a instrução proíbe iniciar a Fase 3 na mesma resposta.
- **IDs cruzados**: cada anti-pattern (`AP-xx`) aponta para uma transformação (`T-xx`), e cada finding do relatório cita ambos. A Fase 3 vira um mapeamento finding → transformação, o que torna o resumo final rastreável.
- **Compatibilidade explícita**: o `mvc-guidelines.md` lista as únicas mudanças de contrato permitidas (todas de segurança), e elas precisam ser anunciadas no relatório antes da confirmação.
- **Validação por baseline**: antes de editar, a skill sobe a versão original e grava as respostas de todos os endpoints. Depois compara a versão refatorada requisição a requisição (status + formato do JSON + valores de cálculo).

### Anti-patterns do catálogo e por quê

| Severidade | Anti-patterns | Motivação |
|---|---|---|
| CRITICAL (6) | AP-01 segredos hardcoded · AP-02 SQL Injection · AP-03 God Class · AP-04 endpoint perigoso · AP-05 senha insegura · AP-06 exposição de dados sensíveis | Encontrados nos 3 projetos; comprometem segurança ou toda a separação de responsabilidades |
| HIGH (6) | AP-07 fat controller · AP-08 estado global · AP-09 acoplamento/sem DI · AP-10 sem transação/órfãos · AP-11 config insegura · AP-12 auth falsa/ausente | Violações MVC/SOLID que impedem testes e geram inconsistência |
| MEDIUM (8) | AP-13 N+1 · AP-14 agregação ineficiente · AP-15 validação · AP-16 duplicação · AP-17 error handling · **AP-18 APIs deprecated** · AP-19 callback hell · AP-20 print/console.log | Performance, padronização e manutenção; AP-18 tem tabela de APIs legadas → substituto moderno para Python, SQLAlchemy, Flask, Node e Express |
| LOW (4) | AP-21 magic numbers · AP-22 nomes ruins · AP-23 código morto · AP-24 código não idiomático | Legibilidade |

Cada entrada traz **sinais de detecção concretos** (padrões de grep por stack, como "query SQL concatenada com `+`", "`.query.get(`", "`let x = {}` em escopo de módulo") e exemplos do que **não** é finding, para evitar falsos positivos.

### Como a skill é agnóstica de tecnologia

- A Fase 1 **detecta** a stack por manifestos e imports (tabelas para Python, Node/TS, Java, Go, Ruby, PHP, C#) em vez de presumir.
- Os sinais de detecção do catálogo vêm em versões para Python **e** JS, e são descritos por conceito ("query dentro de loop sobre resultado de outra query"), não por sintaxe de um framework.
- O `mvc-guidelines.md` define a arquitetura alvo por **responsabilidade de camada** e traz estruturas concretas para Flask com SQL cru, Flask + SQLAlchemy e Express, além de orientação para Django, FastAPI e Spring.
- Uma **tabela de adaptação** muda a estratégia conforme o nível de organização: monolito → criar camadas; parcialmente em camadas → preservar pacotes e criar só o que falta. Por isso o Projeto 3 manteve `models/`, `routes/`, `services/` e `utils/` e ganhou `controllers/`, `config/` e `middlewares/`.
- O script de smoke test da validação usa só a biblioteca padrão do Python e fala HTTP, então funciona para qualquer backend.

### Desafios encontrados e como foram resolvidos

| Desafio | Solução (incorporada à skill) |
|---|---|
| A porta 5000 do macOS é ocupada pelo AirPlay, e a versão original tem porta hardcoded | `validation.md`: verificar a porta antes de subir; versão original via wrapper (`app.run(port=…)`) sem editar código; versão refatorada lê `PORT` |
| Com `debug=True`, o reloader do Werkzeug não funciona dentro de `python -c` | Wrapper sempre com `debug=False` |
| Um `pkill -f` não encerrou o servidor anterior, e a validação seguinte bateu no processo velho | Encerrar processos **pela porta** (`lsof -t -iTCP:<porta>`) e checar a porta antes de cada boot |
| Padronizar erros com `"sucesso": false` fazia o comparador acusar falsa regressão | Regra de compatibilidade: **chaves novas são compatíveis**; só chaves removidas ou renomeadas contam como quebra |
| O relatório financeiro do Projeto 2 tinha ordem não determinística (corrida de callbacks) | Comparar listagens não determinísticas como conjunto e registrar a ordenação como mudança intencional |
| O Projeto 3 tinha bancos existentes com hash MD5: trocar o algoritmo invalidaria as contas | Playbook T-04 ganhou a **migração transparente**: o hash legado é verificado uma vez e regravado com scrypt |
| Endpoints que passam a exigir token quebrariam a comparação com a baseline | Incluir o header já no spec da baseline (a versão original ignora headers extras) |
| No zsh, `-H $VAR` não é dividido em palavras e o curl enviou requisições sem `Content-Type` | Nota no `validation.md`: passar headers literalmente |
| **Feedback da avaliação:** no P3 o relatório marcou a autenticação falsa como HIGH, mas a Fase 3 só assinou o token. Nada o verificava e `DELETE /users` e a troca de `role` continuavam abertos, enquanto no P2 a mesma skill protegeu as rotas destrutivas. A causa: a nota do AP-12 trazia "token assinado" como **exemplo** de mínimo seguro, e o T-06 só mostrava a emissão do token | T-06 ganhou o **mínimo seguro obrigatório** (credencial verificada no servidor **e** todas as operações administrativas protegidas, *fail-closed*, com a lista do que não conta como correção). A Fase 3 proíbe deixar AP-04/AP-12 como recomendação. A Fase 2 ganhou a seção "Administrative Operations". A validação exige testes negativos 401/403. A skill rodou de novo no P3 (ver abaixo) |

---

## C) Resultados

### Resumo das auditorias

| Projeto | Stack detectada | Arquivos / LOC | CRITICAL | HIGH | MEDIUM | LOW | Total |
|---|---|---|---|---|---|---|---|
| 1 — code-smells-project | Python + Flask 3.1.1 (sqlite3 cru) | 4 / ~780 | 6 | 5 | 6 | 4 | **21** |
| 2 — ecommerce-api-legacy | Node.js + Express 4.18 (sqlite3 callbacks) | 3 / ~180 | 4 | 5 | 5 | 3 | **17** |
| 3 — task-manager-api | Python + Flask 3.0 + Flask-SQLAlchemy 3.1 | 12 / ~1155 | 3 | 5 | 7 | 4 | **19** |

APIs deprecated: o Projeto 3 tem `Query.get()` e `datetime.utcnow()`. Nos Projetos 1 e 2 nenhuma foi encontrada, e o relatório lista o que foi verificado.

### Antes / depois

**Projeto 1 — monolito → MVC completo em `src/`**

```
ANTES                         DEPOIS
app.py        (88)            app.py                       # entry point
controllers.py (292)          src/app.py                   # composition root (create_app + DI)
models.py     (314)           src/config/settings.py, constants.py
database.py   (86)            src/database/connection.py (conexão por request), schema.py (schema + seed com hash)
                              src/models/produto_model.py, usuario_model.py, pedido_model.py
                              src/controllers/produto_, usuario_, pedido_, relatorio_, sistema_controller.py
                              src/views/produto_, usuario_, pedido_, sistema_routes.py
                              src/services/notification_service.py
                              src/middlewares/error_handler.py
                              src/utils/errors.py, validators.py
```

**Projeto 2 — God Class → MVC com composição explícita**

```
ANTES                         DEPOIS
src/app.js        (14)        src/server.js                # entry point (npm start)
src/AppManager.js (141)       src/app.js                   # composition root (createApp)
src/utils.js      (25)        src/config/index.js
                              src/database/connection.js (Promises + transações), schema.js
                              src/models/user, course, enrollment, payment, auditLogModel.js
                              src/controllers/checkout, report, userController.js
                              src/services/paymentGateway.js, passwordHasher.js (scrypt)
                              src/routes/index.js
                              src/middlewares/errorHandler.js, asyncHandler.js, requireAdminToken.js
                              src/utils/errors.js, logger.js
```

**Projeto 3 — camadas parciais → MVC (pacotes existentes preservados)**

```
ANTES                                   DEPOIS
app.py (config + bootstrap no import)   app.py (create_app + entry point)
—                                       config/settings.py                         [novo]
models/ task, user, category            models/ task, user, category (+ stats.py)  [corrigidos]
routes/ task, user, report (fat)        routes/ task, user, report, category, system (finos)
—                                       controllers/ task, user, report, category  [novo]
services/notification_service (morto)   services/notification_service (injetado), token_service
utils/helpers (quase tudo sem uso)      utils/ constants, validators, errors, time, helpers
—                                       middlewares/error_handler.py               [novo]
```

### Checklist de validação

| Item | P1 | P2 | P3 |
|---|---|---|---|
| **Fase 1** — Linguagem detectada corretamente | ✅ Python | ✅ JavaScript/Node | ✅ Python |
| Framework detectado corretamente | ✅ Flask 3.1.1 | ✅ Express 4.18 | ✅ Flask 3.0 + SQLAlchemy |
| Domínio descrito corretamente | ✅ E-commerce | ✅ LMS com checkout | ✅ Task Manager |
| Nº de arquivos condiz com a realidade | ✅ 4 | ✅ 3 | ✅ 12 (+3 `__init__` vazios) |
| **Fase 2** — Relatório segue o template | ✅ | ✅ | ✅ |
| Cada finding tem arquivo e linhas exatos | ✅ | ✅ | ✅ |
| Findings ordenados CRITICAL → LOW | ✅ | ✅ | ✅ |
| Mínimo de 5 findings | ✅ 21 | ✅ 17 | ✅ 19 |
| Detecção de APIs deprecated | ✅ (nenhuma; verificação listada) | ✅ (nenhuma; verificação listada) | ✅ `Query.get`, `utcnow` |
| Pausa e pede confirmação antes da Fase 3 | ✅ | ✅ | ✅ |
| **Fase 3** — Estrutura segue padrão MVC | ✅ | ✅ | ✅ |
| Config extraída (sem hardcoded) | ✅ `src/config` | ✅ `src/config` | ✅ `config/settings.py` |
| Models abstraem dados | ✅ | ✅ | ✅ |
| Views/Routes separadas | ✅ `src/views` | ✅ `src/routes` | ✅ `routes/` |
| Controllers concentram o fluxo | ✅ | ✅ | ✅ |
| Error handling centralizado | ✅ | ✅ | ✅ |
| Entry point claro | ✅ `app.py` | ✅ `src/server.js` | ✅ `app.py` |
| Aplicação inicia sem erros | ✅ | ✅ | ✅ |
| Endpoints originais respondem corretamente | ✅ 34/38 (+4 intencionais) | ✅ 7/10 (+3 intencionais) | ✅ 40/44 (+4 intencionais); 2ª execução 39/39 |
| Operações administrativas exigem credencial (critério do T-06 reforçado) | ⚠️ `/admin/reset-db` protegido; `GET /relatorios/vendas` (financeiro) ainda aberto — pendente de nova execução | ✅ `X-Admin-Token` | ✅ Bearer + admin (2ª execução, 22/22 testes negativos) |

### Logs da validação (aplicações rodando após a refatoração)

Cada projeto foi validado com o protocolo do `validation.md`: baseline da versão original → boot da versão refatorada → mesmo spec de requisições → comparação.

<details>
<summary><b>Projeto 1</b> — 38 requisições, 34 idênticas; as 4 diferenças são mudanças de segurança anunciadas</summary>

```
2026-10-09 22:16:07 WARNING src.database.schema: SEED_ADMIN_PASSWORD não definida: senha aleatória gerada para admin@loja.com
 * Serving Flask app 'src.app'
 * Debug mode: off
 * Running on http://127.0.0.1:5055
2026-10-09 22:16:10 INFO src.services.notification_service: Notificação: pedido 1 criado para usuário 2 (email/sms/push)

✓ GET / 200 -> 200
✗ GET /health 200 -> 200            # intencional: sem secret_key/db_path/debug
✓ GET /produtos 200 -> 200
✓ GET /produtos/busca?q=Mouse 200 -> 200
✓ POST /produtos 201 -> 201         (+ 3 casos 400)
✓ PUT /produtos/2 200 -> 200        (+ 404 e 400)
✗ GET /usuarios 200 -> 200          # intencional: sem campo senha
✗ GET /usuarios/1 200 -> 200        # intencional: sem campo senha
✓ POST /login 200 -> 200            (+ 401 e 400)
✓ POST /pedidos 201 -> 201          (+ estoque insuficiente, produto inexistente, sem itens: 400)
✓ GET /pedidos, /pedidos/usuario/2, PUT status, GET /relatorios/vendas -> 200
✓ DELETE /produtos/10 200, DELETE /produtos/999 404
✗ POST /admin/reset-db 200 -> 403   # intencional: exige X-Admin-Token
34/38 matched
```
Valores de `/relatorios/vendas` idênticos à baseline (faturamento 7899.69, desconto 394.98). Testes adicionais: SQL injection no login → 401; `/admin/query` → 404; quantidade negativa → 400; `preco` string → 400; reset com token → 200.
</details>

<details>
<summary><b>Projeto 2</b> — 10 requisições, 7 idênticas; as 3 diferenças são mudanças anunciadas</summary>

```
> node src/server.js
2026-10-09T21:22:58Z WARN PAYMENT_GATEWAY_KEY não configurada: usando gateway simulado
2026-10-09T21:22:58Z INFO LMS API rodando na porta 3000
2026-10-09T21:23:00Z INFO Processando pagamento de 497 no cartão ****4444
2026-10-09T21:23:00Z INFO Checkout concluído: curso 2, usuário 2, matrícula 2
2026-10-09T21:23:00Z INFO Usuário 2 deletado com matrículas e pagamentos

✗ GET /api/admin/financial-report 200 -> 200   # ordem agora determinística (original variava por corrida)
✓ POST /api/checkout 200 -> 200
✓ POST /api/checkout 400 -> 400   (pagamento recusado)
✓ POST /api/checkout 400 -> 400   (Bad Request)
✓ POST /api/checkout 404 -> 404   (curso inexistente)
✓ POST /api/checkout 200 -> 200   (usuário existente)
✓ GET /api/admin/financial-report 200 -> 200
✓ DELETE /api/users/2 200 -> 200
✗ GET /api/admin/financial-report 200 -> 200   # sem aluno "Unknown" órfão (deleção em cascata)
✗ DELETE /api/users/999 200 -> 404             # antes respondia "deletado" para id inexistente
7/10 matched
```
Testes adicionais: rotas admin sem token ou com token errado → 403 (e bloqueadas se `ADMIN_TOKEN` não configurado); JSON inválido → 400; cartão numérico (antes derrubava o processo) → 200; e-mail inválido → 400.
</details>

<details>
<summary><b>Projeto 3</b> — 44 requisições, 40 idênticas; as 4 diferenças são a remoção do hash de senha</summary>

```
Seed concluído com sucesso!   (executado com -W error::DeprecationWarning)
  3 usuários
  4 categorias
  10 tasks
 * Running on http://127.0.0.1:5056   (executado com -W always: nenhum warning)

✓ GET / · /health · /tasks · /tasks/1 · /tasks/search (2) · /tasks/stats       200
✓ POST /tasks 201 (+ 400 título curto, 400 status, 404 usuário, 400 data)
✓ PUT /tasks/1 200 (+ 404, 400)
✓ GET /users 200 · /users/999 404 · POST /users 409/400/400 · PUT /users/2 400
✗ GET /users/1 · POST /users · PUT /users/2 · POST /login    # intencional: sem "password"
✓ POST /login 401 / 400
✓ GET /reports/summary · /reports/user/1 200 · /reports/user/999 404
✓ GET/POST/PUT/DELETE /categories (+ 400 e 404)
✓ DELETE /tasks/2 · /users/3 200, ids inexistentes 404
40/44 matched — value diffs (ignorando timestamps e password): none
```
Testes adicionais: login com banco legado (hash MD5) → 200 e hash migrado para `scrypt`; `priority` string → 400 (antes 500); `/tasks/search?priority=abc` → 400 (antes 500); `PUT /categories/1` sem corpo → 400 (antes 500).
</details>

<details>
<summary><b>Projeto 3 — 2ª execução</b> (após reforço do T-06): 39/39 idênticos à baseline com token de admin; 22/22 testes negativos de autorização</summary>

Relatório: [audit-project-3-rerun.md](reports/audit-project-3-rerun.md) — 3 HIGH (operações administrativas abertas, token nunca verificado, senha fixa do admin no seed) e 1 MEDIUM (validação de `name`/`active`). A Fase 3 criou `middlewares/auth.py` (`require_auth`, `require_admin`, usuário recarregado do banco a cada requisição), `TokenService.verify` com expiração, regras "dono ou admin" e "`role`/`active` só admin" no controller, e o seed com `SEED_ADMIN_PASSWORD` ou senha aleatória.

```
401 DELETE /users/3   sem token · token inválido · token adulterado · esquema "Token"
403 DELETE /users/3   token de user · token de manager        → GET /users/3 continua 200
401 PUT    /users/1   sem token
403 PUT    /users/1   maria altera e-mail/senha do joao        → joao inalterado
403 PUT    /users/2   auto-promoção a admin · user altera active · manager promove
                                                               → maria continua role=user, active=true
200 PUT    /users/2   maria edita a própria conta
400 PUT    /users/2   nome vazio · active "false" (string)
401 POST   /users     role=admin sem token · token inválido
403 POST   /users     role=admin com token de user
201 POST   /users     cadastro público com perfil padrão
401 PUT    /users/2   token de usuária desativada pelo admin
200 DELETE /users/3   admin
token expirado → 401 · token assinado com outra SECRET_KEY → 401
seed sem SEED_ADMIN_PASSWORD → admin com senha aleatória (senha antiga → 401)
```
</details>

Re-auditoria pós-refatoração (greps de AP-01, 02, 04, 05, 08, 11, 17, 18 nas 3 bases): nenhuma ocorrência real. Restaram apenas falsos positivos justificados, como o uso de MD5 exclusivamente para verificar e migrar hashes legados e o `print` no script CLI `seed.py`.

### Observações sobre o comportamento em stacks diferentes

- **Monolito Python (P1)**: a skill criou a estrutura completa. O maior trabalho foi separar o God File e trocar a conexão global por uma conexão por request com injeção via `create_app`.
- **Node/Express (P2)**: o mesmo catálogo detectou os problemas equivalentes. O AP-19 (callback hell) só se aplica aqui e foi resolvido promisificando o driver, sem trocar de biblioteca. As transações exigiram uma fila, porque o driver usa uma única conexão.
- **Python parcialmente organizado (P3)**: a skill **não** recriou a estrutura do zero. Manteve os pacotes, criou só as camadas ausentes e focou nos problemas que a organização em pastas escondia: rotas gordas, código morto, APIs deprecated e N+1.
- **Contrato preservado**: em todos os casos as mudanças de contrato foram anunciadas no relatório da Fase 2, antes da confirmação, e conferidas na validação.

### Recomendações que ficaram fora do escopo (registradas pela skill)

- P3: as operações administrativas exigem token (2ª execução). Autenticação nas **leituras** e no CRUD de tasks/categorias mudaria o contrato de todos os clientes, por isso ficou como recomendação.
- P1: pelo critério reforçado, `GET /relatorios/vendas` (relatório financeiro) deveria exigir credencial — requer nova execução da skill no P1.
- P1: cancelar um pedido não devolve o estoque (comportamento original preservado; decisão de negócio).
- P3: a senha mínima de 4 caracteres foi mantida (os seeds dependem dela) e virou constante nomeada; recomenda-se aumentar.

---

## D) Como Executar

### Pré-requisitos

- [Claude Code](https://docs.claude.com/en/docs/claude-code/overview) instalado e autenticado (`claude --version`)
- Python 3.10+ (projetos 1 e 3) e Node.js 18+ (projeto 2)

### Executar a skill

A skill fica dentro de cada projeto, em `.claude/skills/refactor-arch/`. Rode o Claude Code **a partir da pasta do projeto**:

```bash
# Projeto 1
cd code-smells-project
claude "/refactor-arch"

# Projeto 2
cd ../ecommerce-api-legacy
claude "/refactor-arch"

# Projeto 3
cd ../task-manager-api
claude "/refactor-arch"
```

Opcionalmente, passe um caminho para salvar o relatório da Fase 2: `claude "/refactor-arch ../reports/audit-project-1.md"`.

A skill imprime a análise (Fase 1) e o relatório (Fase 2) e **para** em `Proceed with refactoring (Phase 3)? [y/n]`. Responda `y` para refatorar ou `n` para encerrar sem alterações.

### Validar a refatoração manualmente

```bash
# Projeto 1 — http://localhost:5000
cd code-smells-project && pip install -r requirements.txt && python app.py
curl localhost:5000/health
curl localhost:5000/produtos

# Projeto 2 — http://localhost:3000 (rotas admin exigem o token)
cd ecommerce-api-legacy && npm install && ADMIN_TOKEN=dev-token npm start
curl -X POST localhost:3000/api/checkout -H 'Content-Type: application/json' \
  -d '{"usr":"Ana","eml":"ana@x.com","pwd":"s3nha","c_id":2,"card":"4111222233334444"}'
curl localhost:3000/api/admin/financial-report -H 'X-Admin-Token: dev-token'

# Projeto 3 — http://localhost:5000
cd task-manager-api && pip install -r requirements.txt
export SEED_ADMIN_PASSWORD='uma-senha-forte' && python seed.py && python app.py
curl localhost:5000/tasks
curl -X POST localhost:5000/login -H 'Content-Type: application/json' -d "{\"email\":\"joao@email.com\",\"password\":\"$SEED_ADMIN_PASSWORD\"}"
# use o token devolvido nas rotas administrativas:
curl -X DELETE localhost:5000/users/3 -H "Authorization: Bearer <token>"
```

> No macOS, se a porta 5000 estiver ocupada pelo AirPlay, use `PORT=5050 python app.py`.

Cada projeto tem um `.env.example` com todas as variáveis de ambiente suportadas.
