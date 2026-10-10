# Catálogo de Anti-Patterns (Fase 2)

Cada anti-pattern tem: **ID**, **severidade padrão**, **sinais de detecção** (o que procurar, com padrões de grep por stack), **por que importa** e a **transformação** do playbook (`T-xx`, ver `refactoring-playbook.md`).

> Os padrões de grep são pontos de partida. **Sempre confirme lendo o trecho** e registre as linhas exatas.

## Escala de severidade

| Severidade | Critério |
|---|---|
| **CRITICAL** | Falha grave de arquitetura ou segurança: impede funcionamento correto, expõe dados sensíveis (credenciais hardcoded, SQL Injection, senhas em texto puro) ou viola completamente a separação de responsabilidades (God Class com banco + regras + rotas). |
| **HIGH** | Forte violação de MVC/SOLID que dificulta muito manutenção e testes: regra de negócio pesada em controllers/rotas, acoplamento forte sem DI, estado global mutável, escrita sem transação. |
| **MEDIUM** | Padronização, duplicação, performance moderada: N+1, validação ausente/duplicada, error handling inadequado, APIs deprecated, middlewares mal usados. |
| **LOW** | Legibilidade: nomes ruins, magic numbers, imports não usados, código não idiomático. |

Regra de desempate: se o problema permite **acesso/alteração indevida de dados** ou **vazamento de segredo**, é CRITICAL, independentemente de onde esteja.

## Índice

| ID | Anti-pattern | Severidade | Transformação |
|---|---|---|---|
| AP-01 | Credenciais / segredos hardcoded | CRITICAL | T-01 |
| AP-02 | SQL / NoSQL Injection | CRITICAL | T-02 |
| AP-03 | God Class / God File | CRITICAL | T-03 |
| AP-04 | Endpoint perigoso (execução arbitrária / destrutivo sem proteção) | CRITICAL | T-06 |
| AP-05 | Armazenamento inseguro de senhas | CRITICAL | T-04 |
| AP-06 | Exposição de dados sensíveis em respostas ou logs | CRITICAL | T-05 |
| AP-07 | Regra de negócio na camada de rota/controller (Fat Controller) | HIGH | T-07 |
| AP-08 | Estado global mutável | HIGH | T-08 |
| AP-09 | Acoplamento forte / ausência de injeção de dependência | HIGH | T-08 |
| AP-10 | Escrita multi-etapa sem transação / integridade referencial | HIGH | T-11 |
| AP-11 | Configuração de execução insegura (debug, CORS aberto) | HIGH | T-01 |
| AP-12 | Autenticação falsa ou ausente | HIGH | T-06 |
| AP-13 | Queries N+1 | MEDIUM | T-09 |
| AP-14 | Agregação ineficiente | MEDIUM | T-09 |
| AP-15 | Validação de entrada ausente ou duplicada | MEDIUM | T-14 |
| AP-16 | Código duplicado | MEDIUM | T-07 / T-15 |
| AP-17 | Error handling inadequado / não centralizado | MEDIUM | T-10 |
| AP-18 | Uso de APIs deprecated | MEDIUM | T-12 |
| AP-19 | Callback hell / pyramid of doom | MEDIUM | T-13 |
| AP-20 | `print`/`console.log` como logging e side-effects simulados | MEDIUM | T-16 |
| AP-21 | Magic numbers / strings | LOW | T-15 |
| AP-22 | Nomes pouco expressivos | LOW | T-15 |
| AP-23 | Imports não utilizados / código morto | LOW | T-15 |
| AP-24 | Código não idiomático / condicionais verbosas | LOW | T-15 |

---

## CRITICAL

### AP-01 — Credenciais / segredos hardcoded
**Sinais:**
- Atribuições literais a chaves sensíveis: `SECRET_KEY`, `password`, `pass`, `pwd`, `token`, `api_key`, `apiKey`, `secret`, `gatewayKey`, `smtp`, `DATABASE_URL` com usuário/senha.
- Prefixos típicos de chaves reais: `pk_live_`, `sk_live_`, `AKIA`, `ghp_`, `xox`.
- Objetos de config literais (`const config = { dbPass: "..." }`), atributos de classe (`self.email_password = '...'`).
- Segredos devolvidos em respostas (ex.: health check retornando `secret_key`) → também AP-06.
```bash
grep -rniE "(secret|passw|pwd|pass|token|api_?key|gateway|smtp).{0,20}[:=]\s*['\"][^'\"]{3,}" --include=*.py --include=*.js --include=*.ts .
```
**Por que importa:** qualquer pessoa com acesso ao repositório obtém os segredos; impossível rotacionar sem deploy; ambientes compartilham a mesma chave.
**Relatório:** nunca copie o valor — escreva `<redacted>`.

