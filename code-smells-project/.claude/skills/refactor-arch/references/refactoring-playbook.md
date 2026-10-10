# Playbook de Refatoração (Fase 3)

Transformações concretas, cada uma ligada aos anti-patterns do catálogo. Os exemplos mostram Python/Flask e Node/Express; aplique o mesmo raciocínio em outras stacks com as APIs idiomáticas delas.

| ID | Transformação | Resolve |
|---|---|---|
| T-01 | Externalizar configuração e segredos | AP-01, AP-11 |
| T-02 | Queries parametrizadas | AP-02 |
| T-03 | Decompor God Class/File em camadas MVC | AP-03 |
| T-04 | Hash seguro de senhas | AP-05 |
| T-05 | Remover dados sensíveis de respostas e logs | AP-06 |
| T-06 | Remover ou proteger endpoints perigosos; autenticação mínima | AP-04, AP-12 |
| T-07 | Extrair regra de negócio para controllers (views finas) | AP-07, AP-16 |
| T-08 | Substituir estado global por injeção de dependência / app factory | AP-08, AP-09 |
| T-09 | Eliminar N+1 e agregações ineficientes | AP-13, AP-14 |
| T-10 | Error handling centralizado com exceções de domínio | AP-17 |
| T-11 | Transações e integridade referencial | AP-10 |
| T-12 | Substituir APIs deprecated | AP-18 |
| T-13 | Callback hell → async/await | AP-19 |
| T-14 | Centralizar validação de entrada | AP-15 |
| T-15 | Constantes nomeadas, nomes expressivos, limpeza | AP-16, AP-21–AP-24 |
| T-16 | Logging e services para side-effects | AP-20 |

---

## T-01 — Externalizar configuração e segredos

**Antes (Python)**
```python
app.config["SECRET_KEY"] = "minha-chave-secreta"
app.config["DEBUG"] = True
app.run(host="0.0.0.0", port=5000, debug=True)
```
**Depois**
```python
# src/config/settings.py
import os, secrets

def _bool(value, default=False):
    return default if value is None else value.strip().lower() in ("1", "true", "yes", "on")

class Settings:
    def __init__(self, env=os.environ):
        self.SECRET_KEY = env.get("SECRET_KEY") or secrets.token_hex(32)  # aleatória em dev; defina em produção
        self.DEBUG = _bool(env.get("FLASK_DEBUG"))
        self.HOST = env.get("HOST", "127.0.0.1")
        self.PORT = int(env.get("PORT", "5000"))
        self.DATABASE_PATH = env.get("DATABASE_PATH", "loja.db")
        self.CORS_ORIGINS = env.get("CORS_ORIGINS", "*")

# app.py (entry point)
settings = Settings()
app = create_app(settings)
app.run(host=settings.HOST, port=settings.PORT, debug=settings.DEBUG)
```
**Antes (Node)**
```js
const config = { dbPass: "senha_prod", paymentGatewayKey: "pk_live_xxx", port: 3000 };
```
**Depois**
```js
// src/config/index.js
const config = Object.freeze({
  port: Number(process.env.PORT) || 3000,
  databaseUrl: process.env.DATABASE_URL || ':memory:',
  paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || '',  // sem default real
});
module.exports = config;
```
Crie `.env.example` listando as variáveis (valores fictícios/vazios) e documente no README.

## T-02 — Queries parametrizadas

**Antes**
```python
cursor.execute("SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'")
query += " AND (nome LIKE '%" + termo + "%')"
```
**Depois**
```python
cursor.execute("SELECT * FROM usuarios WHERE email = ?", (email,))
clauses, params = ["1=1"], []
if termo:
    clauses.append("(nome LIKE ? OR descricao LIKE ?)")
    params += [f"%{termo}%", f"%{termo}%"]
cursor.execute(f"SELECT * FROM produtos WHERE {' AND '.join(clauses)}", params)
```
**Node (`sqlite3`)**: `db.get("SELECT * FROM users WHERE email = ?", [email])`. Nunca interpole valores; apenas fragmentos SQL **fixos** do código podem ser compostos.

