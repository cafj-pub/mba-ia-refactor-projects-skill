# Protocolo de Validação (Fase 3)

A refatoração só está concluída quando a aplicação **sobe sem erros** e **todos os endpoints do inventário** respondem de forma equivalente à versão original (exceto as mudanças de contrato intencionais).

Arquivos auxiliares de validação (scripts, specs, saídas) ficam **fora do projeto** (ex.: `/tmp/refactor-arch/<projeto>/`) — nunca commite artefatos de validação.

## 1. Preparação do ambiente

| Stack | Preparação |
|---|---|
| Python | Use o venv do projeto se existir (`.venv/bin/python`); senão crie um: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt` |
| Node | `npm install` (ou `npm ci` se houver lockfile) |

Se o runtime não estiver instalado, informe o usuário e peça orientação — não declare sucesso sem executar.

**Porta:** antes de subir, verifique se a porta está livre (`lsof -nP -iTCP:<porta> -sTCP:LISTEN`). No macOS a 5000 costuma estar ocupada pelo AirPlay. Se estiver ocupada:
- versão original com porta hardcoded → suba via wrapper sem editar o código, ex.: `python -c "from app import app; app.run(port=5055, debug=False)"` (com `debug=True` o reloader do Werkzeug não funciona com `python -c`);
- versão refatorada → use a variável `PORT` (que a refatoração deve suportar).

**Processos:** encerre servidores **pela porta** (`kill $(lsof -t -iTCP:<porta> -sTCP:LISTEN)`), não por `pkill -f` com caminho — o padrão costuma não bater e o processo antigo continua respondendo, invalidando a validação seguinte. Antes de cada boot confirme que a porta está livre.

**Banco:** use um banco descartável para a validação (cópia ou arquivo novo; `DATABASE_PATH`/`DATABASE_URL` apontando para `/tmp`). Se o projeto exige seed (`seed.py`), rode-o antes. Execute baseline e pós-refatoração **com o mesmo estado inicial** de banco.

## 2. Baseline (antes de editar)

1. Monte a lista de requisições a partir do inventário da Fase 1 e dos exemplos do projeto (`*.http`, README). Para cada endpoint inclua:
   - o caminho feliz (com payload válido);
   - ao menos um caso de erro esperado (404 de recurso inexistente, 400 de payload inválido);
   - ordene para que leituras venham antes de escritas destrutivas (DELETE por último);
   - se a refatoração vai passar a exigir credencial (ex.: `X-Admin-Token`), **inclua o header já no spec da baseline** — a versão original ignora headers extras e assim o mesmo spec serve para as duas execuções;
   - no zsh variáveis não sofrem word-splitting: passe headers do `curl` literalmente (`-H 'Content-Type: application/json'`), não via `$VAR`.
2. Suba a aplicação original em background, aguarde ficar pronta (poll em `/` ou `/health` por até ~15s).
3. Execute as requisições e salve, para cada uma: método, path, status, `Content-Type` e corpo.
4. Derrube o processo e restaure o banco ao estado inicial.

Script genérico (salve em `/tmp/refactor-arch/smoke.py`; usa apenas biblioteca padrão):

```python
import json, sys, urllib.request, urllib.error