### AP-02 — SQL / NoSQL Injection
**Sinais:**
- Concatenação ou interpolação de entrada em SQL: `"... WHERE id = " + str(id)`, `f"SELECT ... {var}"`, `` `SELECT ... ${var}` ``, `"... '%" + termo + "%'"`, `.format(` em strings SQL.
- `cursor.execute(query)` onde `query` foi montada com `+=`.
- Mongo: `$where` com string do usuário, objetos de filtro vindos diretamente do `req.body`.
```bash
grep -rnE "(execute|run|get|all|query)\(\s*(f?['\"\`]).*(SELECT|INSERT|UPDATE|DELETE).*(\+|\{|\\$\{)" --include=*.py --include=*.js .
grep -rnE "['\"](SELECT|INSERT|UPDATE|DELETE)[^'\"]*['\"]\s*\+" --include=*.py --include=*.js .
```
**Não é finding:** placeholders (`?`, `%s`, `:name`, `$1`) com parâmetros separados; ORM com filtros tipados.
**Por que importa:** leitura/alteração/destruição arbitrária do banco, bypass de login (`' OR '1'='1`).

### AP-03 — God Class / God File
**Sinais:**
- Um arquivo/classe com responsabilidades de **3 ou mais** camadas: definição de rotas + SQL/ORM + regra de negócio + config/infra (ex.: classe `AppManager` com `initDb`, `setupRoutes` e o fluxo de checkout).
- Arquivo de "models" que contém regra de negócio, formatação de resposta e queries para vários domínios diferentes (> ~200 linhas, > 3 entidades).
- Funções > ~50 linhas que fazem validação + persistência + notificação + resposta.
**Por que importa:** impossível testar em isolamento, alto acoplamento, qualquer mudança tem efeito colateral em todo o sistema.
**Linhas:** reporte o intervalo do arquivo/classe (ex.: `models.py:1-314`) e cite as responsabilidades misturadas.

### AP-04 — Endpoint perigoso
**Sinais:**
- Endpoint que executa SQL/código/comando recebido do cliente: `execute(request.json["sql"])`, `eval(`, `exec(`, `child_process.exec(req...)`, `os.system(`.
- Endpoint destrutivo em massa (reset/drop/truncate de banco) sem autenticação/autorização.
```bash
grep -rnE "(eval|exec)\(|os\.system|subprocess|child_process|DELETE FROM [a-z_]+\"?\)?$|DROP TABLE|TRUNCATE|/admin" --include=*.py --include=*.js .
```
**Por que importa:** é um backdoor — controle total do banco/servidor por qualquer cliente anônimo.

### AP-05 — Armazenamento inseguro de senhas
**Sinais:**
- Senha gravada como recebida (`INSERT ... senha` com o valor do request), comparação `WHERE senha = '...'`.
- Hash rápido/inseguro: `hashlib.md5`, `hashlib.sha1`, `sha256` sem salt, `crypto.createHash('md5')`.
- "Criptografia" caseira: base64, loops concatenando strings (ex.: `badCrypto`), XOR.
- Senha padrão quando ausente (`pwd || "123456"`).
**Correto:** `werkzeug.security.generate_password_hash` / `bcrypt` / `argon2` (Python); `crypto.scrypt` / `bcrypt` / `argon2` (Node).
**Por que importa:** vazamento do banco expõe todas as senhas (e reuso em outros sistemas).

### AP-06 — Exposição de dados sensíveis em respostas ou logs
**Sinais:**
- Serialização que inclui `senha`/`password`/hash (`to_dict()` com `'password': self.password`, `SELECT *` devolvido inteiro).
- Health/debug endpoints retornando config interna (`secret_key`, `db_path`, `debug`).
- Logs com dados de cartão, senha, token, chave de API (`console.log(\`Processando cartão ${cc} na chave ${key}\`)`).
- Mensagens de exceção internas devolvidas ao cliente (`return {"erro": str(e)}`) → também AP-17.
**Por que importa:** viola LGPD/PCI-DSS e entrega informação para atacantes.

---

## HIGH

### AP-07 — Regra de negócio na camada de rota/controller (Fat Controller)
**Sinais:**
- Handler de rota que contém: cálculos de domínio (totais, descontos, estatísticas), loops de agregação, validações extensas, chamadas diretas ao banco/ORM (`Model.query...`, `db.session...`, `cursor.execute`), orquestração de vários passos (cria usuário → cobra → matricula → audita).
- Handlers com > ~30 linhas ou várias responsabilidades.
- Regra de negócio dentro do *model* de acesso a dados (ex.: faixas de desconto dentro da função que faz SELECT).
**Por que importa:** regra fica presa ao HTTP, não é reutilizável nem testável sem subir servidor.