## T-03 — Decompor God Class/File em camadas MVC

**Antes** — um arquivo/classe com conexão, schema, rotas e regra:
```js
class AppManager {
  constructor() { this.db = new sqlite3.Database(':memory:'); }
  initDb() { /* CREATE TABLE + seeds */ }
  setupRoutes(app) {
    app.post('/api/checkout', (req, res) => { /* validação + SQL + pagamento + auditoria */ });
  }
}
```
**Depois** — uma responsabilidade por módulo:
```js
// database/connection.js   → cria a conexão e expõe run/get/all em Promise
// database/schema.js       → CREATE TABLE + seed
// models/courseModel.js    → findActiveById(id)
// controllers/checkoutController.js → checkout({ name, email, password, courseId, card })
// routes/index.js          → router.post('/api/checkout', asyncHandler(checkoutView))
// app.js                   → createApp(): conecta, injeta, registra rotas e errorHandler
```
Passo a passo:
1. Liste cada função/bloco do God File e classifique-o (config, infra, model, controller, view).
2. Crie os módulos alvo (ver `mvc-guidelines.md`) e mova o código **sem mudar comportamento**.
3. Substitua chamadas cruzadas por imports da camada correta (views → controllers → models).
4. Reaponte o entry point e remova o arquivo antigo.

## T-04 — Hash seguro de senhas

**Antes**
```python
self.password = hashlib.md5(pwd.encode()).hexdigest()
cursor.execute("INSERT INTO usuarios (..., senha) VALUES (?, ...)", (senha_em_texto_puro, ...))
```
**Depois (Python — Werkzeug já vem com Flask)**
```python
from werkzeug.security import generate_password_hash, check_password_hash

def set_password(self, raw):
    self.password = generate_password_hash(raw)

def check_password(self, raw):
    return check_password_hash(self.password, raw)
```
**Antes (Node)**
```js
function badCrypto(pwd) { /* base64 em loop */ }
```
**Depois (Node — módulo nativo `crypto`)**
```js
const crypto = require('crypto');
function hashPassword(password) {
  const salt = crypto.randomBytes(16).toString('hex');
  const hash = crypto.scryptSync(password, salt, 64).toString('hex');
  return `scrypt$${salt}$${hash}`;
}
function verifyPassword(password, stored) {
  const [, salt, hash] = stored.split('$');
  const candidate = crypto.scryptSync(password, salt, 64);
  return crypto.timingSafeEqual(candidate, Buffer.from(hash, 'hex'));
}
```
Seeds também devem gravar o hash. Login: buscar por e-mail e verificar o hash (nunca `WHERE senha = ?`).

**Bancos existentes com hash legado** (ex.: MD5 hex de 32 caracteres): não invalide as contas. Reconheça o formato legado, verifique-o uma única vez e regrave com o algoritmo novo (migração transparente):
```python
_LEGACY_MD5_HASH = re.compile(r'^[0-9a-f]{32}$')

def check_password(self, raw):
    if _LEGACY_MD5_HASH.match(self.password or ''):
        is_valid = hmac.compare_digest(self.password, hashlib.md5(raw.encode()).hexdigest())
        if is_valid:
            self.set_password(raw)   # o controller faz commit após login bem-sucedido
        return is_valid
    return check_password_hash(self.password, raw)
```

## T-05 — Remover dados sensíveis de respostas e logs

**Antes**
```python
def to_dict(self):
    return {"id": self.id, "email": self.email, "password": self.password}

return jsonify({"status": "ok", "secret_key": app.config["SECRET_KEY"], "debug": True})
```
```js
console.log(`Processando cartão ${cc} na chave ${config.paymentGatewayKey}`);
```
**Depois**
```python
def to_dict(self):
    return {"id": self.id, "email": self.email}  # nunca senha/hash

return jsonify({"status": "ok", "database": "connected", "versao": settings.VERSION})
```
```js
logger.info(`Processando pagamento do cartão final ${card.slice(-4)}`);
```

## T-06 — Remover ou proteger endpoints perigosos; autenticação mínima

