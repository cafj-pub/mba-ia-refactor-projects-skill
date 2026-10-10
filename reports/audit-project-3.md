```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python 3 (sem versão fixada; runtime local 3.11)
Framework:     Flask 3.0.0 + Flask-SQLAlchemy 3.1.1 (SQLAlchemy 2.x)
Dependencies:  flask-cors 4.0.0; marshmallow 3.20.1, requests 2.31.0 e python-dotenv 1.0.0 declarados mas não usados
Database:      SQLite (instance/tasks.db) via SQLAlchemy ORM; seed manual em seed.py
Domain:        Task Manager API (tasks, usuários, categorias, relatórios de produtividade)
Architecture:  Parcialmente em camadas — pacotes models/, routes/, services/, utils/ existem, mas as rotas concentram validação, queries ORM e estatísticas; services/ e utils/ praticamente não são usados; config hardcoded no entry point
Entry point:   app.py (python seed.py && python app.py, porta 5000)
Source files:  12 files analyzed (~1155 lines) + 3 __init__.py vazios
DB tables:     users, tasks, categories
Endpoints:     22 routes mapped
================================
```

| Método | Rota | Handler |
|---|---|---|
| GET | `/`, `/health` | app.py:26, 22 |
| GET, POST | `/tasks` | routes/task_routes.py:11, 85 |
| GET, PUT, DELETE | `/tasks/<id>` | routes/task_routes.py:65, 156, 225 |
| GET | `/tasks/search`, `/tasks/stats` | routes/task_routes.py:240, 273 |
| GET, POST | `/users` | routes/user_routes.py:10, 42 |
| GET, PUT, DELETE | `/users/<id>` | routes/user_routes.py:27, 92, 134 |
| GET | `/users/<id>/tasks` | routes/user_routes.py:153 |
| POST | `/login` | routes/user_routes.py:185 |
| GET | `/reports/summary`, `/reports/user/<id>` | routes/report_routes.py:12, 103 |
| GET, POST | `/categories` | routes/report_routes.py:157, 167 |
| PUT, DELETE | `/categories/<id>` | routes/report_routes.py:190, 211 |

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python + Flask 3.0.0 (Flask-SQLAlchemy 3.1.1)
Files:   12 analyzed | ~1155 lines of code
Date:    2026-10-09
```

## Summary
CRITICAL: 3 | HIGH: 5 | MEDIUM: 7 | LOW: 4

| # | Severity | Anti-pattern | Location |
|---|----------|--------------|----------|
| 1 | CRITICAL | Credenciais / segredos hardcoded (AP-01) | app.py:13; services/notification_service.py:7-10 |
| 2 | CRITICAL | Hash de senha inseguro — MD5 sem salt (AP-05) | models/user.py:27-32 |
| 3 | CRITICAL | Exposição do hash de senha nas respostas (AP-06) | models/user.py:16-25 |
| 4 | HIGH | Regra de negócio nas rotas / ausência de controllers (AP-07) | routes/*.py |
| 5 | HIGH | Autenticação falsa (AP-12) | routes/user_routes.py:207-211 |
| 6 | HIGH | Acoplamento forte / sem app factory (AP-09) | app.py:9-31; services/notification_service.py:5-10 |
| 7 | HIGH | Configuração de execução insegura (AP-11) | app.py:11-15, 34 |
| 8 | HIGH | Integridade referencial (AP-10) | routes/report_routes.py:211-223; routes/user_routes.py:140-146 |
| 9 | MEDIUM | APIs deprecated — `Query.get()` e `datetime.utcnow()` (AP-18) | 16 + 22 ocorrências |
| 10 | MEDIUM | Queries N+1 (AP-13) | routes/task_routes.py:41-57; routes/user_routes.py:22; routes/report_routes.py:55-68, 161-164 |
| 11 | MEDIUM | Agregação ineficiente (AP-14) | routes/report_routes.py:15-43; routes/task_routes.py:275-287 |
| 12 | MEDIUM | Código duplicado (AP-16) | routes/task_routes.py, user_routes.py, report_routes.py |
| 13 | MEDIUM | Validação duplicada, não usada ou sem checagem de tipo (AP-15) | routes/task_routes.py:92-114, 166-213, 261; utils/helpers.py:57-108 |
| 14 | MEDIUM | Error handling inadequado — `except:` genérico (AP-17) | 12 ocorrências |
| 15 | MEDIUM | print como logging (AP-20) | routes/task_routes.py, user_routes.py; utils/helpers.py; services/notification_service.py |
| 16 | LOW | Imports, dependências e código não utilizados (AP-23) | app.py:7; routes/*.py; utils/helpers.py; requirements.txt:4-6 |
| 17 | LOW | Magic numbers / strings (AP-21) | routes/task_routes.py, user_routes.py, report_routes.py |
| 18 | LOW | Código não idiomático (AP-24) | models/task.py:38-60; models/user.py:34-38; routes/task_routes.py:141, 210 |
| 19 | LOW | Nomes pouco expressivos (AP-22) | routes/report_routes.py:24-28; routes/*.py |

## Findings

### #1 [CRITICAL] Credenciais / segredos hardcoded (AP-01)
File: app.py:13
File: services/notification_service.py:7-10
Description: `SECRET_KEY` literal (`<redacted>`) no entry point; usuário e senha SMTP (`email_password = <redacted>`) fixos no construtor do serviço de notificação.
Impact: Chave de assinatura e credencial de e-mail expostas no repositório; impossível variar por ambiente.
Recommendation: `config/settings.py` lendo variáveis de ambiente (`.env` via python-dotenv, já declarado) e injetando no serviço — Playbook T-01.

### #2 [CRITICAL] Hash de senha inseguro — MD5 sem salt (AP-05)
File: models/user.py:27-32
Description: `set_password`/`check_password` usam `hashlib.md5(pwd).hexdigest()` sem salt e comparação não constante.
Impact: Hashes MD5 são quebrados por rainbow tables em segundos; senhas iguais geram hashes iguais.
Recommendation: `werkzeug.security.generate_password_hash`/`check_password_hash`, com upgrade transparente dos hashes MD5 existentes no próximo login — Playbook T-04.

### #3 [CRITICAL] Exposição do hash de senha nas respostas (AP-06)
File: models/user.py:16-25
File: routes/user_routes.py:33, 85, 129, 209
Description: `User.to_dict()` inclui `password`, devolvido em `GET /users/<id>`, `POST /users`, `PUT /users/<id>` e `POST /login`.
Impact: Qualquer cliente obtém o hash (MD5, ver #2) de qualquer usuário.
Recommendation: Remover `password` da serialização — Playbook T-05.

### #4 [HIGH] Regra de negócio nas rotas / ausência de controllers (AP-07)
File: routes/task_routes.py:11-63, 85-154, 156-223, 273-299
File: routes/user_routes.py:42-90, 92-132
File: routes/report_routes.py:12-101, 103-155
Description: Apesar da separação em pacotes, os handlers fazem validação de domínio, queries ORM, transações e cálculo de estatísticas; não existe camada de controller e `services/` não é usado por nenhuma rota.
Impact: Regras presas ao HTTP; nenhuma lógica é reutilizável ou testável sem o servidor; arquivos de rota com 200–300 linhas.
Recommendation: Criar `controllers/` (task, user, report, category) com as regras; rotas apenas extraem input e serializam — Playbook T-07.

### #5 [HIGH] Autenticação falsa (AP-12)
File: routes/user_routes.py:207-211
Description: O login devolve `'fake-jwt-token-' + str(user.id)` — token previsível e não verificável; nenhuma rota exige autenticação (inclusive deleção de usuários e alteração de `role`).
Impact: Qualquer cliente forja tokens e executa operações administrativas.
Recommendation: Emitir token assinado (`itsdangerous`, já dependência do Flask) mantendo a chave `token`; proteger rotas sensíveis como evolução — Playbook T-06.

### #6 [HIGH] Acoplamento forte / sem app factory (AP-09)
File: app.py:9-31
File: services/notification_service.py:5-10
Description: App criada no import do módulo, `db.create_all()` executado como efeito colateral do import (30-31); rotas importam `db` e models diretamente; o serviço instancia sua própria configuração SMTP; `seed.py` depende do módulo `app`.
Impact: Impossível criar a aplicação com outra configuração (ex.: banco de teste); dependências ocultas.
Recommendation: `create_app(settings)` como composition root, injetando dependências (serviço de notificação, emissor de token) nos controllers — Playbook T-08.

### #7 [HIGH] Configuração de execução insegura (AP-11)
File: app.py:11-15, 34
Description: `debug=True` e `host='0.0.0.0'` fixos; URI do banco hardcoded; `CORS(app)` liberado para qualquer origem.
Impact: Debugger do Werkzeug exposto na rede (execução remota de código).
Recommendation: `FLASK_DEBUG`, `HOST`, `PORT`, `DATABASE_URL`, `CORS_ORIGINS` via config, debug desligado por padrão — Playbook T-01.

### #8 [HIGH] Integridade referencial (AP-10)
File: routes/report_routes.py:211-223
File: routes/user_routes.py:140-146
Description: Deletar uma categoria deixa as tasks apontando para um `category_id` inexistente (SQLite sem FK enforcement); a deleção de usuário apaga as tasks uma a uma em loop.
Impact: Dados órfãos; relatórios e joins inconsistentes.
Recommendation: Na mesma transação, desassociar as tasks da categoria (`category_id = NULL`) e apagar as tasks do usuário com um único `DELETE` em lote — Playbook T-11.

### #9 [MEDIUM] APIs deprecated (AP-18)
File: routes/task_routes.py:42, 51, 67, 117, 122, 158, 188, 195, 227
File: routes/user_routes.py:29, 94, 136, 155
File: routes/report_routes.py:105, 192, 213
File: models/task.py:15, 16, 52; models/user.py:14; models/category.py:11
Description: `Model.query.get()` (Legacy Query API do SQLAlchemy 2.x — `LegacyAPIWarning` confirmado em execução) e `datetime.utcnow()` (deprecated desde Python 3.12) também em routes/task_routes.py:31, 72, 215, 285; routes/user_routes.py:172; routes/report_routes.py:35, 42, 45, 71, 133; utils/helpers.py:38; services/notification_service.py:35; seed.py:66-74.
Impact: Warnings hoje e quebra em versões futuras do SQLAlchemy/Python.
Recommendation: `db.session.get(Model, id)`; helper `utcnow()` com `datetime.now(timezone.utc)` (mantendo datetimes naive em UTC no banco) — Playbook T-12.

### #10 [MEDIUM] Queries N+1 (AP-13)
File: routes/task_routes.py:41-57
File: routes/user_routes.py:22
File: routes/report_routes.py:55-68, 161-164
Description: `GET /tasks` faz `User.query.get` e `Category.query.get` para cada task; `GET /users` acessa `u.tasks` (lazy load) por usuário; o relatório consulta tasks por usuário e `GET /categories` conta tasks por categoria em loop.
Impact: 1 + 2N queries por listagem.
Recommendation: `joinedload(Task.user, Task.category)` e contagens com `GROUP BY` — Playbook T-09.

### #11 [MEDIUM] Agregação ineficiente (AP-14)
File: routes/report_routes.py:15-43
File: routes/task_routes.py:275-287
Description: 12 queries `count()` quase idênticas (por status e por prioridade) e carregamento de **todas** as tasks em memória para contar as atrasadas.
Impact: Custo cresce com o volume de tasks; round-trips desnecessários.
Recommendation: `GROUP BY status` / `GROUP BY priority` e filtro de atrasadas no banco — Playbook T-09.

### #12 [MEDIUM] Código duplicado (AP-16)
File: routes/task_routes.py:17-39, 71-80, 284-287
File: routes/user_routes.py:162-180
File: routes/report_routes.py:33-37, 132-135
Description: A regra "task atrasada" é reimplementada 6 vezes, embora `Task.is_overdue()` exista (models/task.py:50-60) sem uso; serialização manual de task duplica `Task.to_dict()`.
Impact: Mudança de regra exige editar 6 lugares; divergências já possíveis.
Recommendation: Usar `task.is_overdue()` e `to_dict()` como fonte única — Playbook T-07 / T-15.

### #13 [MEDIUM] Validação duplicada, não usada ou sem checagem de tipo (AP-15)
File: routes/task_routes.py:92-114, 166-213, 261
File: routes/user_routes.py:61, 106
File: routes/report_routes.py:196-197
File: utils/helpers.py:19-23, 57-108
Description: Regras de task copiadas entre create e update; `utils.process_task_data` e `validate_email` existem mas não são usados (regex de e-mail repetida nas rotas); `priority` string causa `TypeError` (500) e `int(priority)` na busca causa `ValueError` (500); `update_category` não valida corpo ausente.
Impact: Entradas inválidas geram 500; regras divergem entre endpoints.
Recommendation: Validadores únicos em `utils/validators.py`, usados pelos controllers, com checagem de tipo — Playbook T-14.

### #14 [MEDIUM] Error handling inadequado — `except:` genérico (AP-17)
File: routes/task_routes.py:62, 137, 204, 236
File: routes/user_routes.py:130, 149
File: routes/report_routes.py:186, 207, 221
File: utils/helpers.py:46, 49, 88
Description: `except:` sem tipo (captura até `KeyboardInterrupt`/`SystemExit`), sem log; nenhum error handler global.
Impact: Erros reais escondidos; diagnóstico impossível.
Recommendation: Exceções de domínio + `errorhandler` central (formato `{"error": ...}`) — Playbook T-10.

### #15 [MEDIUM] print como logging (AP-20)
File: routes/task_routes.py:149, 153, 219, 234
File: routes/user_routes.py:83, 89, 147
File: utils/helpers.py:39, 41
File: services/notification_service.py:21, 24
Description: `print` para eventos e erros, inclusive mensagens de exceção.
Impact: Sem níveis, sem destino configurável.
Recommendation: `logging` configurado na factory — Playbook T-16.

### #16 [LOW] Imports, dependências e código não utilizados (AP-23)
File: app.py:7
File: routes/task_routes.py:7; routes/user_routes.py:5-6; routes/report_routes.py:7-8
File: utils/helpers.py:3-7, 9-55, 110-116
File: models/task.py:3, 38-48
File: services/notification_service.py:1-48
File: requirements.txt:4-6
Description: `os, sys, json, time, hashlib` importados sem uso; helpers e constantes nunca chamados; `NotificationService` nunca instanciado; `Task.validate_status/validate_priority` sem uso; `marshmallow` e `requests` declarados sem uso.
Impact: Ruído, superfície de dependências maior.
Recommendation: Remover o que não é usado; ligar o serviço de notificação ao fluxo de atribuição de task — Playbook T-15.

### #17 [LOW] Magic numbers / strings (AP-21)
File: routes/task_routes.py:96-114, 167-184
File: routes/user_routes.py:64, 71, 115, 120
File: routes/report_routes.py:45, 129, 180
Description: Listas de status e roles repetidas, limites de título (3/200), prioridade (1–5, `<= 2` = alta), senha mínima (4), janela de 7 dias, cor padrão `#000000` — enquanto `utils/helpers.py:110-116` define constantes equivalentes que ninguém usa.
Impact: Regras espalhadas e inconsistentes.
Recommendation: Constantes de domínio em um único módulo — Playbook T-15.

