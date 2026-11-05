---
name: relatorio-ads
description: >
  Gera relatório semanal de performance de anúncios pagos (Google Ads + Meta Ads). Lê CSVs
  exportados das plataformas (ou prints) e devolve análise executiva com KPIs, top criativos,
  alertas (queima de orçamento, CTR baixo, conversões caindo) e recomendações práticas pra
  semana seguinte.
  Use quando o usuário pedir "relatório de ads", "relatório de campanha", "como foram os ads",
  "performance da semana", "relatorio meta", "relatorio google ads", ou /mazyos:relatorio-ads.
---

# /mazyos:relatorio-ads — Relatório semanal de Google Ads + Meta Ads

Skill que transforma exports brutos das plataformas em relatório executivo que o dono entende sem precisar abrir a interface do Google ou da Meta.

## Dependências

- **Contexto:** `_memoria/empresa.md`, `_memoria/estrategia.md`
- **Tom de voz:** `_memoria/preferencias.md`
- **Inputs:** CSVs do Google Ads e/ou Meta Ads Manager. Print também aceito (transcrever)
- **Histórico:** `marketing/campanhas/relatorios/` (criar se não existir)

---

## Como rodar

Usuário roda o comando e cola/aponta os arquivos:

```
/mazyos:relatorio-ads
dados/google-ads-2026-05-12.csv
dados/meta-ads-2026-05-12.csv
```

Ou simplesmente:

```
/mazyos:relatorio-ads
```

Aí a skill pergunta onde estão os exports da semana.

## Workflow

### Passo 1 — Ler os exports

**Google Ads:** colunas mínimas esperadas — Campanha, Grupo, Impressões, Cliques, CTR, CPC médio, Custo, Conversões, CPA, Conv. rate.

**Meta Ads:** colunas mínimas esperadas — Campanha, Conjunto, Impressões, Alcance, Cliques no link, CTR, CPM, Frequência, Custo, Resultados, Custo por resultado.

Se faltar coluna crítica (Conversões / Resultados), avisar e seguir só com tráfego.

### Passo 2 — Comparar com a semana anterior

Buscar em `marketing/campanhas/relatorios/` o relatório anterior. Se existir, calcular variação semana vs semana:

- Investimento total
- Cliques / Impressões
- CTR (clique / impressão)
- CPC / CPM
- Conversões totais (Google + Meta)
- CPA (custo / conversão)
- Custo por canal

Se não existir, é a primeira leitura — sinalizar como baseline.

### Passo 3 — Resumo executivo (topo do relatório)

Uma página, leitura de 2 minutos. Estrutura:

```markdown
# Relatório de Ads — semana <DD/MM> a <DD/MM>

## Resumo executivo

**Investimento:** R$ X.XXX (▼/▲ Y% vs semana anterior)
**Conversões:** N (▼/▲ Y%)
**CPA médio:** R$ X.XX (▼/▲ Y%)

**Canais:**
- Google Ads: R$ X.XXX → N conversões (CPA R$ X.XX)
- Meta Ads:   R$ X.XXX → N conversões (CPA R$ X.XX)

**Headline da semana:** 1 frase do que mais importa (campanha que estourou, criativo que matou,
alerta de orçamento, queda inesperada).
```

### Passo 4 — Detalhamento por canal

Pra cada canal, listar:

**Top 3 campanhas/grupos por performance** (menor CPA, maior conv. rate)
**Bottom 3** (maior CPA, menor conv. rate) — sinalizar pra pausar ou ajustar
**Top criativos** (Meta): impressões + CTR + custo por resultado
**Bottom criativos** (Meta): pra trocar ou pausar
**Palavras-chave com mais custo e zero conversão** (Google) — virar negativas

### Passo 5 — Alertas automáticos

Varrer os dados e gerar alertas em vermelho/amarelo:

| Alerta | Critério |
|---|---|
| 🔴 Queima de orçamento | Campanha gastou >R$X com 0 conversões |
| 🔴 CTR despencou | CTR caiu >30% vs semana anterior |
| 🟡 Frequência alta (Meta) | Conjunto com freq > 3.0 — público saturado |
| 🟡 Conv. rate baixa | <1% em campanha Search |
| 🟡 CPC subindo | CPC médio +20% vs semana anterior |
| 🟢 Oportunidade | Campanha com CTR/conv acima da média + orçamento limitado → considerar aumentar |

### Passo 6 — Recomendações pra semana

Lista curta (3-5 itens) de ações concretas:

```markdown
## Pra fazer na próxima semana

1. **Pausar** Grupo "X" — gastou R$ 230 sem conversão em 7 dias
2. **Adicionar negativas:** [lista de termos que apareceram nos search terms e não convertem]
3. **Trocar criativo Meta** do conjunto "Y" — frequência 4.2, performance caindo
4. **Aumentar orçamento** da campanha "Z" — CPA R$ 12, abaixo do alvo
5. **Testar** novo RSA com headline "<sugestão baseada em concorrência atual>"
```

### Passo 7 — Salvar

```
marketing/campanhas/relatorios/<YYYY-MM-DD>-relatorio.md
```

Frontmatter com:
```yaml
---
periodo_inicio: YYYY-MM-DD
periodo_fim: YYYY-MM-DD
investimento_total: 0000.00
conversoes_total: 0
cpa_medio: 00.00
canais: [google-ads, meta-ads]
---
```

Esse frontmatter facilita comparações futuras com scripts e a leitura de longo prazo.

### Passo 8 — Entrega

Mostrar o resumo executivo direto no chat (Passos 3 + 5 + 6) e apontar pro arquivo completo:

> "Relatório completo em `marketing/campanhas/relatorios/<data>-relatorio.md`. Quer que eu envie por email pro cliente?"

Se sim, chamar `/mazyos:email-profissional` com o resumo executivo + link/anexo.

---

## Regras

- **Nunca inventar números.** Se o export tá truncado ou ilegível, dizer "dados incompletos" e seguir só com o que dá.
- **Comparação é o que importa.** Número solto ("R$ 1.200 essa semana") não significa nada sem o comparativo.
- **Alertas em ordem.** Vermelho primeiro, amarelo depois, verde por último.
- **Recomendações concretas.** "Pausar Grupo X" > "Otimizar campanhas". Nome da campanha, valor, motivo.
- **Linguagem do dono.** Seguir `_memoria/preferencias.md`. CPM, CTR, CPA são OK se o dono já entende; se não, traduzir ("custo por mil pessoas que viram", "% de quem clicou", "quanto custou cada cliente").
- **Frequência boa pra Meta:** 1.5–3.0. Acima de 3.0 já satura. Acima de 4.0 vira ruído.
- **Quando reportar perda:** não amenizar. "A campanha X queimou R$ 200 sem trazer venda" é mais útil que "a campanha X teve performance abaixo do esperado".