**Antes**
```python
@app.route("/admin/query", methods=["POST"])
def executar_query():
    cursor.execute(request.get_json()["sql"])   # SQL arbitrário

@app.route("/admin/reset-db", methods=["POST"])
def reset_database(): ...                       # sem autenticação
```
**Depois**
```python
# /admin/query: REMOVIDO (backdoor). Listar em "Intentional Contract Changes".

# middlewares/auth.py
def require_admin_token(settings):
    def decorator(view):
        @functools.wraps(view)
        def wrapper(*args, **kwargs):
            expected = settings.ADMIN_TOKEN
            provided = request.headers.get("X-Admin-Token", "")
            if not expected or not hmac.compare_digest(provided, expected):
                raise ForbiddenError("Acesso negado")
            return view(*args, **kwargs)
        return wrapper
    return decorator
```
Token falso (`'fake-jwt-token-' + id`) → token **assinado** (ex.: `itsdangerous.URLSafeTimedSerializer(SECRET_KEY).dumps({"user_id": id})`, `jsonwebtoken` no Node), mantendo a chave `token` na resposta.

## T-07 — Extrair regra de negócio para controllers (views finas)

**Antes** — rota faz tudo:
```python
@task_bp.route('/tasks', methods=['POST'])
def create_task():
    data = request.get_json()
    if not data.get('title'): return jsonify({'error': 'Título é obrigatório'}), 400
    if data.get('status') not in ['pending', 'in_progress', 'done', 'cancelled']: ...
    if data.get('user_id') and not User.query.get(data['user_id']): ...
    task = Task(); ...; db.session.add(task); db.session.commit()
    return jsonify(task.to_dict()), 201
```
**Depois**
```python
# routes/task_routes.py (View)
@task_bp.route('/tasks', methods=['POST'])
def create_task():
    task = task_controller.create_task(request.get_json(silent=True))
    return jsonify(task), 201

# controllers/task_controller.py (Controller)
def create_task(data):
    fields = validate_task_payload(data, partial=False)   # lança ValidationError
    _ensure_relations_exist(fields)                        # lança NotFoundError
    task = Task(**fields)
    db.session.add(task)
    db.session.commit()
    return task.to_dict()
```
Duplicações (serialização manual, cálculo de "atrasado") viram **um** método do model (`task.to_dict()`, `task.is_overdue()`) usado por todos.

## T-08 — Substituir estado global por injeção de dependência / app factory

**Antes**
```python
db_connection = None
def get_db():
    global db_connection
    if db_connection is None:
        db_connection = sqlite3.connect("loja.db", check_same_thread=False)
    return db_connection
```
```js
let globalCache = {};
class AppManager { constructor() { this.db = new sqlite3.Database(':memory:'); } }
```
**Depois (Python — conexão por request)**
```python
from flask import g, current_app

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE_PATH"])
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_app(app):
    app.teardown_appcontext(close_db)
```
**Depois (Node — composição)**
```js
// app.js
async function createApp(config) {
  const db = await createConnection(config.databaseUrl);
  const models = createModels(db);
  const controllers = createControllers({ models, services: createServices(config) });
  const app = express();
  app.use(express.json());
  app.use(buildRouter(controllers));
  app.use(errorHandler);
  return app;
}
```
Caches globais sem uso real são removidos; se necessários, viram um objeto injetado com ciclo de vida definido.

## T-09 — Eliminar N+1 e agregações ineficientes

