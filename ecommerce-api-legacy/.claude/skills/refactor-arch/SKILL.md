---
name: refactor-arch
description: Audita e refatora uma codebase de backend (qualquer linguagem/framework) para o padrão MVC. Executa 3 fases — análise da stack, auditoria de anti-patterns com relatório por severidade (CRITICAL/HIGH/MEDIUM/LOW) e refatoração validada. Use quando o usuário pedir para auditar arquitetura, encontrar code smells, ou refatorar um projeto legado para MVC.
argument-hint: "[caminho opcional para salvar o relatório da Fase 2]"
---

# refactor-arch — Auditoria e Refatoração Arquitetural para MVC

Você é um arquiteto de software sênior. Sua missão é analisar o projeto do **diretório de trabalho atual**, auditar a codebase contra um catálogo de anti-patterns e, **somente após confirmação explícita do usuário**, refatorá-la para o padrão MVC, garantindo que a aplicação continue funcionando.

A skill é **agnóstica de tecnologia**: nunca presuma a stack — detecte-a. Todo o conhecimento de domínio está nos arquivos de referência abaixo. Leia cada um **no momento indicado** (não antes), e siga-os à risca.

| Arquivo | Quando ler | Para quê |
|---|---|---|
| [references/project-analysis.md](references/project-analysis.md) | Fase 1 | Heurísticas de detecção de linguagem, framework, banco, domínio e arquitetura |
| [references/anti-patterns-catalog.md](references/anti-patterns-catalog.md) | Fase 2 | Catálogo de anti-patterns, sinais de detecção e severidade |
| [references/report-template.md](references/report-template.md) | Fase 2 | Formato obrigatório do relatório de auditoria |
| [references/mvc-guidelines.md](references/mvc-guidelines.md) | Fase 3 | Arquitetura alvo, responsabilidades de cada camada, regras de compatibilidade |
| [references/refactoring-playbook.md](references/refactoring-playbook.md) | Fase 3 | Transformações concretas (antes/depois) para cada anti-pattern |
| [references/validation.md](references/validation.md) | Fase 3 | Protocolo de baseline, boot e smoke test dos endpoints |

## Regras invioláveis

1. **Nenhum arquivo do projeto é criado, alterado ou removido antes da confirmação no fim da Fase 2.** As Fases 1 e 2 são somente leitura. A única escrita permitida antes da confirmação é salvar o relatório no caminho passado em `$ARGUMENTS` (se houver).
2. **Nunca reproduza valores de segredos** (senhas, chaves, tokens, connection strings) no terminal ou no relatório. Cite apenas o *nome* da variável e o local (`arquivo:linha`) e escreva `<redacted>` no lugar do valor.
3. **Cada finding precisa de evidência real**: arquivo e linha(s) exatos, conferidos lendo o arquivo (use numeração de linhas — `cat -n`, `grep -n` ou a ferramenta Read). Nunca invente linhas.
4. **Preserve o contrato da API** (rotas, métodos HTTP, status codes, formato do JSON) — exceto quando a mudança for correção de segurança listada no relatório (ver `mvc-guidelines.md` § Compatibilidade).
5. **Não toque** em `.claude/`, `.git/`, `node_modules/`, ambientes virtuais (`.venv/`, `venv/`) nem em lockfiles, a não ser para adicionar/remover dependências estritamente necessárias.
6. Se algo falhar na validação, **corrija e valide de novo** (até 3 tentativas). Nunca declare sucesso sem ter executado a validação.

---

## FASE 1 — Análise do Projeto (somente leitura)