def call(base, method, path, body=None, headers=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(base + path, data=data, method=method,
                                 headers={"Content-Type": "application/json", **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            status, raw = r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        status, raw = e.code, e.read().decode()
    try:
        payload = json.loads(raw)
    except ValueError:
        payload = raw
    return {"method": method, "path": path, "status": status, "body": payload}

def render(headers, variables):
    out = {}
    for key, value in (headers or {}).items():
        for name, var in variables.items():
            value = value.replace("{{" + name + "}}", str(var))
        out[key] = value
    return out

if __name__ == "__main__":
    base, spec_file, out_file = sys.argv[1:4]
    # [{"method": "POST", "path": "/login", "body": {...}, "capture": {"admin_token": "token"}},
    #  {"method": "DELETE", "path": "/users/3", "headers": {"Authorization": "Bearer {{admin_token}}"}}]
    spec = json.load(open(spec_file))
    variables, results = {}, []
    for s in spec:
        result = call(base, s["method"], s["path"], s.get("body"), render(s.get("headers"), variables))
        for name, field in s.get("capture", {}).items():
            if isinstance(result["body"], dict):
                variables[name] = result["body"].get(field, "")
        results.append(result)
    json.dump(results, open(out_file, "w"), indent=2, ensure_ascii=False)
    for r in results:
        print(f'{r["status"]}  {r["method"]:6} {r["path"]}')
```

## 3. Validação pós-refatoração

1. **Estática:** compile/importe todos os módulos (`python -m compileall -q .` excluindo venv; `node --check` em cada arquivo `.js`). Confirme que não há imports quebrados.
2. **Boot:** suba a aplicação refatorada pelo comando documentado (com `PORT` se necessário). O log não pode conter traceback/erro. Confirme que o processo continua vivo após a primeira requisição.
3. **Smoke test:** rode o mesmo spec da baseline e compare:
   - status code **igual** para cada requisição;
   - todas as chaves do JSON original continuam presentes com o mesmo tipo (ignore valores voláteis: timestamps, ids autoincrementais, hashes). **Chaves novas são compatíveis** (ex.: padronizar erros com `"sucesso": false`); chaves removidas/renomeadas são quebra;
   - mesma quantidade de itens em listagens (se a ordem original era não determinística — ex.: callbacks concorrentes — compare como conjunto e registre a ordenação determinística como mudança intencional);
   - para endpoints de cálculo (relatórios, totais), **valores** iguais aos da baseline.
   Diferenças só são aceitas se estiverem em "Intentional Contract Changes" — liste cada uma explicitamente.
4. **Autorização (obrigatório se houver finding AP-04/AP-12):** para **cada** operação administrativa do relatório, execute e registre:
   - sem credencial → `401` (ou `403` no modelo `X-Admin-Token`);
   - credencial inválida/expirada/adulterada → `401`/`403`;
   - credencial válida de usuário **sem** permissão (ex.: perfil `user`) → `403`, e confirme que o dado **não** mudou;
   - credencial de admin → mesmo status da baseline.
   Se o spec precisa de um token, capture-o de uma resposta anterior (ex.: login do admin) com `"capture"` e use `{{var}}` nos headers; a versão original ignora o header, então o mesmo spec serve para baseline e pós-refatoração.
5. **Re-auditoria:** rode novamente os greps do catálogo para AP-01, AP-02, AP-04, AP-05, AP-06, AP-08 e confira que não restaram ocorrências na nova base (ignorando `.env.example`, testes e a pasta `.claude/`).
6. **Limpeza:** derrube os processos iniciados (`kill <pid>`), remova bancos temporários e `__pycache__` gerados pela validação.

Comparação sugerida (Python):

```python
import json, sys
VOLATILE = {"criado_em", "created_at", "updated_at", "timestamp", "generated_at", "token"}

def compatible(before, after):
    """True se `after` preserva o formato de `before` (chaves extras em `after` são aceitas)."""
    if isinstance(before, dict):
        return isinstance(after, dict) and all(
            k in after and compatible(v, after[k]) for k, v in before.items() if k not in VOLATILE)
    if isinstance(before, list):
        return isinstance(after, list) and len(before) == len(after) and all(
            compatible(b, a) for b, a in zip(before, after))
    if isinstance(before, (int, float)) and not isinstance(before, bool):
        return isinstance(after, (int, float)) and not isinstance(after, bool)
    return type(before) is type(after)

before, after = (json.load(open(f)) for f in sys.argv[1:3])
ok = 0
for b, a in zip(before, after):
    same = b["status"] == a["status"] and compatible(b["body"], a["body"])
    ok += same
    print(("✓" if same else "✗"), b["method"], b["path"], b["status"], "->", a["status"])
print(f"{ok}/{len(before)} matched")
```
Cada `✗` precisa corresponder a um item de "Intentional Contract Changes"; caso contrário, é regressão a corrigir.

## 4. Critérios de sucesso

- ✓ Aplicação inicia sem erros
- ✓ Todos os endpoints do inventário respondem (status e formato equivalentes à baseline)
- ✓ Diferenças restritas às mudanças de contrato intencionais
- ✓ Zero ocorrências de anti-patterns CRITICAL/HIGH na nova base

Se algum critério falhar: diagnostique, corrija e repita a validação (até 3 ciclos). Persistindo a falha, reporte com `✗` e a causa no resumo final — nunca omita.