**Antes**
```python
for pedido in pedidos:
    itens = cursor.execute("SELECT * FROM itens_pedido WHERE pedido_id = ?", (pedido["id"],))
    for item in itens:
        prod = cursor.execute("SELECT nome FROM produtos WHERE id = ?", (item["produto_id"],))
```
**Depois — um JOIN e agrupamento em memória**
```python
rows = cursor.execute("""
    SELECT p.id AS pedido_id, i.produto_id, i.quantidade, i.preco_unitario, pr.nome AS produto_nome
    FROM pedidos p
    LEFT JOIN itens_pedido i ON i.pedido_id = p.id
    LEFT JOIN produtos pr ON pr.id = i.produto_id
    WHERE p.id IN (...)""").fetchall()
```
**ORM (SQLAlchemy)**
```python
tasks = Task.query.options(joinedload(Task.user), joinedload(Task.category)).all()
```
**Agregação — várias contagens → uma query**
```python
# Antes: 5 queries
pending = Task.query.filter_by(status='pending').count()
done = Task.query.filter_by(status='done').count()
# Depois: 1 query
counts = dict(db.session.query(Task.status, func.count(Task.id)).group_by(Task.status).all())
```
```sql
SELECT COUNT(*) AS total, COALESCE(SUM(total), 0) AS faturamento,
       SUM(CASE WHEN status = 'pendente' THEN 1 ELSE 0 END) AS pendentes
FROM pedidos;
```

## T-10 — Error handling centralizado com exceções de domínio

**Antes**
```python
def buscar_produto(id):
    try:
        ...
    except Exception as e:
        return jsonify({"erro": str(e)}), 500
```
**Depois**
```python
# utils/errors.py
class AppError(Exception):
    status_code = 500
    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.message = message
        if status_code: self.status_code = status_code
class ValidationError(AppError): status_code = 400
class NotFoundError(AppError):  status_code = 404
class ConflictError(AppError):  status_code = 409

# middlewares/error_handler.py
def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(err):
        return jsonify({"erro": err.message}), err.status_code   # mantém o formato do projeto

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        if isinstance(err, HTTPException): return err
        app.logger.exception("Erro não tratado")
        return jsonify({"erro": "Erro interno do servidor"}), 500
```
**Node**
```js
const asyncHandler = (fn) => (req, res, next) => Promise.resolve(fn(req, res, next)).catch(next);
function errorHandler(err, req, res, next) {
  if (err instanceof AppError) return res.status(err.statusCode).send(err.message);
  console.error(err);
  res.status(500).send('Erro interno');
}
```
Handlers não têm mais `try/except` genérico.

## T-11 — Transações e integridade referencial

**Antes**
```python
cursor.execute("INSERT INTO pedidos ...")
for item in itens:
    cursor.execute("INSERT INTO itens_pedido ...")
    cursor.execute("UPDATE produtos SET estoque = estoque - ? ...")
db.commit()   # falha no meio → dados parciais em conexões compartilhadas
```
**Depois**
```python
with db:   # sqlite3: commit no sucesso, rollback em exceção
    pedido_id = db.execute("INSERT INTO pedidos ...", params).lastrowid
    db.executemany("INSERT INTO itens_pedido ...", itens_params)
    db.executemany("UPDATE produtos SET estoque = estoque - ? WHERE id = ?", estoque_params)
```
**Node**
```js
await db.run('BEGIN');
try {
  await db.run('DELETE FROM payments WHERE enrollment_id IN (SELECT id FROM enrollments WHERE user_id = ?)', [id]);
  await db.run('DELETE FROM enrollments WHERE user_id = ?', [id]);
  await db.run('DELETE FROM users WHERE id = ?', [id]);
  await db.run('COMMIT');
} catch (err) { await db.run('ROLLBACK'); throw err; }
```
Prefira também `FOREIGN KEY ... ON DELETE CASCADE` (com `PRAGMA foreign_keys = ON` no SQLite) ou `cascade='all, delete-orphan'` no ORM.

## T-12 — Substituir APIs deprecated

**Antes**
```python
created_at = db.Column(db.DateTime, default=datetime.utcnow)
user = User.query.get(user_id)
```
```js
const buf = new Buffer(pwd);
app.use(require('body-parser').json());
```
**Depois**
```python
# utils/time.py
def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)  # mantém datetimes naive no banco

created_at = db.Column(db.DateTime, default=utcnow)
user = db.session.get(User, user_id)
```
```js
const buf = Buffer.from(pwd);
app.use(express.json());
```
Mantenha a semântica: se o banco guarda datas naive em UTC, continue gravando naive em UTC.

## T-13 — Callback hell → async/await

