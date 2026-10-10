# task-manager-api

API de Task Manager em Python/Flask usada como entrada do desafio `refactor-arch`. Já possuía alguma separação de camadas (`models/`, `routes/`, `services/`, `utils/`); a refatoração preservou esses pacotes e completou a arquitetura MVC com `controllers/`, `config/` e `middlewares/`.

## Como rodar

```bash
pip install -r requirements.txt
python seed.py
python app.py
```

A aplicação sobe em `http://localhost:5000` (configurável via `PORT`). O `seed.py` popula o banco SQLite (`tasks.db`) com usuários, categorias e tasks de exemplo — **rode-o antes do primeiro boot**, caso contrário os endpoints vão retornar listas vazias.

> Bancos criados pela versão anterior continuam funcionando: senhas com hash MD5 legado são migradas para o hash atual no primeiro login bem-sucedido.

## Configuração

Variáveis de ambiente (ou arquivo `.env`) — veja [.env.example](.env.example): `SECRET_KEY`, `DATABASE_URL`, `FLASK_DEBUG`, `HOST`, `PORT`, `CORS_ORIGINS`, `LOG_LEVEL` e `SMTP_*` (notificação de task atribuída; desabilitada se vazio).

## Estrutura

```
app.py                  # composition root (create_app) + entry point
config/settings.py      # configuração via ambiente
database.py             # instância do SQLAlchemy
models/                 # entidades ORM + consultas agregadas (stats.py)
controllers/            # regras de negócio: tasks, usuários, relatórios, categorias
routes/                 # blueprints finos (views)
services/               # notificação por e-mail, emissão de token
middlewares/            # error handler central
utils/                  # constantes, validadores, erros de domínio, helpers
seed.py                 # dados de exemplo
```