### AP-08 — Estado global mutável
**Sinais:**
- Variáveis de módulo reatribuídas/mutadas: `global db_connection`, `let globalCache = {}`, `let totalRevenue = 0`, listas em memória como "banco" (`self.notifications = []` em singleton).
- Conexão de banco única compartilhada entre threads (`check_same_thread=False` + variável global).
```bash
grep -rnE "^\s*global |^(let|var) [a-zA-Z_]+ = (\{|\[|0)|check_same_thread=False" --include=*.py --include=*.js .
```
**Por que importa:** condições de corrida, vazamento de memória, testes interdependentes, impossível escalar horizontalmente.

### AP-09 — Acoplamento forte / ausência de injeção de dependência
**Sinais:**
- Dependências instanciadas dentro de quem as usa (`new sqlite3.Database(...)` no construtor da classe de negócio, `NotificationService()` criado dentro da rota).
- Camadas superiores importando detalhes de infraestrutura (rota importando `db`/cursor diretamente; controller chamando `get_db()`).
- Ausência de composition root / app factory (`create_app`, `createApp`).
**Por que importa:** impossível substituir por mocks em testes; trocar banco/serviço exige alterar regra de negócio.

### AP-10 — Escrita multi-etapa sem transação / integridade referencial
**Sinais:**
- Vários `INSERT`/`UPDATE` relacionados (pedido + itens + estoque; matrícula + pagamento) sem `BEGIN/COMMIT/ROLLBACK` ou `session` única.
- Retorno antecipado no meio de uma sequência de escritas.
- `DELETE` de entidade pai deixando filhos órfãos (comentário ou mensagem admitindo "dados sujos"), ausência de `FOREIGN KEY`/`ON DELETE`.
**Por que importa:** falha parcial deixa o banco inconsistente (pagamento sem matrícula, estoque baixado sem pedido).

### AP-11 — Configuração de execução insegura
**Sinais:** `debug=True` / `DEBUG = True` fixo, `app.run(host='0.0.0.0', debug=True)`, `CORS(app)` / `cors()` sem restrição de origem em API com dados sensíveis, `NODE_ENV` ignorado.
**Por que importa:** o debugger do Werkzeug permite execução remota de código; stack traces vazam internals.

### AP-12 — Autenticação falsa ou ausente
**Sinais:** tokens previsíveis (`'fake-jwt-token-' + id`), login que não emite credencial verificável, rotas `admin`/relatórios financeiros/deleção sem qualquer verificação de identidade.
**Por que importa:** qualquer cliente se passa por qualquer usuário ou acessa operações administrativas.
**Nota:** se implementar autenticação completa estiver fora do escopo (quebraria o contrato), registre como recomendação e aplique o mínimo seguro (ex.: token assinado; proteger endpoints destrutivos).

---

## MEDIUM

### AP-13 — Queries N+1
**Sinais:**
- Query dentro de loop sobre o resultado de outra query: `for row in rows: cursor.execute(... row["id"])`, `for t in tasks: User.query.get(t.user_id)`, `courses.forEach(c => db.all(...))`.
- Acesso a relacionamento lazy dentro de loop (`len(u.tasks)`, `t.user.name`) sem eager loading.
**Correto:** `JOIN`, `IN (...)`, `joinedload`/`selectinload`, `GROUP BY`.

### AP-14 — Agregação ineficiente
**Sinais:** várias consultas `COUNT(*)` quase idênticas que só mudam o filtro (`filter_by(status='pending').count()`, `...='done'`), carregar todos os registros (`.all()`) para contar/filtrar em Python/JS.
**Correto:** uma consulta com `GROUP BY` / `SUM(CASE ...)`, ou filtro no banco.

### AP-15 — Validação de entrada ausente ou duplicada
**Sinais:**
- Campos usados sem checagem de tipo/intervalo (`int(request.args['priority'])` sem tratamento → 500; `preco < 0` com `preco` string → TypeError; `dados.get` com `dados = None`).
- Mesmas regras de validação copiadas em create/update ou em várias rotas; listas de valores válidos repetidas.
- Função de validação existente (`utils.process_task_data`, `validate_email`) que não é usada pelas rotas.

### AP-16 — Código duplicado
**Sinais:** blocos de serialização dict copiados (o mesmo `{"id": row["id"], ...}` em várias funções), regra repetida (cálculo de "atrasado" em 4 lugares), `to_dict()` existente porém reimplementado manualmente nas rotas.

### AP-17 — Error handling inadequado / não centralizado
**Sinais:**
- `except:` / `except Exception` genérico em **todo** handler; `catch` vazio; callback que ignora `err`.
- `return jsonify({"erro": str(e)}), 500` (vaza detalhes) ou erro engolido silenciosamente.
- Ausência de handler global (`@app.errorhandler`, `app.use((err, req, res, next) => ...)`).
- Códigos de erro em retorno de função (`return {"erro": ...}` no model) em vez de exceções de domínio.

