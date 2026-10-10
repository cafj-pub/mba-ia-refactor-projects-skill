# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express usada como entrada do desafio `refactor-arch` — refatorada para o padrão MVC.

## Como rodar

```bash
npm install
ADMIN_TOKEN=um-token-local npm start
```

A aplicação sobe em `http://localhost:3000` (configurável via `PORT`). O banco SQLite é em memória por padrão e já carrega seeds automaticamente no boot.

Exemplos de requisições estão em `api.http` (as rotas administrativas exigem o header `X-Admin-Token`).

## Configuração

Veja [.env.example](.env.example):

| Variável | Default | Descrição |
|---|---|---|
| `PORT` | `3000` | Porta HTTP |
| `DATABASE_FILE` | `:memory:` | Banco SQLite |
| `PAYMENT_GATEWAY_KEY` | vazio | Chave do gateway (simulado se vazio) |
| `ADMIN_TOKEN` | vazio (rotas admin bloqueadas) | Token do header `X-Admin-Token` |
| `LOG_LEVEL` | `info` | `error`, `warn`, `info`, `debug` |

## Estrutura

```
src/
├── server.js              # entry point (listen)
├── app.js                 # composition root (createApp)
├── config/                # variáveis de ambiente
├── database/              # conexão promisificada + transações, schema e seed
├── models/                # acesso a dados por entidade
├── controllers/           # checkout, relatório financeiro, usuários
├── services/              # gateway de pagamento, hash de senhas
├── routes/                # rotas HTTP (views)
├── middlewares/           # error handler, asyncHandler, token admin
└── utils/                 # erros de domínio, logger
```
