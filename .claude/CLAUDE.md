# MazyOS (plugin)

Este repositório é o plugin (mod) MazyOS do Claude Code, não um workspace de
negócio. Estrutura:

- `.claude-plugin/` — manifesto do plugin e marketplace (o repositório é os dois)
- `hooks/` — módulo de hooks em TypeScript: `register.tsx` (hooks), `memoria.ts`
  (leitura do workspace), `sistema.ts` (as regras que vão pro system prompt)
- `types/index.d.ts` — contrato do estado em `$.state`
- `tests/` — testes do mod (`claude plugin test .`)
- `skills/` — as skills do MazyOS, invocadas como `/mazyos:<nome>`
- `templates/` — perfis de CLAUDE.md, catálogos e o esqueleto do workspace
  (`templates/workspace/`, copiado pela skill `/mazyos:instalar`)

Regras ao mexer aqui:

- As regras de operação do MazyOS vivem em `hooks/sistema.ts`, não num
  CLAUDE.md: um plugin não carrega CLAUDE.md.
- Caminhos dentro de skills usam `${CLAUDE_PLUGIN_ROOT}` (raiz do plugin) e
  `${CLAUDE_SKILL_DIR}` (pasta da skill). Nunca `.claude/skills/...`.
- Mudou os campos de `MazyosWorkspace`? Troque a tag `shape` do atom em
  `hooks/register.tsx`.
- Antes de commitar: `claude plugin validate .` e `claude plugin test .`.
- Pra experimentar numa pasta de negócio: `claude --plugin-dir <este repo>`.