1. Leia `references/project-analysis.md`.
2. Inventarie os arquivos-fonte (excluindo dependências, builds, venvs, `.claude/`), conte arquivos e linhas.
3. Detecte: linguagem, framework + versão, dependências relevantes, banco de dados, entry point e como a aplicação é executada (comando + porta).
4. Mapeie a arquitetura atual: camadas existentes, responsabilidades de cada arquivo, tabelas/entidades.
5. Monte o **inventário de endpoints** (método + rota + arquivo:linha). Ele será usado na validação da Fase 3.
6. Infira o domínio da aplicação a partir de entidades, tabelas e rotas.
7. Imprima o resumo exatamente neste formato:

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <linguagem + versão se detectável>
Framework:     <framework + versão>
Dependencies:  <libs relevantes>
Database:      <engine + forma de acesso (ORM / driver cru)>
Domain:        <descrição curta do domínio (entidades principais)>
Architecture:  <classificação + justificativa curta>
Entry point:   <arquivo> (<comando de execução>, porta <n>)
Source files:  <n> files analyzed (~<loc> lines)
DB tables:     <tabelas/entidades>
Endpoints:     <n> routes mapped
================================
```

Em seguida, liste o inventário de endpoints em uma tabela curta.

---

## FASE 2 — Auditoria (somente leitura)

1. Leia `references/anti-patterns-catalog.md` e `references/report-template.md`.
2. Percorra **todos** os arquivos-fonte, cruzando-os com **cada** anti-pattern do catálogo. Use os sinais de detecção (padrões de grep) do catálogo como ponto de partida, mas **confirme lendo o código** — sem falsos positivos.
3. Agrupe ocorrências do mesmo anti-pattern no mesmo arquivo em um único finding (listando todas as linhas). O mesmo anti-pattern em arquivos diferentes pode virar findings separados quando a correção for diferente.
4. Classifique cada finding pela severidade do catálogo (ajuste apenas com justificativa explícita). Inclua **sempre** a verificação de APIs deprecated (AP-18).
5. Ordene os findings: CRITICAL → HIGH → MEDIUM → LOW.
6. Gere o relatório **exatamente** no formato de `report-template.md` e imprima-o.
7. Se `$ARGUMENTS` contiver um caminho, salve o relatório (Markdown) nesse caminho.
8. **PARE e peça confirmação**, imprimindo exatamente:

```
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

Encerre sua resposta aqui e **aguarde** a resposta do usuário. Não inicie a Fase 3 na mesma resposta, em hipótese alguma.
- Resposta `n` (ou qualquer coisa diferente de confirmação): encerre sem modificar nada.
- Resposta `y`/sim: siga para a Fase 3. Se o usuário pedir para limitar o escopo (ex.: "só CRITICAL e HIGH"), respeite.

---

## FASE 3 — Refatoração e Validação

1. Leia `references/mvc-guidelines.md`, `references/refactoring-playbook.md` e `references/validation.md`.
2. **Baseline** (antes de qualquer edição): suba a aplicação original e registre as respostas de todos os endpoints do inventário, seguindo `validation.md` § Baseline. Se não for possível subir a versão original, registre o motivo e prossiga.
3. **Planeje** a estrutura alvo com base em `mvc-guidelines.md`, adaptando-a ao estado atual:
   - Projeto monolítico → criar as camadas do zero.
   - Projeto parcialmente organizado → **reaproveitar** o que já está correto, mover responsabilidades para a camada certa e criar só o que falta (ex.: `controllers/`, `config/`, `middlewares/`).
   Imprima a árvore planejada antes de editar.
4. **Execute** as transformações do playbook, na ordem: segurança (CRITICAL) → estrutura MVC → HIGH → MEDIUM → LOW. Para cada finding do relatório, aplique a transformação indicada (`T-xx`).
5. **Atualize** artefatos de execução que dependam da estrutura: manifesto de dependências, scripts de start, README do projeto (como rodar e variáveis de ambiente), e crie `.env.example` com as variáveis necessárias (sem valores reais de segredos).
6. **Remova** os arquivos antigos que foram completamente substituídos (não deixe código morto duplicado).
7. **Valide** seguindo `validation.md`: imports/compilação, boot sem erros, smoke test de todos os endpoints do inventário comparado à baseline, e uma nova varredura dos anti-patterns CRITICAL/HIGH na nova base. Corrija e repita até passar.
8. Encerre os processos que você iniciou e remova arquivos temporários (ex.: bancos SQLite de teste criados pela validação).
9. Imprima o resumo final:

```
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
<árvore de diretórios>

## Changes Applied
<finding → transformação aplicada, um por linha, com severidade>

## Intentional Contract Changes
<mudanças de contrato por segurança, ou "None">

## Validation
  ✓/✗ Application boots without errors
  ✓/✗ All endpoints respond correctly (<n>/<n> matched baseline)
  ✓/✗ Zero CRITICAL/HIGH anti-patterns remaining
  ✓/✗ <outras checagens executadas>

## Remaining Recommendations
<itens fora do escopo ou não corrigidos, com justificativa>
================================
```

Use `✗` com explicação honesta para qualquer verificação que não passou.
