# task-manager-api — 2ª execução da skill (após correção do T-06)

Execução da `refactor-arch` sobre o código **já refatorado** na 1ª execução ([audit-project-3.md](audit-project-3.md)), depois de reforçar o T-06 do playbook e a Fase 3. Objetivo: fechar o finding HIGH de autenticação, que a 1ª execução tinha reportado sem corrigir.

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python 3 (sem versão fixada; runtime local 3.11)
Framework:     Flask 3.0.0 + Flask-SQLAlchemy 3.1.1 (SQLAlchemy 2.x)
Dependencies:  flask-cors 4.0.0, python-dotenv 1.0.0; itsdangerous (transitiva do Flask) para tokens
Database:      SQLite (instance/tasks.db) via SQLAlchemy ORM; seed em seed.py
Domain:        Task Manager API (tasks, usuários, categorias, relatórios de produtividade)
Architecture:  Em camadas (MVC) — routes → controllers → models; config, services, middlewares e utils separados; composition root em app.py
Entry point:   app.py (python seed.py && python app.py, porta 5000)
Source files:  25 files analyzed (~1160 lines)
DB tables:     users, tasks, categories
Endpoints:     22 routes mapped
================================
```

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python + Flask 3.0.0 (Flask-SQLAlchemy 3.1.1)
Files:   25 analyzed | ~1160 lines of code
Date:    2026-10-17
```

## Summary
CRITICAL: 0 | HIGH: 3 | MEDIUM: 1 | LOW: 0

| # | Severity | Anti-pattern | Location |
|---|----------|--------------|----------|
| 1 | HIGH | Operações administrativas sem autenticação (AP-12) | routes/user_routes.py:15-26; controllers/user_controller.py:44-93 |
| 2 | HIGH | Token emitido mas nunca verificado (AP-12) | services/token_service.py:4-11 |
| 3 | HIGH | Senha fixa do admin no seed (AP-01, severidade ajustada) | seed.py:19-24 |
| 4 | MEDIUM | Validação ausente em `name`/`active` (AP-15) | controllers/user_controller.py:71-72, 81-82 |

## Findings

### #1 [HIGH] Operações administrativas sem autenticação (AP-12)
File: routes/user_routes.py:15-26
File: controllers/user_controller.py:47, 58-60, 67-85, 87-93
Description: `DELETE /users/<id>` apaga qualquer usuário e suas tasks; `PUT /users/<id>` altera `role`, `active`, e-mail e senha de **qualquer** usuário; `POST /users` aceita `role` do corpo e cria contas `admin`. Nenhuma das rotas exige credencial.
Impact: Qualquer cliente anônimo se promove a admin, desativa ou apaga contas e toma contas alheias trocando e-mail/senha.
Recommendation: Mínimo seguro de T-06 — `require_admin` (Bearer + perfil admin recarregado do banco) em `DELETE /users/<id>`; `require_auth` em `PUT /users/<id>` com regra no controller (dono ou admin; `role`/`active` só admin); `POST /users` com perfil diferente de `user` só por admin autenticado (cadastro com perfil padrão continua público). 401 sem credencial, 403 sem permissão — Playbook T-06.

### #2 [HIGH] Token emitido mas nunca verificado (AP-12)
File: services/token_service.py:4-11
Description: A 1ª execução trocou o token falso por um token assinado (`URLSafeTimedSerializer`), mas não existe `verify`/`loads` nem middleware que leia `Authorization` — grep por `verify|loads(|Authorization|require_` não encontra nenhum uso. O payload ainda carrega `role`, que não deve ser confiado.
Impact: O token é decorativo: não autentica nada, e o finding original (#5 de audit-project-3.md) continua aberto.
Recommendation: `TokenService.verify` com expiração (`TOKEN_MAX_AGE_SECONDS`), payload só com `user_id`, middleware `middlewares/auth.py` que recarrega o usuário e rejeita inativos — Playbook T-06.

### #3 [HIGH] Senha fixa do admin no seed (AP-01)
File: seed.py:19-24
Description: O seed cria `joao@email.com` com perfil `admin` e senha literal no código (`<redacted>`).
Impact: Depois que as rotas administrativas forem protegidas por perfil admin (#1), essa senha pública passa a ser a chave delas em qualquer ambiente populado pelo seed.
Severidade: catálogo indica CRITICAL para credenciais hardcoded; ajustada para HIGH porque afeta apenas bancos criados pelo `seed.py` (que apaga os dados existentes, uso de desenvolvimento).
Recommendation: Senha do admin vinda de `SEED_ADMIN_PASSWORD` ou gerada aleatoriamente — Playbook T-06 (credencial administrativa do seed) / T-01.

### #4 [MEDIUM] Validação ausente em `name` e `active` (AP-15)
File: controllers/user_controller.py:71-72, 81-82
Description: `PUT /users/<id>` grava `name` sem checar se é string não vazia e `active` sem checar se é booleano.
Impact: Usuário com nome vazio; valores não booleanos em `active` (ex.: `"false"`, truthy) mantêm a conta ativa ou geram erro 500.
Recommendation: Validar `name` (string não vazia) e `active` (bool) — Playbook T-14.

## Deprecated APIs
Nenhuma API deprecated detectada. Verificado: `Query.get`, `datetime.utcnow` (só aparece no docstring de `utils/time.py`), `before_first_request`, `JSONEncoder`, `pkg_resources`, `distutils`.

## Administrative Operations
| Endpoint | Operação | Proteção atual | Proteção após Fase 3 |
|----------|----------|----------------|----------------------|
| DELETE /users/<id> | Apaga conta e tasks | nenhuma | Bearer + perfil admin |
| PUT /users/<id> (`role`, `active`) | Altera privilégio/status | nenhuma | Bearer + perfil admin |
| PUT /users/<id> (`name`, `email`, `password`) | Altera dados de acesso | nenhuma | Bearer; dono da conta ou admin |
| POST /users com `role` ≠ `user` | Cria conta privilegiada | nenhuma | Bearer + perfil admin |
| POST /users com perfil padrão | Cadastro | pública | pública (sem mudança) |

Leituras (`GET /users`, `/tasks`, `/reports/*`) e CRUD de tasks/categorias não são operações administrativas pelo critério do catálogo: não alteram privilégios nem contas e não expõem dados financeiros. O relatório de produtividade só agrega dados que `GET /users` e `GET /tasks` já devolvem. Exigir autenticação nelas fica como recomendação, porque mudaria o contrato de todos os clientes.

## Architecture Overview
Current: Em camadas (MVC) após a 1ª execução; falta a camada de autenticação/autorização.
Target:  Acrescentar `middlewares/auth.py` (autenticação) e regras de autorização em `controllers/user_controller.py`; `TokenService.verify`; seed com senha de admin vinda do ambiente.

## Proposed Contract Changes
- `DELETE /users/<id>` exige `Authorization: Bearer <token>` de um admin (401 sem token/token inválido, 403 se não admin).
- `PUT /users/<id>` exige `Authorization: Bearer <token>`; só o próprio usuário ou um admin (403); alterar `role` ou `active` só admin (403).
- `POST /users` com `role` diferente de `user` exige Bearer de admin (401 sem token, 403 se não admin).
- Token do login passa a expirar (`TOKEN_MAX_AGE_SECONDS`, padrão 3600 s) e não carrega mais `role`.
- `seed.py` não usa mais senha fixa para o admin: `SEED_ADMIN_PASSWORD` ou senha aleatória.
- `PUT /users/<id>` com `name` vazio ou `active` não booleano → 400.

```
================================
Total: 4 findings
================================
```

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
