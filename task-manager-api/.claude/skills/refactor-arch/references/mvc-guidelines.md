# Guidelines de Arquitetura — MVC Alvo (Fase 3)

Em APIs HTTP o "V" do MVC é a **camada de apresentação HTTP**: as rotas que recebem a requisição e serializam a resposta (JSON). Não há templates HTML, então **Views = Routes**.

## 1. Camadas e responsabilidades

| Camada | Responsabilidade | Pode depender de | NUNCA deve |
|---|---|---|---|
| **config/** | Ler configuração do ambiente (env vars, `.env`), defaults seguros, constantes de execução | — | Conter segredos reais como default |
| **models/** | Representar entidades e acessar dados: schema/ORM, queries (parametrizadas), mapeamento linha → objeto/dict, serialização segura (`to_dict` sem campos sensíveis), regras **intrínsecas** à entidade (ex.: `task.is_overdue()`) | database/infra | Conhecer HTTP (`request`, `res`, status codes), enviar e-mails, ler config de request |
| **controllers/** | Fluxo da aplicação e regra de negócio: validar entrada, orquestrar models e services, transações, cálculos de domínio, lançar erros de domínio | models, services, utils | Conhecer HTTP (sem `request`/`jsonify`/`req`/`res`), escrever SQL cru |
| **views/** ou **routes/** | Mapear método + path → controller; extrair dados do request (body, params, query); chamar o controller; serializar a resposta e o status code | controllers | Acessar banco, conter regra de negócio, validar regras de domínio |
| **services/** (opcional) | Integrações externas e efeitos colaterais: e-mail, gateway de pagamento, hashing, notificações | config | Acessar request/response |
| **middlewares/** | Preocupações transversais: error handler central, autenticação, logging de requisições | utils (erros) | Conter regra de negócio |
| **database/** (ou dentro de models) | Conexão, ciclo de vida, schema e seed | config | Ser estado global mutável compartilhado sem controle |
| **utils/** | Funções puras e genéricas (erros de domínio, validadores, formatação de datas) | — | Depender de camadas superiores |
| **app (composition root)** | Criar a aplicação, carregar config, inicializar banco, registrar rotas e middlewares, injetar dependências | todas | Conter rotas ou regra de negócio |
| **entry point** | Ler host/porta da config e iniciar o servidor | app | Qualquer outra coisa |

**Regra de dependência:** `views → controllers → models/services → database/config`. Nunca no sentido inverso. Erros sobem como **exceções de domínio** (`NotFoundError`, `ValidationError`, `ConflictError`, ...) e são traduzidos em HTTP **apenas** no error handler central.

## 2. Estruturas alvo por stack

Ajuste nomes ao idioma/convenção do projeto (ex.: `produto_model.py` em projeto em português). Não crie camadas vazias.

### Python / Flask (driver SQL cru)
```
<projeto>/
├── app.py                      # entry point fino: create_app() + app.run(host, port da config)
├── src/
│   ├── app.py                  # composition root: create_app(config) → registra blueprints, error handlers, db
│   ├── config/settings.py      # classe Settings lida de os.environ (com defaults seguros)
│   ├── database/connection.py  # conexão por request (flask.g) + teardown; schema.py / seed.py
│   ├── models/<entidade>_model.py
│   ├── controllers/<entidade>_controller.py
│   ├── views/<entidade>_routes.py   # Blueprints
│   ├── services/<integração>_service.py
│   ├── middlewares/error_handler.py
│   └── utils/errors.py, validators.py
├── requirements.txt
└── .env.example
```

### Python / Flask + SQLAlchemy (projeto já com pastas)
Mantenha o layout de pacotes existente (`models/`, `routes/`, `services/`, `utils/`) e **acrescente** o que falta:
```
<projeto>/
├── app.py                 # create_app() + entry point
├── config/settings.py
├── database.py            # instância db (extensão) — pode permanecer
├── models/                # ORM + regras intrínsecas + to_dict seguro
├── controllers/           # NOVO: regras de negócio que estavam nas rotas
├── routes/                # Views: blueprints finos
├── services/              # integrações (config injetada)
├── middlewares/error_handler.py
└── utils/                 # erros de domínio, validadores, helpers de data
```

### Node.js / Express
```
<projeto>/
├── src/
│   ├── server.js | app.js      # entry point: createApp() + listen(config.port)
│   ├── app.js | createApp.js   # composition root (pode ser o mesmo arquivo do entry se for curto)
│   ├── config/index.js         # process.env + defaults seguros
│   ├── database/connection.js  # conexão + helpers promisificados; schema.js / seed.js
│   ├── models/<entidade>Model.js
│   ├── controllers/<recurso>Controller.js
│   ├── routes/index.js         # Views: express.Router()
│   ├── services/<integração>Service.js
│   ├── middlewares/errorHandler.js, asyncHandler.js
│   └── utils/errors.js
├── package.json                # "start" apontando para o entry point
└── .env.example
```

### Outras stacks
Mesmo princípio: Django (`models.py` / `views.py` finos + `services.py`), FastAPI (`routers/` + `services/` + `models/`), Spring (`@RestController` → `@Service` → `@Repository`). Use a convenção idiomática do framework.

## 3. Regras de implementação

1. **Composition root único:** `create_app()` / `createApp()` monta tudo; dependências (conexão, services) são passadas ou resolvidas ali — nada de instanciar infraestrutura dentro de regra de negócio.
2. **Config:** tudo que varia por ambiente vem de env vars. Segredos **sem default real** (gere um aleatório em dev ou falhe com mensagem clara). `DEBUG` desligado por padrão. Porta configurável (`PORT`) mantendo a porta original como default.
3. **Views finas:** cada handler tem tipicamente ≤ 10 linhas: extrair input → chamar controller → `jsonify`/`res.json` com status.
4. **Controllers sem HTTP:** recebem dicts/valores, retornam dados; sinalizam falhas com exceções de domínio.
5. **Models seguros:** só queries parametrizadas; serialização sem senha/hash/segredos; consultas agregadas com JOIN/GROUP BY em vez de N+1.
6. **Transações:** operações com múltiplas escritas em uma transação (commit único, rollback em erro).
7. **Error handling central:** um handler mapeia exceções de domínio → status code e formato de erro do projeto; exceções inesperadas → 500 com mensagem genérica + log.
8. **Logging:** `logging`/logger em vez de `print`/`console.log` espalhados.
9. **Sem código morto:** remova arquivos e funções substituídos, imports não usados.
10. **Entry point claro:** o comando de execução documentado no README continua funcionando (`python app.py`, `npm start`).

## 4. Compatibilidade de contrato (obrigatório)

Preserve, para cada endpoint do inventário da Fase 1:
- método HTTP e path;
- status codes de sucesso e de erro de validação/não encontrado;
- formato do JSON (nomes das chaves, envelope como `{"dados": ..., "sucesso": true}`), idioma das mensagens e chaves de entrada (mesmo que mal nomeadas — renomeie só variáveis internas).

**Mudanças de contrato permitidas** (devem estar listadas em "Proposed Contract Changes" do relatório e em "Intentional Contract Changes" no resumo final):
- remover campos sensíveis das respostas (senha, hash, segredo, config interna);
- remover endpoints que executam código/SQL arbitrário;
- exigir credencial e perfil autorizado em **operações administrativas** (deleção de contas, mudança de `role`/`active`, criação de conta privilegiada, alteração de dados de acesso de outro usuário, reset, relatórios financeiros) — obrigatório quando houver finding AP-04/AP-12 (ver T-06);
- substituir a senha fixa de contas administrativas criadas por seed por valor vindo do ambiente ou aleatório;
- trocar mensagens de erro internas (`str(e)`) por mensagens genéricas;
- passar a responder `404` onde antes um recurso inexistente era tratado como sucesso, ou `400` onde antes uma entrada inválida gerava `500`;
- corrigir integridade (ex.: deleção em cascata em vez de deixar órfãos).

Qualquer outra mudança de contrato é proibida.

## 5. Adaptação ao nível de organização

| Estado atual | Estratégia |
|---|---|
| Monolito (1–4 arquivos misturando tudo) | Criar a estrutura alvo do zero; migrar função por função; manter um entry point na raiz se o comando de execução depender dele |
| Pseudo-camadas (`models.py`/`controllers.py` planos) | Dividir por domínio e reposicionar responsabilidades (SQL → models, regras → controllers, HTTP → views) |
| Parcialmente em camadas | Preservar pacotes corretos; extrair regra de negócio das rotas para `controllers/`; criar `config/`, `middlewares/`; corrigir models (serialização, hashing); eliminar duplicação |
| Já em MVC | Focar nos findings de segurança/performance/qualidade sem reestruturar |

## 6. Definição de pronto

- [ ] Estrutura de diretórios segue o padrão MVC acima
- [ ] Configuração extraída para módulo de config (sem segredos hardcoded)
- [ ] Models abstraem o acesso a dados
- [ ] Views/Routes apenas roteiam e serializam
- [ ] Controllers concentram o fluxo da aplicação
- [ ] Error handling centralizado
- [ ] Operações administrativas exigem credencial verificada (401/403 testados)
- [ ] Entry point claro
- [ ] Aplicação inicia sem erros
- [ ] Endpoints originais respondem corretamente (comparados à baseline)