### #18 [LOW] Código não idiomático (AP-24)
File: models/task.py:38-60
File: models/user.py:34-38
File: routes/task_routes.py:141, 210; utils/helpers.py:103
Description: `if cond: return True else: return False`, ifs aninhados em escada, `type(tags) == list`, contadores `x = x + 1`.
Impact: Verbosidade e leitura difícil.
Recommendation: Expressões booleanas diretas e `isinstance` — Playbook T-15.

### #19 [LOW] Nomes pouco expressivos (AP-22)
File: routes/report_routes.py:24-28
File: routes/task_routes.py:51, 122; routes/user_routes.py:13
Description: `p1`…`p5`, `t`, `u`, `c`, `cat`.
Impact: Leitura mais difícil.
Recommendation: Nomes descritivos — Playbook T-15.

## Deprecated APIs
| Location | Deprecated usage | Modern replacement |
|----------|------------------|--------------------|
| routes/task_routes.py:42, 51, 67, 117, 122, 158, 188, 195, 227; routes/user_routes.py:29, 94, 136, 155; routes/report_routes.py:105, 192, 213 | `Model.query.get(id)` (SQLAlchemy Legacy Query API) | `db.session.get(Model, id)` |
| models/task.py:15, 16, 52; models/user.py:14; models/category.py:11; routes/*.py; utils/helpers.py:38; services/notification_service.py:35; seed.py:66-74 | `datetime.utcnow()` (deprecated no Python 3.12) | `datetime.now(timezone.utc)` |

## Architecture Overview
Current: Parcialmente em camadas — models (ORM) corretos em essência, mas rotas fazem papel de controller + repositório; services/ e utils/ ociosos; config e bootstrap no import de `app.py`.
Target:  Manter `models/`, `routes/` (views finas), `services/`, `utils/`; criar `controllers/`, `config/settings.py`, `middlewares/error_handler.py`; `create_app()` em `app.py`; categorias em `routes/category_routes.py`.

## Proposed Contract Changes
- Campo `password` removido das respostas de usuário (`/users`, `/users/<id>`, `/login`).
- `token` do login passa a ser assinado (mesma chave, valor diferente).
- Entradas inválidas que geravam 500 (prioridade não numérica, corpo ausente em `PUT /categories/<id>`) passam a retornar 400; erros 500 retornam mensagem genérica.
- Deletar categoria desassocia as tasks (`category_id = null`).

```
================================
Total: 19 findings
================================
```

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
