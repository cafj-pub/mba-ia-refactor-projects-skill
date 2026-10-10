```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python 3 (sem versão fixada; runtime local 3.11)
Framework:     Flask 3.1.1
Dependencies:  flask-cors 5.0.1
Database:      SQLite (arquivo loja.db) via driver cru sqlite3
Domain:        E-commerce API (produtos, usuários, pedidos, relatório de vendas)
Architecture:  Monolítica com pseudo-camadas — 4 arquivos planos; models.py mistura SQL, regras de negócio e serialização de 4 domínios; app.py mistura config, rotas e endpoints admin com SQL
Entry point:   app.py (python app.py, porta 5000)
Source files:  4 files analyzed (~780 lines)
DB tables:     produtos, usuarios, pedidos, itens_pedido
Endpoints:     19 routes mapped
================================
```

| Método | Rota | Handler |
|---|---|---|
| GET | `/` | app.py:32 |
| GET | `/health` | app.py:30 → controllers.py:264 |
| GET, POST | `/produtos` | app.py:11, 14 |
| GET | `/produtos/busca` | app.py:12 |
| GET, PUT, DELETE | `/produtos/<id>` | app.py:13, 15, 16 |
| GET, POST | `/usuarios` | app.py:18, 20 |
| GET | `/usuarios/<id>` | app.py:19 |
| POST | `/login` | app.py:21 |
| GET, POST | `/pedidos` | app.py:23, 24 |
| GET | `/pedidos/usuario/<usuario_id>` | app.py:25 |
| PUT | `/pedidos/<pedido_id>/status` | app.py:26 |
| GET | `/relatorios/vendas` | app.py:28 |
| POST | `/admin/reset-db` | app.py:47 |
| POST | `/admin/query` | app.py:59 |

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask 3.1.1
Files:   4 analyzed | ~780 lines of code
Date:    2026-10-09
```

## Summary
CRITICAL: 6 | HIGH: 5 | MEDIUM: 6 | LOW: 4

| # | Severity | Anti-pattern | Location |
|---|----------|--------------|----------|
| 1 | CRITICAL | SQL Injection (AP-02) | models.py (17 queries) |
| 2 | CRITICAL | Endpoint perigoso — SQL arbitrário e reset sem auth (AP-04) | app.py:47-78 |
| 3 | CRITICAL | Credenciais / segredos hardcoded (AP-01) | app.py:7, controllers.py:289 |
| 4 | CRITICAL | Senhas em texto puro (AP-05) | models.py:109-111, 126-129; database.py:75-83 |
| 5 | CRITICAL | Exposição de dados sensíveis (AP-06) | models.py:83, 99; controllers.py:285-289 |
| 6 | CRITICAL | God File (AP-03) | models.py:1-314 |
| 7 | HIGH | Estado global mutável — conexão única compartilhada (AP-08) | database.py:4-11 |
| 8 | HIGH | Regra de negócio fora do lugar (AP-07) | controllers.py, models.py |
| 9 | HIGH | Escrita multi-etapa sem transação (AP-10) | models.py:133-169 |
| 10 | HIGH | Configuração de execução insegura (AP-11) | app.py:8-9, 88 |
| 11 | HIGH | Acoplamento forte / sem composition root (AP-09) | app.py:1-30, controllers.py:3, 266 |
| 12 | MEDIUM | Queries N+1 (AP-13) | models.py:171-233, 154-156 |
| 13 | MEDIUM | Validação ausente/duplicada (AP-15) | controllers.py:24-90, 167-201, 237-243 |
| 14 | MEDIUM | Error handling não centralizado, vaza `str(e)` (AP-17) | controllers.py (16 handlers) |
| 15 | MEDIUM | Código duplicado (AP-16) | models.py:12-21, 31-40, 304-313, 177-233 |
| 16 | MEDIUM | Agregação ineficiente (AP-14) | models.py:239-254, controllers.py:268-274 |
| 17 | MEDIUM | print como logging / notificações simuladas (AP-20) | controllers.py, app.py |
| 18 | LOW | Magic numbers / strings (AP-21) | models.py:256-262, controllers.py:47-52, 242, 285-286 |
| 19 | LOW | Nomes pouco expressivos (AP-22) | controllers.py, models.py |
| 20 | LOW | Imports não utilizados / código morto (AP-23) | models.py:2, database.py:2, controllers.py:268 |
| 21 | LOW | Código não idiomático (AP-24) | models.py:146, controllers.py:200 |

## Findings

### #1 [CRITICAL] SQL Injection (AP-02)
File: models.py:28, 47-50, 57-61, 68, 92, 109-111, 126-129, 140, 149-151, 155, 157-166, 174, 188, 192, 220, 224, 279-281, 289-299
Description: Praticamente todas as queries são montadas por concatenação de strings com valores do request (`"SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'"`, `" AND (nome LIKE '%" + termo + "%' ..."`).
Impact: Bypass de login (`' OR '1'='1`), leitura/alteração/destruição arbitrária do banco por qualquer cliente.
Recommendation: Usar placeholders `?` com parâmetros em todas as queries; montar filtros dinâmicos com lista de cláusulas fixas + lista de parâmetros — Playbook T-02.

### #2 [CRITICAL] Endpoint perigoso — execução de SQL arbitrário e reset sem autenticação (AP-04)
File: app.py:59-78, 47-57
Description: `POST /admin/query` executa qualquer SQL enviado no corpo (`cursor.execute(query)`); `POST /admin/reset-db` apaga todas as tabelas sem qualquer autenticação.
Impact: Backdoor — qualquer cliente anônimo lê senhas, altera dados ou apaga o banco inteiro.
Recommendation: Remover `/admin/query`; proteger `/admin/reset-db` com token administrativo configurado por variável de ambiente (desabilitado se não configurado) e mover a lógica para model/controller — Playbook T-06.

### #3 [CRITICAL] Credenciais / segredos hardcoded (AP-01)
File: app.py:7
File: controllers.py:289
Description: `SECRET_KEY` definido como literal no código (`<redacted>`) e repetido literalmente na resposta do health check.
Impact: A chave que assina sessões fica exposta no repositório e para qualquer cliente; impossível rotacionar por ambiente.
Recommendation: Ler `SECRET_KEY` de variável de ambiente em `config/settings.py` (aleatória em dev quando ausente) e nunca devolvê-la — Playbook T-01.

### #4 [CRITICAL] Senhas armazenadas e comparadas em texto puro (AP-05)
File: models.py:109-111, 126-129
File: database.py:31, 75-83
Description: `criar_usuario` grava a senha recebida sem hash; `login_usuario` compara `WHERE senha = '<senha>'`; o seed grava as senhas dos usuários de exemplo em texto puro.
Impact: Qualquer vazamento do banco (ou o próprio `/admin/query`) expõe todas as senhas.
Recommendation: `werkzeug.security.generate_password_hash`/`check_password_hash`; login busca por e-mail e verifica o hash; seed grava hash — Playbook T-04.

### #5 [CRITICAL] Exposição de dados sensíveis em respostas (AP-06)
File: models.py:83, 99
File: controllers.py:285-289
Description: `GET /usuarios` e `GET /usuarios/<id>` devolvem o campo `senha`; `GET /health` devolve `secret_key`, `db_path`, `debug` e `ambiente`.
Impact: Vazamento de credenciais de todos os usuários e de configuração interna para qualquer cliente.
Recommendation: Serializador de usuário sem `senha`; health check só com status e contagens — Playbook T-05.

### #6 [CRITICAL] God File (AP-03)
File: models.py:1-314
Description: Um único módulo concentra acesso a dados, regras de negócio (validação de estoque em 139-146, faixas de desconto em 256-262) e formatação de resposta para 4 domínios distintos (produtos, usuários, pedidos, relatórios). `app.py:47-78` também mistura rotas com SQL direto.
Impact: Impossível testar regras em isolamento; qualquer mudança em um domínio arrisca os demais.
Recommendation: Separar em `models/` por entidade (só SQL e mapeamento), `controllers/` por domínio (regras) e `views/` (rotas) — Playbook T-03.

### #7 [HIGH] Estado global mutável — conexão única compartilhada (AP-08)
File: database.py:4-11
Description: `global db_connection` com `sqlite3.connect(..., check_same_thread=False)` reaproveitada por todas as requisições e threads; schema e seed executados como efeito colateral do primeiro `get_db()`.
Impact: Condições de corrida, transações de uma requisição vazando para outra, impossível isolar em testes.
Recommendation: Conexão por requisição em `flask.g` com teardown; inicialização de schema/seed explícita na factory — Playbook T-08.

### #8 [HIGH] Regra de negócio fora da camada correta (AP-07)
File: controllers.py:24-62, 64-96, 188-220, 237-255, 264-292
File: models.py:139-146, 256-262
Description: Handlers HTTP fazem validação de domínio, disparam "notificações" e acessam o banco diretamente (`health_check`); o model de dados calcula descontos e valida estoque.
Impact: Regras presas ao HTTP e ao SQL, não reutilizáveis nem testáveis isoladamente.
Recommendation: Views finas → controllers com as regras (validação, desconto, estoque, notificações via service) → models só com persistência — Playbook T-07.

### #9 [HIGH] Escrita multi-etapa sem transação (AP-10)
File: models.py:133-169
File: database.py:36-53
Description: `criar_pedido` insere pedido, itens e baixa estoque em várias instruções sem transação explícita; com a conexão global, uma falha no meio deixa escritas pendentes que serão commitadas pela próxima requisição. Tabelas sem `FOREIGN KEY`.
Impact: Pedidos sem itens, estoque baixado sem pedido, registros órfãos.
Recommendation: Bloco transacional único (`with conn:`) para pedido + itens + estoque; FKs no schema — Playbook T-11.

### #10 [HIGH] Configuração de execução insegura (AP-11)
File: app.py:8, 9, 88
Description: `DEBUG = True` fixo, `app.run(host="0.0.0.0", debug=True)` e `CORS(app)` liberado para qualquer origem.
Impact: Debugger do Werkzeug exposto na rede permite execução remota de código; stack traces vazam internals.
Recommendation: `DEBUG`, `HOST`, `PORT` e origens CORS vindos de config com defaults seguros (debug off, 127.0.0.1) — Playbook T-01.

### #11 [HIGH] Acoplamento forte / ausência de composition root (AP-09)
File: app.py:1-30
File: controllers.py:3, 266
Description: Aplicação criada no escopo do módulo, sem factory; controllers importam `get_db` e o módulo `models` diretamente, sem ponto de injeção.
Impact: Não é possível criar a app com outra config/banco (ex.: testes); dependências implícitas entre camadas.
Recommendation: `create_app(settings)` como composition root registrando blueprints, error handlers e banco — Playbook T-08.

### #12 [MEDIUM] Queries N+1 (AP-13)
File: models.py:171-201, 203-233, 154-156
Description: Para cada pedido é feita uma query de itens e, para cada item, outra query de produto (`cursor2`, `cursor3`); em `criar_pedido` o preço é consultado de novo a cada item.
Impact: Número de queries cresce com pedidos × itens; listagens lentas.
Recommendation: Um `SELECT` com `LEFT JOIN` entre pedidos, itens_pedido e produtos, agrupando em memória — Playbook T-09.

### #13 [MEDIUM] Validação ausente ou duplicada (AP-15)
File: controllers.py:24-54, 64-90, 167-174, 188-201, 237-243
Description: Regras de produto copiadas entre criar/atualizar (atualizar não valida nome nem categoria); tipos não checados (`preco` string → `TypeError` → 500); `dados.get` com corpo ausente → 500 em login e status; quantidade dos itens do pedido não validada (quantidade negativa aumenta o estoque).
Impact: Erros 500 para entrada inválida e dados inconsistentes.
Recommendation: Funções de validação únicas no controller/utils, reutilizadas em create/update, com checagem de tipo — Playbook T-14.

### #14 [MEDIUM] Error handling não centralizado e vazando detalhes (AP-17)
File: controllers.py:10-12, 21-22, 60-62, 95-96, 108-109, 125-126, 133-134, 143-144, 164-165, 185-186, 218-220, 226-227, 234-235, 254-255, 261-262, 291-292
File: app.py:77-78
File: models.py:143, 145
Description: Cada handler tem `try/except Exception` genérico devolvendo `str(e)` ao cliente; o model sinaliza erro retornando dicionários `{"erro": ...}`.
Impact: Vazamento de detalhes internos, código repetido, erros de domínio misturados com dados.
Recommendation: Exceções de domínio (`ValidationError`, `NotFoundError`) + `errorhandler` central que preserva o formato `{"erro": ...}` — Playbook T-10.

### #15 [MEDIUM] Código duplicado (AP-16)
File: models.py:12-21, 31-40, 304-313
File: models.py:177-201, 209-233
Description: O mesmo bloco de serialização de produto aparece 3 vezes; `get_pedidos_usuario` e `get_todos_pedidos` são cópias quase idênticas.
Impact: Correções precisam ser replicadas; divergências futuras.
Recommendation: Funções únicas de mapeamento (`_row_to_produto`) e uma consulta de pedidos parametrizada por filtro — Playbook T-07 / T-15.

### #16 [MEDIUM] Agregação ineficiente (AP-14)
File: models.py:239-254
File: controllers.py:268-274
Description: Relatório faz 5 queries separadas (`COUNT`, `SUM`, um `COUNT` por status); health faz 4 queries.
Impact: Round-trips desnecessários ao banco.
Recommendation: Uma única query com `COUNT`, `SUM` e `SUM(CASE WHEN ...)` — Playbook T-09.

### #17 [MEDIUM] print como logging e notificações simuladas no controller (AP-20)
File: controllers.py:8, 11, 57, 61, 106, 161, 179, 182, 208-210, 219, 248, 250
File: app.py:56, 83-86
Description: `print` usado para log de erros/eventos (inclui e-mail do usuário no login) e para "enviar" e-mail/SMS/push dentro do handler de pedidos.
Impact: Sem níveis/destino de log; side-effects acoplados ao controller.
Recommendation: `logging` configurado na factory; notificações em `services/notification_service.py` — Playbook T-16.

### #18 [LOW] Magic numbers / strings (AP-21)
File: models.py:256-262
File: controllers.py:47-52, 242, 285-286
File: app.py:88
Description: Faixas de desconto (10000/0.1, 5000/0.05, 1000/0.02), limites de nome (2/200), listas de categorias e status, versão "1.0.0" e ambiente "producao" literais, porta 5000.
Impact: Regras de negócio escondidas e repetidas.
Recommendation: Constantes nomeadas em módulo de domínio/config — Playbook T-15.

### #19 [LOW] Nomes pouco expressivos (AP-22)
File: controllers.py:14, 56, 64, 98, 136, 160
File: models.py:24, 54, 65, 89, 187, 191, 219, 223
Description: Parâmetro/variável `id` sombreando o builtin; `cursor2`, `cursor3`, `prod`, `row`.
Impact: Leitura mais difícil, risco de bugs por sombreamento.
Recommendation: `produto_id`, `usuario_id`, nomes descritivos — Playbook T-15.

### #20 [LOW] Imports não utilizados / código morto (AP-23)
File: models.py:2
File: database.py:2
File: controllers.py:268
Description: `import sqlite3` em models.py e `import os` em database.py não usados; `cursor.execute("SELECT 1")` sem leitura do resultado.
Impact: Ruído e falsa impressão de dependência.
Recommendation: Remover — Playbook T-15.

### #21 [LOW] Código não idiomático (AP-24)
File: models.py:146
File: controllers.py:200
Description: `total = total + (...)`; `if not itens or len(itens) == 0` (redundante).
Impact: Verbosidade.
Recommendation: `total += ...`; `if not itens` — Playbook T-15.

## Deprecated APIs
Nenhuma API deprecated detectada. Verificado: `datetime.utcnow`, `Query.get`, `before_first_request`, `JSONEncoder`, `pkg_resources`/`distutils` — nenhum uso. As APIs Flask utilizadas (`add_url_rule`, `jsonify`, `request.get_json`) são suportadas no Flask 3.1.

## Architecture Overview
Current: Monolítica com pseudo-camadas — `models.py` e `controllers.py` existem, mas models contém regras e formatação, controllers acessam banco e fazem validação/notificação, `app.py` contém config, rotas e SQL administrativo.
Target:  `src/config`, `src/database`, `src/models` (por entidade), `src/controllers` (por domínio), `src/views` (blueprints), `src/services`, `src/middlewares/error_handler.py`, `src/app.py` (factory) + `app.py` entry point.

## Proposed Contract Changes
- `POST /admin/query` removido (execução de SQL arbitrário).
- `POST /admin/reset-db` passa a exigir header `X-Admin-Token` igual a `ADMIN_TOKEN` (403 se ausente/incorreto ou não configurado).
- Campo `senha` removido das respostas de `/usuarios`.
- `GET /health` deixa de retornar `secret_key`, `db_path` e `debug`.
- Erros 500 passam a retornar mensagem genérica em vez de `str(e)`; entradas inválidas que antes geravam 500 passam a retornar 400.

```
================================
Total: 21 findings
================================
```

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
