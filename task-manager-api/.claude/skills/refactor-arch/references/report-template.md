# Template do Relatório de Auditoria (Fase 2)

O relatório é impresso no terminal **e** é Markdown válido (pode ser salvo em arquivo sem edição). Siga a estrutura exatamente.

## Regras de preenchimento

- **Ordem:** todos os CRITICAL, depois HIGH, MEDIUM, LOW. Dentro da mesma severidade, ordene por impacto.
- **Numeração:** `#1`, `#2`, ... contínua no relatório inteiro.
- **File:** `caminho/relativo:linha` ou `caminho:inicio-fim`; várias ocorrências separadas por vírgula (`routes/task_routes.py:30-39, 71-80`). Ocorrências em vários arquivos: uma linha `File:` por arquivo.
- **Description:** o que foi encontrado, citando o trecho/identificador concreto (nunca o valor de um segredo — use `<redacted>`).
- **Impact:** consequência concreta para segurança, manutenção, testes ou performance.
- **Recommendation:** ação concreta + ID da transformação do playbook (`T-xx`).
- **Summary:** contagens precisam bater com o número de findings listados.
- **Deprecated APIs:** a seção é obrigatória; se não houver, escreva "Nenhuma API deprecated detectada" e o que foi verificado.
- **Administrative Operations:** seção obrigatória — tabela com cada operação administrativa, a proteção atual e a proteção que a Fase 3 aplicará. Se não houver nenhuma, escreva "Nenhuma operação administrativa".
- **Proposed Contract Changes:** liste cada rota que passará a exigir credencial (e qual). Toda recomendação de AP-04/AP-12 deve corresponder a um item aqui.
- Mínimo esperado: ≥ 5 findings com pelo menos 1 CRITICAL ou HIGH (se o projeto realmente tiver menos problemas, explique).

## Estrutura

```markdown
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <nome do diretório>
Stack:   <Linguagem> + <Framework> <versão>
Files:   <n> analyzed | ~<loc> lines of code
Date:    <AAAA-MM-DD>

## Summary
CRITICAL: <n> | HIGH: <n> | MEDIUM: <n> | LOW: <n>

| # | Severity | Anti-pattern | Location |
|---|----------|--------------|----------|
| 1 | CRITICAL | <nome> (AP-xx) | <arquivo:linhas> |
| ... | | | |

## Findings

### #1 [CRITICAL] <Nome do anti-pattern> (AP-xx)
File: <arquivo:linhas>
Description: <o que foi encontrado, com evidência>
Impact: <consequência>
Recommendation: <ação concreta> — Playbook T-xx

### #2 [CRITICAL] ...

## Deprecated APIs
| Location | Deprecated usage | Modern replacement |
|----------|------------------|--------------------|
| <arquivo:linha> | <api> | <substituto> |

## Administrative Operations
| Endpoint | Operação | Proteção atual | Proteção após Fase 3 |
|----------|----------|----------------|----------------------|
| <método rota> | <o que faz> | <nenhuma / token não verificado / ...> | <Bearer + admin / X-Admin-Token / dono ou admin> |

## Architecture Overview
Current: <classificação da Fase 1 + principais violações de camadas>
Target:  <estrutura MVC proposta em 1–3 linhas (pastas principais)>

## Proposed Contract Changes
<mudanças de contrato que a Fase 3 fará por segurança (ex.: remover endpoint de SQL arbitrário, retirar `password` das respostas) — ou "None">

================================
Total: <n> findings
================================
```

Logo após o relatório, imprima a pergunta de confirmação definida no `SKILL.md`.

## Exemplo de finding bem escrito

```markdown
### #3 [CRITICAL] SQL Injection (AP-02)
File: models.py:28, 48-49, 57-60, 68, 92, 109-111, 126-128
Description: Queries montadas por concatenação de strings com valores vindos do request (`"... WHERE email = '" + email + "' AND senha = '" + senha + "'"`).
Impact: Bypass de login com `' OR '1'='1`, leitura e destruição arbitrária de dados.
Recommendation: Usar queries parametrizadas com placeholders (`?`) em todas as consultas — Playbook T-02.
```

## Exemplo de finding mal escrito (não faça)

```markdown
### [HIGH] Código ruim
File: models.py
Description: O código tem vários problemas.
```
(Sem linha, sem anti-pattern identificado, sem impacto, sem recomendação acionável.)
