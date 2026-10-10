# Análise de Projeto — Heurísticas (Fase 1)

Objetivo: descobrir **o que** é o projeto (stack, domínio) e **como** ele está organizado (arquitetura), sem modificar nada.

## 1. Inventário de arquivos

Liste apenas código-fonte da aplicação. Exclua sempre:

```
.git/  .claude/  node_modules/  .venv/  venv/  env/  __pycache__/  dist/  build/  target/
vendor/  coverage/  .pytest_cache/  *.lock  package-lock.json  yarn.lock  poetry.lock  *.db  *.sqlite
```

Comandos úteis (adapte à extensão detectada):

```bash
find . -type f \( -name '*.py' -o -name '*.js' -o -name '*.ts' -o -name '*.java' -o -name '*.go' -o -name '*.rb' -o -name '*.php' -o -name '*.cs' \) \
  -not -path '*/node_modules/*' -not -path '*/.venv/*' -not -path '*/venv/*' -not -path '*/.claude/*' -not -path '*/.git/*'
wc -l <arquivos>        # total de linhas
```

"Source files" = número de arquivos de código da aplicação (inclui scripts como `seed.py`; não inclui `__init__.py` vazios — mencione-os à parte se existirem).

## 2. Detecção de linguagem

| Sinal (arquivo de manifesto / extensão predominante) | Linguagem |
|---|---|
| `requirements.txt`, `pyproject.toml`, `setup.py`, `Pipfile`, `*.py` | Python |
| `package.json` + `*.js` / `*.mjs` / `*.cjs` | JavaScript (Node.js) |
| `package.json` + `tsconfig.json` / `*.ts` | TypeScript (Node.js) |
| `pom.xml`, `build.gradle`, `*.java` / `*.kt` | Java / Kotlin |
| `go.mod`, `*.go` | Go |
| `Gemfile`, `*.rb` | Ruby |
| `composer.json`, `*.php` | PHP |
| `*.csproj`, `*.cs` | C# |

Versão: `python_requires`/`.python-version`/`runtime.txt`; `engines.node` em `package.json`/`.nvmrc`. Se não houver, informe a versão do runtime local apenas como referência (`python3 --version`, `node --version`).

## 3. Detecção de framework

Leia o manifesto e confirme pelos imports no código:

| Dependência | Import / sinal no código | Framework |
|---|---|---|
| `flask` | `from flask import Flask`, `@app.route`, `Blueprint`, `add_url_rule` | Flask |
| `django` | `settings.py`, `urls.py`, `INSTALLED_APPS` | Django |
| `fastapi` | `FastAPI()`, `@app.get`, `APIRouter` | FastAPI |
| `express` | `require('express')` / `import express`, `app.get(...)`, `express.Router()` | Express |
| `@nestjs/core` | decorators `@Controller`, `@Module` | NestJS |
| `koa`, `fastify`, `hapi` | `new Koa()`, `fastify()` | Koa / Fastify / Hapi |
| `spring-boot-starter-web` | `@RestController` | Spring Boot |
| `gin-gonic/gin`, `labstack/echo` | `gin.Default()` | Gin / Echo |
| `rails` / `laravel/framework` | `routes.rb` / `routes/web.php` | Rails / Laravel |

Reporte a versão **declarada** no manifesto (ex.: `flask==3.1.1`, `"express": "^4.18.2"`).
Liste também dependências relevantes (CORS, ORM, validação, HTTP client, dotenv) e sinalize dependências declaradas mas não usadas.

## 4. Banco de dados e acesso a dados

| Sinal | Conclusão |
|---|---|
| `sqlite3.connect`, `require('sqlite3')`, `':memory:'`, `*.db` | SQLite (driver cru) |
| `flask_sqlalchemy`, `SQLAlchemy`, `db.Model` | SQLAlchemy ORM |
| `psycopg2`, `pg`, `mysql`, `mysql2`, `pymongo`, `mongoose` | Postgres / MySQL / MongoDB |
| `sequelize`, `typeorm`, `prisma`, `knex` | ORM/Query builder Node |
| `CREATE TABLE` em strings, `__tablename__`, `models.Model` | Tabelas/entidades |

Extraia as tabelas a partir de `CREATE TABLE`, `__tablename__`, schemas/migrations. Anote se o banco é em arquivo, em memória ou servidor externo, e onde o schema/seed é criado.

## 5. Entry point e execução

- Python: arquivo com `if __name__ == '__main__':` / `app.run(...)`; `FLASK_APP`; `wsgi.py`; `manage.py`.
- Node: `scripts.start` / `main` no `package.json`; arquivo com `app.listen(...)`.
- Registre **comando**, **host** e **porta** (literal ou via env) — necessários para a validação. Verifique se há passo prévio obrigatório (ex.: `seed.py`, migrations).

## 6. Inventário de endpoints

Padrões de busca:

```bash
# Flask
grep -rnE "@[a-zA-Z_]+\.route\(|add_url_rule\(|Blueprint\(" --include=*.py .
# FastAPI
grep -rnE "@(app|router)\.(get|post|put|patch|delete)\(" --include=*.py .
# Express / Koa
grep -rnE "\.(get|post|put|patch|delete|all|use)\(\s*['\"\`]/" --include=*.js --include=*.ts . | grep -v node_modules
```

Para cada rota registre: método, path (incluindo prefixo de Blueprint/Router), handler, `arquivo:linha`. Consulte também arquivos de exemplo de requisição (`*.http`, coleções Postman, README) — eles mostram os payloads esperados e devem entrar no smoke test.

## 7. Inferência do domínio

Combine nomes de tabelas/modelos, rotas e strings de negócio:
- `produtos`, `pedidos`, `carrinho`, `checkout`, `payments` → E-commerce
- `courses`, `enrollments`, `students` → LMS / plataforma de cursos (pode ter checkout)
- `tasks`, `categories`, `due_date`, `priority` → Task Manager
Descreva em uma linha: tipo de sistema + entidades principais (ex.: "E-commerce API (produtos, pedidos, usuários)").

## 8. Classificação da arquitetura atual

| Classificação | Sinais |
|---|---|
| **Monolítica sem camadas** | Poucos arquivos; um mesmo arquivo mistura rotas, SQL, regras de negócio e config; classes "Manager"/"App" que fazem tudo |
| **Pseudo-camadas** | Arquivos chamados `models.py`/`controllers.py` existem, mas *models* contém regra de negócio/formatação e *controllers* acessam o banco diretamente ou validam tudo à mão |
| **Parcialmente em camadas** | Pastas `models/`, `routes/`, `services/`, `utils/`, porém rotas contêm regra de negócio e consultas ao ORM, services pouco usados, config hardcoded no entry point |
| **Em camadas (MVC/Layered)** | Rotas finas → controllers → models; config externa; error handling central; composição em um ponto único |

Na linha "Architecture" do resumo, informe a classificação + uma justificativa curta com evidência (ex.: "Monolítica — 4 arquivos; `models.py` mistura SQL, regras e formatação; segredos em `app.py`").

Mapeie também, por arquivo, quais responsabilidades ele carrega (rotas, regra de negócio, acesso a dados, config, apresentação/serialização, infraestrutura). Esse mapa guia a Fase 3.
