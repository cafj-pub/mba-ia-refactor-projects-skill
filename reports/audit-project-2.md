```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      JavaScript (Node.js; sem engines fixado — runtime local v20)
Framework:     Express ^4.18.2
Dependencies:  sqlite3 ^5.1.6
Database:      SQLite em memória (':memory:') via driver sqlite3 com API de callbacks
Domain:        LMS / plataforma de cursos com checkout (usuários, cursos, matrículas, pagamentos, auditoria) + relatório financeiro
Architecture:  Monolítica — God Class AppManager.js concentra conexão, schema, seeds, rotas e regras; utils.js mistura config com segredos, cache global e "criptografia"
Entry point:   src/app.js (npm start, porta 3000)
Source files:  3 files analyzed (~180 lines)
DB tables:     users, courses, enrollments, payments, audit_logs
Endpoints:     3 routes mapped
================================
```

| Método | Rota | Handler |
|---|---|---|
| POST | `/api/checkout` | src/AppManager.js:28 |
| GET | `/api/admin/financial-report` | src/AppManager.js:80 |
| DELETE | `/api/users/:id` | src/AppManager.js:131 |

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   JavaScript (Node.js) + Express 4.18
Files:   3 analyzed | ~180 lines of code
Date:    2026-10-09
```

## Summary
CRITICAL: 4 | HIGH: 5 | MEDIUM: 5 | LOW: 3

| # | Severity | Anti-pattern | Location |
|---|----------|--------------|----------|
| 1 | CRITICAL | Credenciais / segredos hardcoded (AP-01) | src/utils.js:1-7 |
| 2 | CRITICAL | Armazenamento inseguro de senhas (AP-05) | src/utils.js:17-23; src/AppManager.js:18, 68 |
| 3 | CRITICAL | Dados sensíveis em log — cartão e chave do gateway (AP-06) | src/AppManager.js:45 |
| 4 | CRITICAL | God Class (AP-03) | src/AppManager.js:4-139 |
| 5 | HIGH | Regra de negócio no handler de rota (AP-07) | src/AppManager.js:28-78, 80-129 |
| 6 | HIGH | Escrita multi-etapa sem transação / registros órfãos (AP-10) | src/AppManager.js:50-63, 131-137 |
| 7 | HIGH | Endpoints administrativos sem autenticação (AP-12) | src/AppManager.js:80, 131 |
| 8 | HIGH | Estado global mutável (AP-08) | src/utils.js:9-15 |
| 9 | HIGH | Acoplamento forte / sem injeção de dependência (AP-09) | src/AppManager.js:5-8; src/app.js:8-10 |
| 10 | MEDIUM | Queries N+1 (AP-13) | src/AppManager.js:83-128 |
| 11 | MEDIUM | Callback hell / pyramid of doom (AP-19) | src/AppManager.js:37-77, 83-128 |
| 12 | MEDIUM | Error handling inadequado — erros ignorados (AP-17) | src/AppManager.js:57, 92, 104, 106, 133 |
| 13 | MEDIUM | Validação de entrada ausente (AP-15) | src/AppManager.js:29-35, 132 |
| 14 | MEDIUM | console.log como logging (AP-20) | src/AppManager.js:45; src/utils.js:13; src/app.js:13 |
| 15 | LOW | Nomes pouco expressivos (AP-22) | src/AppManager.js:29-33, 89, 102; src/utils.js:12, 17 |
| 16 | LOW | Magic numbers / strings (AP-21) | src/AppManager.js:21, 46, 108; src/utils.js:6, 19, 22 |
| 17 | LOW | Código morto / exports não usados (AP-23) | src/utils.js:2-5, 10, 25; src/AppManager.js:2 |

## Findings

### #1 [CRITICAL] Credenciais / segredos hardcoded (AP-01)
File: src/utils.js:1-7
Description: Objeto `config` literal com `dbUser`, `dbPass` (`<redacted>`), `paymentGatewayKey` com prefixo de chave de produção `pk_live_` (`<redacted>`) e `smtpUser`.
Impact: Segredos de produção expostos a qualquer pessoa com acesso ao repositório; impossível rotacionar sem alterar código.
Recommendation: `src/config/index.js` lendo `process.env` (sem defaults para segredos) + `.env.example` — Playbook T-01.

### #2 [CRITICAL] Armazenamento inseguro de senhas (AP-05)
File: src/utils.js:17-23
File: src/AppManager.js:18, 68
Description: `badCrypto` "criptografa" com base64 repetido e truncado em 10 caracteres (sem salt, reversível/colidente); senha padrão `"123456"` quando o cliente não envia `pwd`; seed grava senha em texto puro.
Impact: Senhas triviais de recuperar após vazamento; contas criadas com senha conhecida.
Recommendation: `crypto.scrypt` com salt aleatório e comparação `timingSafeEqual`; sem senha padrão (gerar senha aleatória) — Playbook T-04.

### #3 [CRITICAL] Dados sensíveis em log (AP-06)
File: src/AppManager.js:45
Description: `console.log` imprime o número completo do cartão e a chave do gateway de pagamento a cada checkout.
Impact: Violação de PCI-DSS; logs passam a conter dados de cartão e segredos.
Recommendation: Logar só os 4 últimos dígitos e nunca a chave — Playbook T-05.

### #4 [CRITICAL] God Class (AP-03)
File: src/AppManager.js:4-139
Description: `AppManager` cria a conexão (5-8), define schema e seeds (10-23), registra rotas (25-138) e implementa checkout, pagamento, auditoria, relatório e deleção nos próprios handlers.
Impact: Nenhuma parte pode ser testada ou reutilizada isoladamente; qualquer mudança arrisca todo o sistema.
Recommendation: Separar em `config/`, `database/`, `models/`, `controllers/`, `services/`, `routes/`, `middlewares/` com composição em `app.js` — Playbook T-03.

### #5 [HIGH] Regra de negócio no handler de rota (AP-07)
File: src/AppManager.js:28-78, 80-129
Description: O handler de checkout decide aprovação de pagamento (`cc.startsWith("4")`, linha 46), cria usuário, matrícula, pagamento e auditoria; o handler do relatório calcula receita por curso.
Impact: Regras presas ao HTTP; impossível testar o fluxo de checkout sem subir o servidor.
Recommendation: `checkoutController`/`reportController` sem `req`/`res`; gateway de pagamento como service — Playbook T-07.

### #6 [HIGH] Escrita multi-etapa sem transação / registros órfãos (AP-10)
File: src/AppManager.js:50-63
File: src/AppManager.js:131-137
File: src/AppManager.js:12-16
Description: Matrícula, pagamento e log de auditoria são inseridos em callbacks separados sem transação; a deleção de usuário remove só o registro em `users` e a própria resposta admite que "matrículas e pagamentos ficaram sujos"; tabelas sem `FOREIGN KEY`.
Impact: Falha no meio do checkout gera matrícula sem pagamento; deleções deixam dados órfãos (relatório mostra alunos "Unknown").
Recommendation: Transação única (`BEGIN/COMMIT/ROLLBACK`) no checkout e deleção em cascata dentro de transação — Playbook T-11.

### #7 [HIGH] Endpoints administrativos sem autenticação (AP-12)
File: src/AppManager.js:80, 131
Description: `GET /api/admin/financial-report` (nomes de alunos e valores pagos) e `DELETE /api/users/:id` são públicos.
Impact: Qualquer cliente lê dados financeiros ou apaga usuários.
Recommendation: Middleware exigindo `X-Admin-Token` configurado via env (desabilitado se não configurado) — Playbook T-06.

### #8 [HIGH] Estado global mutável (AP-08)
File: src/utils.js:9-15
Description: `globalCache` (objeto de módulo que só cresce e nunca é lido) e `totalRevenue` exportado como variável de módulo.
Impact: Vazamento de memória a cada checkout; estado compartilhado entre requisições e testes.
Recommendation: Remover o cache sem uso; dados persistidos via audit log — Playbook T-08.

### #9 [HIGH] Acoplamento forte / sem injeção de dependência (AP-09)
File: src/AppManager.js:5-8
File: src/app.js:8-10
Description: A classe instancia `new sqlite3.Database(':memory:')` internamente; `app.js` depende de uma classe que é ao mesmo tempo banco, roteador e regra.
Impact: Impossível substituir banco ou gateway em testes.
Recommendation: Composition root `createApp(config)` que cria a conexão e injeta models/services nos controllers — Playbook T-08.

### #10 [MEDIUM] Queries N+1 (AP-13)
File: src/AppManager.js:83-128
Description: Para cada curso, uma query de matrículas; para cada matrícula, uma query de usuário e outra de pagamento (1 + C + 2·M queries).
Impact: Relatório degrada linearmente com o número de matrículas.
Recommendation: Uma query com `LEFT JOIN` courses → enrollments → users → payments e agregação em memória — Playbook T-09.

### #11 [MEDIUM] Callback hell / pyramid of doom (AP-19)
File: src/AppManager.js:37-77
File: src/AppManager.js:83-128
Description: Até 7 níveis de funções aninhadas aninhados no checkout; relatório com contadores manuais (`coursesPending--`, `enrPending--`) e `const self = this` (linha 26). A ordem dos cursos no relatório varia entre chamadas (corrida entre callbacks).
Impact: Fluxo difícil de ler e de tratar erros; resposta não determinística.
Recommendation: Promisificar o driver e usar `async/await` — Playbook T-13.

### #12 [MEDIUM] Error handling inadequado — erros ignorados (AP-17)
File: src/AppManager.js:57, 92, 104, 106, 133
Description: Parâmetro `err` ignorado em vários callbacks (linha 92: se a query falhar, `enrollments.length` lança TypeError e derruba o processo; linha 133: responde "deletado" mesmo em erro ou se o usuário não existe); sem error handler central do Express.
Impact: Crash do servidor em falha de banco; respostas de sucesso falsas.
Recommendation: `asyncHandler` + middleware `errorHandler` central com erros de domínio — Playbook T-10.

### #13 [MEDIUM] Validação de entrada ausente (AP-15)
File: src/AppManager.js:29-35, 132
Description: Só verifica presença de `usr`, `eml`, `c_id`, `card`; não valida tipos/formatos (e-mail, cartão numérico, `c_id` inteiro); `:id` da deleção não é validado.
Impact: Dados inválidos persistidos; erros internos em vez de 400.
Recommendation: Validação centralizada no controller, mantendo a resposta `400 Bad Request` — Playbook T-14.

### #14 [MEDIUM] console.log como logging (AP-20)
File: src/AppManager.js:45
File: src/utils.js:13
File: src/app.js:13
Description: `console.log` espalhado para eventos e cache; sem níveis nem formato.
Impact: Logs não controláveis por ambiente; combinado ao #3, vaza dados sensíveis.
Recommendation: Logger único (`src/utils/logger.js`) com nível configurável — Playbook T-16.

### #15 [LOW] Nomes pouco expressivos (AP-22)
File: src/AppManager.js:29-33, 89, 102
File: src/utils.js:12, 17
Description: Variáveis `u`, `e`, `p`, `cid`, `cc`, `c`, `enr`; nomes enganosos `badCrypto`, `logAndCache` (faz duas coisas), `AppManager` (faz tudo). As chaves do payload (`usr`, `eml`, `pwd`, `c_id`) fazem parte do contrato e serão mantidas.
Impact: Leitura difícil.
Recommendation: Desestruturar o payload para nomes claros (`name`, `email`, `password`, `courseId`, `card`) — Playbook T-15.

### #16 [LOW] Magic numbers / strings (AP-21)
File: src/AppManager.js:21, 46, 108
File: src/utils.js:6, 19, 22
Description: Regra de aprovação `"4"`, status `'PAID'`/`'DENIED'` repetidos, `10000` iterações e corte em `10` caracteres, porta `3000`.
Impact: Regras escondidas e duplicadas.
Recommendation: Constantes nomeadas (`PAYMENT_STATUS`, `APPROVED_CARD_PREFIX`) e porta via config — Playbook T-15.

### #17 [LOW] Código morto / exports não usados (AP-23)
File: src/utils.js:2-5, 10, 25
File: src/AppManager.js:2
Description: `dbUser`, `dbPass`, `smtpUser` nunca usados; `totalRevenue` e `globalCache` exportados e importados sem uso.
Impact: Ruído e falsa dependência.
Recommendation: Remover — Playbook T-15.

## Deprecated APIs
Nenhuma API deprecated detectada. Verificado: `new Buffer()` (o código usa `Buffer.from`), `url.parse`, `fs.exists`, `crypto.createCipher`, `body-parser` (usa `express.json()`), `req.param()`, `res.send(status)`, `app.del()`. A API de callbacks do `sqlite3` não é deprecated, mas será encapsulada em Promises (finding #11).

## Architecture Overview
Current: Monolítica — `AppManager` é God Class (banco + rotas + regras); `utils.js` mistura config com segredos, estado global e hashing.
Target:  `src/config`, `src/database` (conexão promisificada + schema/seed), `src/models`, `src/controllers`, `src/services` (pagamento, senhas), `src/routes`, `src/middlewares` (erros, admin), `src/app.js` (composition root) + `src/server.js` (entry point).

## Proposed Contract Changes
- `GET /api/admin/financial-report` e `DELETE /api/users/:id` passam a exigir header `X-Admin-Token` igual a `ADMIN_TOKEN` (403 sem token válido).
- `DELETE /api/users/:id` remove também matrículas e pagamentos do usuário; responde `404 Usuário não encontrado` para id inexistente e a mensagem de sucesso passa a ser `Usuário deletado`.
- Ordem dos cursos no relatório financeiro passa a ser determinística (por id do curso).
- Checkout sem `pwd` para usuário novo passa a gerar senha aleatória em vez de `"123456"`.

```
================================
Total: 17 findings
================================
```

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