**Antes**
```js
db.get(sqlCourse, [cid], (err, course) => {
  db.get(sqlUser, [email], (err, user) => {
    db.run(sqlEnroll, [user.id, cid], function (err) {
      db.run(sqlPay, [this.lastID, course.price], (err) => res.json({ ok: true }));
    });
  });
});
```
**Depois**
```js
// database/connection.js
function promisify(db) {
  return {
    get: (sql, p = []) => new Promise((ok, ko) => db.get(sql, p, (e, row) => (e ? ko(e) : ok(row)))),
    all: (sql, p = []) => new Promise((ok, ko) => db.all(sql, p, (e, rows) => (e ? ko(e) : ok(rows)))),
    run: (sql, p = []) => new Promise((ok, ko) => db.run(sql, p, function (e) { e ? ko(e) : ok({ lastID: this.lastID, changes: this.changes }); })),
  };
}
// controller
const course = await courseModel.findActiveById(courseId);
if (!course) throw new NotFoundError('Curso não encontrado');
const user = await userModel.findOrCreate({ name, email, password });
const enrollmentId = await enrollmentModel.create(user.id, course.id);
```

## T-14 — Centralizar validação de entrada

**Antes** — regras copiadas em create e update, tipo nunca checado:
```python
if "preco" not in dados: return jsonify({"erro": "Preço é obrigatório"}), 400
if preco < 0: ...   # TypeError se vier string → 500
```
**Depois**
```python
# utils/validators.py
def require_fields(data, fields_with_messages):
    if not isinstance(data, dict):
        raise ValidationError("Dados inválidos")
    for field, message in fields_with_messages:
        if field not in data:
            raise ValidationError(message)

def to_number(value, message):
    if isinstance(value, bool):
        raise ValidationError(message)
    try:
        return float(value)
    except (TypeError, ValueError):
        raise ValidationError(message)

# controllers/produto_controller.py
def _validate_produto(dados):
    require_fields(dados, [("nome", "Nome é obrigatório"), ("preco", "Preço é obrigatório"), ...])
    ...
```
Use a mesma função em create e update. Mantenha as mensagens originais. Se o projeto já tem lib de validação (marshmallow, pydantic, joi, zod) declarada, prefira usá-la.

## T-15 — Constantes nomeadas, nomes expressivos, limpeza

**Antes**
```python
if faturamento > 10000: desconto = faturamento * 0.1
elif faturamento > 5000: desconto = faturamento * 0.05
if t.priority <= 2: high_priority = high_priority + 1
def is_admin(self):
    if self.role == 'admin': return True
    else: return False
if type(tags) == list: ...
import os, sys, json   # não usados
```
**Depois**
```python
# constantes de domínio
DISCOUNT_TIERS = ((10000, 0.10), (5000, 0.05), (1000, 0.02))  # (faturamento mínimo, taxa)
HIGH_PRIORITY_THRESHOLD = 2

def calcular_desconto(faturamento):
    return next((faturamento * taxa for limite, taxa in DISCOUNT_TIERS if faturamento > limite), 0)

def is_admin(self):
    return self.role == ROLE_ADMIN

if isinstance(tags, list): ...
# imports não usados removidos
```
```js
// Antes: let u = req.body.usr; let cc = req.body.card;
// Depois (chaves do contrato preservadas, nomes internos claros):
const { usr: name, eml: email, pwd: password, c_id: courseId, card } = req.body;
```

## T-16 — Logging e services para side-effects

**Antes**
```python
print("ENVIANDO EMAIL: Pedido " + str(pedido_id) + " criado")
print("ERRO: " + str(e))
```
**Depois**
```python
# services/notification_service.py
logger = logging.getLogger(__name__)

class NotificationService:
    def pedido_criado(self, pedido_id, usuario_id):
        logger.info("Notificando criação do pedido %s para usuário %s", pedido_id, usuario_id)

# controllers/pedido_controller.py — service injetado/obtido da composição
notification_service.pedido_criado(pedido_id, usuario_id)
```
Configure o logging uma única vez na composição (`logging.basicConfig(level=settings.LOG_LEVEL)`).
