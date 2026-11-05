---
name: publicar-tema
description: >
  Orquestra a criação completa de uma peça de conteúdo SEO + redes sociais a partir de um tema.
  Pega um tema (manual ou da estratégia de conteúdo do SEO), escreve o artigo de blog completo,
  gera o carrossel resumo via skill /mazyos:carrossel, e produz as legendas pra Instagram, Facebook e
  LinkedIn — tudo amarrado, com o carrossel apontando pro blog.
  Use quando o usuário pedir "publicar tema", "gera o conteúdo do tema X", "transforma esse tema
  em post", "cria o conteúdo completo", ou /mazyos:publicar-tema.
---

# /mazyos:publicar-tema — Pipeline de conteúdo SEO + redes sociais

Skill orquestradora. Pega um tema → entrega artigo no blog + carrossel + 3 legendas (Insta, FB, LinkedIn), tudo conectado.

## Dependências

- **Estratégia de conteúdo:** `marketing/seo/05-estrategia-conteudo.md` (lista mestra de temas, criada pelo `/mazyos:seo`)
- **Outras pesquisas SEO:** `marketing/seo/01-pesquisa-demanda.md`, `02-analise-concorrencia.md`, `08-geo-otimizacao-ia.md`
- **Skill carrossel:** `${CLAUDE_PLUGIN_ROOT}/skills/carrossel/SKILL.md` (a skill `/mazyos:carrossel`) — usar pra fase do carrossel
- **Site (blog):** `site/` — destino dos artigos. Estrutura comum: Astro em `site/astro-site/src/content/blog/`, ou WordPress, ou outro. Se ainda não tiver site, perguntar antes
- **Tom de voz:** `_memoria/preferencias.md`
- **Contexto:** `_memoria/empresa.md`, `identidade/design-guide.md`

---

## Workflow

### Passo 0 — Escolher o tema

Se o usuário passou um tema explícito → usar.

Se não passou nada → ler `marketing/seo/05-estrategia-conteudo.md`, listar os artigos satélite + a página pilar, e perguntar:

> "Qual tema da estratégia? (lista de opções)"

Marcar mentalmente quais já viraram blog (checar pasta do blog) pra não duplicar.

### Passo 1 — Pesquisa rápida

Antes de escrever, ler o que tem nas pesquisas SEO sobre esse tema:
- Keyword principal e variações (`01-pesquisa-demanda.md`)
- Como concorrentes tratam (`02-analise-concorrencia.md`) — pra fugir do óbvio
- Ângulo GEO se aplicável (`08-geo-otimizacao-ia.md`) — perguntas que IAs respondem

### Passo 2 — Escrever o blog post

**Destino:** depende do stack do site. Padrões comuns:
- Astro: `site/astro-site/src/content/blog/<slug>.md`
- WordPress: gerar markdown que o usuário cola no editor
- Outro: confirmar com o usuário

**Slug:** kebab-case curto, sem stopwords. Ex: "Como conservar carne salgada no restaurante" → `conservar-carne-salgada`.

**Frontmatter (se o stack usa markdown com frontmatter):**

```yaml
---
title: "Título atrativo, próximo da keyword"
description: "Meta description 150-160 caracteres, com keyword e benefício pro leitor"
publishedAt: YYYY-MM-DD
author: "<nome configurado em _memoria/empresa.md>"
keywords:
  - keyword principal
  - variação 1
  - variação 2
draft: true
---
```

**Sempre começar com `draft: true`.** O usuário revisa e flipa pra `false` quando aprovar.

**Estrutura do artigo (800-1500 palavras):**

1. **Lead (1-2 parágrafos):** problema concreto do público, sem enrolação
2. **H2 explicativo:** o quê e por quê
3. **H2 prático:** como fazer / o que olhar
4. **H2 comparativo ou de detalhe técnico** (opcional)
5. **H2 onde a empresa se encaixa:** conexão natural com o produto, sem ser propaganda
6. **CTA final:** link WhatsApp / formulário / contato configurado

**Regras de escrita** (seguir `_memoria/preferencias.md` estritamente):
- Sem jargão de marketing/inglês quando o público não usa
- Frases curtas, parágrafos de 2-4 linhas
- Concreto: números, certificações, datas, valores quando souber
- Markdown limpo: `##` pra H2, `###` pra H3, listas com `-`, links em `[texto](url)`

### Passo 3 — Carrossel resumo

**Sem perguntar, partir direto pra criação do carrossel** chamando `${CLAUDE_PLUGIN_ROOT}/skills/carrossel/SKILL.md` (a skill `/mazyos:carrossel`) (tipo 1: carrossel texto puro).

**Pasta:** `marketing/conteudo/<slug-do-blog>-<YYYY-MM-DD>/`

Estrutura de slides do resumo:
- **Slide 1 — capa:** mesmo título do blog (ou variação enxuta)
- **Slides 2-6:** os pontos-chave do blog (1 ideia por slide, frase natural, não bullet seco)
- **Slide final — CTA pro blog:** "Texto completo no nosso blog" + URL `<dominio>/blog/<slug>`

**Capa:** seguir sequência alternada do feed (claro → foto/escuro → cor principal → repete) — checar `marketing/conteudo/` mais recente.

### Passo 4 — Legendas (3 versões)

Salvar todas em `marketing/conteudo/<pasta-do-carrossel>/`:

**`legenda.md`** (Instagram + Facebook — mesmo texto):
- Hook na primeira linha
- 2-3 parágrafos de contexto (frases naturais, sem corporativês)
- CTA pro carrossel ("Arraste pro lado") + CTA pro blog ("Texto completo no link da bio" ou URL direta)
- Bloco oferta da empresa (diferenciais, contato)
- 10-15 hashtags (público + nicho + local)

**`legenda-linkedin.md`** (LinkedIn — mais formal, sem hashtags):
- Hook (pode ser provocativo, profissional)
- 3-5 parágrafos analíticos — LinkedIn aceita texto longo
- Sem "arraste pro lado" (público diferente, comportamento diferente)
- CTA: link direto pro blog
- Sem bloco de oferta agressivo — fechar com 1 linha de quem é a empresa
- Máx 3 hashtags no final, do nicho profissional

### Passo 5 — Resumo de entrega

No fim, mostrar pro usuário uma lista clara:

```
✓ Blog post: <caminho>/<slug>.md (draft)
✓ Carrossel: marketing/conteudo/<pasta>/
  - carrossel.html + render.js
  - PNGs em instagram/
✓ Legendas:
  - legenda.md (Insta + FB)
  - legenda-linkedin.md

Pra publicar:
1. Revisar o blog → flipar draft: false
2. Rebuild do site (se Astro/Hugo/etc) ou copiar pro CMS
3. Renderizar PNGs do carrossel: cd marketing/conteudo/<pasta> && node render.js
4. Postar carrossel no Insta + FB com legenda.md (ou usar /mazyos:aprovar-post)
5. Postar texto + link no LinkedIn com legenda-linkedin.md
```

---

## Quando NÃO usar essa skill

- Pedido de carrossel avulso (sem blog) → usar `/mazyos:carrossel` direto
- Atualização de artigo existente → editar direto o .md
- Post único, frase de impacto → `/mazyos:carrossel`

## Princípios

1. **Blog é a peça-mãe.** Carrossel e legendas são derivados dele, não o contrário.
2. **Tudo conectado.** Cada peça referencia a outra (carrossel linka pro blog, blog tem CTA pro contato).
3. **Draft sempre.** Nunca publicar automaticamente — usuário revisa antes (ou usa `/mazyos:aprovar-post`).
4. **Linguagem do público real.** Sem corporativês. Sempre.