### AP-18 — Uso de APIs deprecated
Verifique **sempre**. Recomende o equivalente moderno.

| Stack | API deprecated / legada | Equivalente moderno |
|---|---|---|
| Python ≥ 3.12 | `datetime.utcnow()`, `datetime.utcfromtimestamp()` | `datetime.now(timezone.utc)`, `datetime.fromtimestamp(ts, timezone.utc)` |
| Python | `distutils`, `pkg_resources`, `imp`, `asyncio.get_event_loop()` fora de loop, `logging.warn` | `setuptools`/`packaging`, `importlib.metadata`, `importlib`, `asyncio.run`, `logging.warning` |
| SQLAlchemy 2.x / Flask-SQLAlchemy 3.x | `Model.query.get(id)` (Legacy Query API), `engine.execute()` | `db.session.get(Model, id)`, `with engine.connect()` / `db.session.execute(select(...))` |
| Flask ≥ 2.3 | `@app.before_first_request`, `flask.json.JSONEncoder`, `_app_ctx_stack`, `app.env`, `FLASK_ENV` | código de startup na factory, `app.json` provider, `g`/`current_app`, `app.debug`/`FLASK_DEBUG` |
| Node.js | `new Buffer()`, `url.parse()`, `fs.exists()`, `crypto.createCipher()`, `util.isArray()`, `querystring` | `Buffer.from/alloc`, `new URL()`, `fs.existsSync`/`fs.promises.access`, `crypto.createCipheriv()`, `Array.isArray`, `URLSearchParams` |
| Express | `body-parser` separado (Express ≥ 4.16), `req.param()`, `res.send(status)`, `res.json(status, body)`, `app.del()`, `res.sendfile()` | `express.json()`/`express.urlencoded()`, `req.params`/`req.query`/`req.body`, `res.sendStatus()`/`res.status().send()`, `app.delete()`, `res.sendFile()` |

```bash
grep -rnE "utcnow\(|utcfromtimestamp|\.query\.get\(|before_first_request|JSONEncoder|pkg_resources|distutils" --include=*.py .
grep -rnE "new Buffer\(|url\.parse\(|fs\.exists\(|createCipher\(|body-parser|req\.param\(|app\.del\(|sendfile\(" --include=*.js --include=*.ts . | grep -v node_modules
```
Se nada for encontrado, declare explicitamente no relatório: "Nenhuma API deprecated detectada".

### AP-19 — Callback hell / pyramid of doom
**Sinais:** ≥ 3 níveis de callbacks aninhados (`db.get(..., (err, x) => { db.run(..., function(err) { ... }) })`), contadores manuais de pendências (`pending--; if (pending === 0) res.json(...)`), `const self = this` para escapar de `function()`.
**Correto:** `async/await` com promisificação (`util.promisify`, drivers com API de Promise).

### AP-20 — `print`/`console.log` como logging e side-effects simulados
**Sinais:** `print("ERRO: ...")`, `console.log` em handlers, "notificações" implementadas como `print("ENVIANDO EMAIL ...")` dentro do controller, banners de start com `print`.
**Correto:** módulo `logging` / logger configurável; notificações extraídas para um service injetável.

---

## LOW

### AP-21 — Magic numbers / strings
**Sinais:** limites e faixas literais (`if faturamento > 10000: desconto = faturamento * 0.1`), `len(password) < 4`, `priority <= 2`, portas, listas de status/categorias/roles literais repetidas, `'#000000'`.
**Correto:** constantes nomeadas em um módulo de domínio/config.

### AP-22 — Nomes pouco expressivos
**Sinais:** variáveis de 1–3 letras fora de loops triviais (`u`, `e`, `p`, `cc`, `cid`, `c`), campos de payload abreviados (`usr`, `eml`, `pwd`), nomes que mentem (`badCrypto`, `AppManager`, `logAndCache` que faz duas coisas), `id` sombreando builtin.
**Nota:** nomes que fazem parte do **contrato da API** (chaves do JSON de entrada/saída) devem ser mantidos; renomeie apenas internamente.

### AP-23 — Imports não utilizados / código morto
**Sinais:** `import os, sys, json` sem uso, funções utilitárias nunca chamadas, exports nunca importados (`totalRevenue`), variáveis atribuídas e não lidas, dependências declaradas sem uso.
```bash
# Python: confira cada nome importado
grep -nE "^(from .+ )?import " <arquivo>
```

### AP-24 — Código não idiomático / condicionais verbosas
**Sinais:** `if cond: return True else: return False`, ifs aninhados em escada que podem ser uma expressão, `type(x) == list` (use `isinstance`), `x = x + 1` em contadores, comparação manual de status repetida em vez de método do model.
