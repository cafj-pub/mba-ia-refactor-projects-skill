# code-smells-project

API de E-commerce em Python/Flask usada como entrada do desafio `refactor-arch` — refatorada para o padrão MVC.

## Como rodar

```bash
pip install -r requirements.txt
python app.py
```

A aplicação sobe em `http://localhost:5000` (configurável via `PORT`). O banco SQLite (`loja.db`) é criado automaticamente no primeiro boot, já com produtos e usuários de exemplo (senhas gravadas com hash).

> Se você tem um `loja.db` gerado pela versão antiga (senhas em texto puro), apague-o antes do primeiro boot.

## Configuração

Todas as configurações vêm de variáveis de ambiente — veja [.env.example](.env.example). As principais:

| Variável | Default | Descrição |
|---|---|---|
| `SECRET_KEY` | aleatória por processo | Chave da aplicação (defina em produção) |
| `FLASK_DEBUG` | `false` | Modo debug |
| `HOST` / `PORT` | `127.0.0.1` / `5000` | Endereço do servidor |
| `DATABASE_PATH` | `loja.db` | Arquivo SQLite |
| `CORS_ORIGINS` | `*` | Origens permitidas |
| `ADMIN_TOKEN` | vazio (desabilitado) | Token do header `X-Admin-Token` para `POST /admin/reset-db` |
| `SEED_ADMIN_PASSWORD` | aleatória | Senha do `admin@loja.com` criado no seed |

## Estrutura

```
app.py                      # entry point
src/
├── app.py                  # composition root (create_app)
├── config/                 # settings (env) e constantes de domínio
├── database/               # conexão por request, schema e seed
├── models/                 # acesso a dados (SQL parametrizado)
├── controllers/            # regras de negócio e fluxo
├── views/                  # blueprints (rotas HTTP)
├── services/               # notificações
├── middlewares/            # error handler central
└── utils/                  # erros de domínio e validadores
```
