---
name: atualizar
description: >
  Varre o projeto e atualiza os arquivos de contexto (`_memoria/empresa.md`, `preferencias.md`,
  `estrategia.md`, `CLAUDE.md`, `identidade/design-guide.md`) que ficaram desatualizados em relação
  ao estado real do workspace. Use quando o usuário disser "atualiza", "/mazyos:atualizar", "varre o
  projeto", ou pedir uma reconciliação geral.
---

# /mazyos:atualizar — Varredura e atualização de contexto

Compara o que está nos arquivos de contexto com o estado real do workspace e propõe atualizações.

## Workflow

### Passo 1 — Levantamento

Listar:
- Pastas na raiz (cada uma representa uma área de trabalho)
- Subpastas em `clientes/` (se existir) — cada uma é um cliente
- Skills locais em `.claude/skills/` — quais existem hoje (as do MazyOS vêm do plugin e não precisam ser listadas)
- Arquivos recentes (últimos 30 dias) em pastas como `propostas/`, `conteudo/`, `clientes/<x>/`

### Passo 2 — Comparação

Ler os arquivos de contexto e identificar:

- **Em `_memoria/empresa.md`:** lista de clientes / serviços / ferramentas — bate com a realidade do workspace?
- **Em `_memoria/estrategia.md`:** o foco atual ainda faz sentido (datas, prioridades)?
- **Em `CLAUDE.md`:** as regras de organização e a estrutura de pastas listada batem com o que existe?
- **Em `identidade/design-guide.md`:** continua coerente com o que foi gerado nas últimas peças (carrosséis, slides)?

### Passo 3 — Proposta de mudanças

Apresentar pro usuário uma lista curta no formato:

```
Encontrei [N] coisas pra atualizar:

1. _memoria/empresa.md — falta o cliente "Acme" (vi pasta clientes/Acme/ criada em [data])
2. CLAUDE.md — tem regra "propostas vão em propostas/" mas vejo propostas em clientes/<x>/propostas/
3. _memoria/estrategia.md — fala em "fechar 1º cliente em fevereiro", já é abril e tem 3 clientes ativos

Quer que eu aplique essas mudanças? Posso aplicar todas, escolher algumas, ou nenhuma.
```

### Passo 4 — Aplicação

Se o usuário aprovar, editar os arquivos com cirurgia — só a linha relevante, sem reformatar o documento todo. Mostrar o diff de cada mudança aplicada.

## Regras

- Não inventar fatos — só registrar o que tem evidência no workspace
- Se a evidência for ambígua (ex: pasta vazia chamada "Cliente Novo"), perguntar antes de adicionar
- Não apagar conteúdo dos arquivos de contexto — só atualizar e adicionar
- Se nenhuma mudança for necessária, responder "Tá tudo coerente, nada pra atualizar"
