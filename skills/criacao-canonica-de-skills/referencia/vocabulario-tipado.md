---
id: referencia.vocabulario-tipado
nome: Vocabulário Tipado
tipo: ferramenta
camada: 8-referência
status: ativo

essencia: >
  Os rótulos fechados da skill — camadas, tipos, status, calibração, forças,
  relações com inversas e papéis funcionais —, com significado operacional e
  equivalente em inglês.

em-uma-palavra: Rótulos

certeza: estabelecido
maturidade: consolidado
origem: derivada
---
# Vocabulário Tipado

> Os rótulos fechados da skill — camadas, tipos, status, certeza, maturidade, origem, forças, relações semânticas com as suas inversas e papéis funcionais —, cada um com o significado operacional e o equivalente em inglês. É exatamente o vocabulário que a auditoria mecânica reconhece.

A forma canônica é a primeira coluna. Skills escritas em inglês usam a coluna em inglês, sem misturar as duas línguas na mesma skill. A auditoria aceita também as grafias sem acento, mas a forma canônica é a acentuada.

---

## Chaves do frontmatter dos documentos

| Chave | Em inglês | Conteúdo |
|---|---|---|
| `id` | `id` | Caminho relativo do arquivo sem extensão, com `/` trocado por `.` |
| `nome` | `name` | Nome legível do conceito |
| `tipo` | `type` | Papel do documento |
| `camada` | `layer` | Posição arquitetural, com número |
| `status` | `status` | Estado no ciclo de vida |
| `essencia` | `essence` | O documento inteiro em uma a três linhas |
| `em-uma-palavra` | `in-one-word` | Âncora mnemônica |
| `certeza` | `certainty` | Força da evidência |
| `maturidade` | `maturity` | Grau de teste e estabilidade |
| `origem` | `origin` | De onde o conhecimento vem |

---

## Camadas

| Valor | Em inglês | Função |
|---|---|---|
| `1-entrada` | `1-entry` | Ponto de carregamento; é o `SKILL.md`, que não recebe frontmatter canônico |
| `2-raiz` | `2-root` | Executor-alvo, objetivo, axiomas |
| `3-epistemológica` | `3-epistemic` | Como pensar |
| `4-operacional` | `4-operational` | Como executar |
| `5-contratos` | `5-contracts` | Como passar trabalho entre componentes |
| `6-meta-engenharia` | `6-meta-engineering` | Como projetar o sistema que faz o trabalho |
| `7-prática` | `7-practice` | Como aplicar no domínio |
| `8-referência` | `8-reference` | O que consultar durante a execução |

A auditoria lê o número; o nome depois do hífen existe para o agente.

---

## Tipos de documento

| Valor | Em inglês | Natureza |
|---|---|---|
| `fundamento` | `foundation` | Verdade irredutível dentro da skill |
| `mecanismo` | `mechanism` | Processo causal: como algo funciona |
| `padrão` | `pattern` | Estrutura recorrente e reconhecível |
| `heurística` | `heuristic` | Regra prática com exceções; exige calibração |
| `ferramenta` | `tool` | Instrumento aplicável com entrada e saída claras |
| `modelo-mental` | `mental-model` | Lente que muda como a situação é vista |
| `lei` | `law` | Relação formal e testável entre variáveis |

---

## Status

| Valor | Em inglês | Numa skill entregue |
|---|---|---|
| `ativo` | `active` | Sim |
| `maduro` | `mature` | Sim — validado por uso real |
| `rascunho` | `draft` | Não: o documento ainda não pertence à skill |
| `em-revisão` | `under-review` | Não: a revisão termina antes da entrega |
| `depreciado` | `deprecated` | Nunca: o documento é dissolvido ou removido |
| `fundido` | `merged` | Nunca: o conteúdo já vive em outro documento |

---

## Calibração epistêmica

| `certeza` | Em inglês | Postura do agente |
|---|---|---|
| `estabelecido` | `established` | Tratar como fato |
| `consensual` | `consensus` | Tratar como provável |
| `debatido` | `debated` | Considerar múltiplas perspectivas |
| `experimental` | `experimental` | Aplicar com cautela |
| `especulativo` | `speculative` | Usar só como exploração |

| `maturidade` | Em inglês | Significado |
|---|---|---|
| `seminal` | `seminal` | Formulação inicial, pouco testada |
| `consolidado` | `consolidated` | Testado e estável |
| `em-evolução` | `evolving` | Válido, num campo que muda |
| `em-revisão` | `under-revision` | O próprio conhecimento está sendo reavaliado |

| `origem` | Em inglês | Significado |
|---|---|---|
| `empírica` | `empirical` | Observação e experiência |
| `teórica` | `theoretical` | Dedução a partir de teoria |
| `heurística` | `heuristic` | Regra prática consagrada pelo uso |
| `derivada` | `derived` | Derivação a partir de outros conhecimentos da skill |

---

## Força das conexões

| Valor | Em inglês | Comportamento esperado |
|---|---|---|
| `forte` | `strong` | Ativar sempre junto |
| `moderada` | `moderate` | Ativar quando o contexto sugerir |
| `sutil` | `subtle` | Ativar só em exploração profunda |

---

## Relações semânticas

São recíprocas: o documento de destino registra a relação na coluna "recíproca".

| Relação | Em inglês | Recíproca | Recíproca em inglês |
|---|---|---|---|
| `complementa` | `complements` | `complementa` | `complements` |
| `contrasta-com` | `contrasts-with` | `contrasta-com` | `contrasts-with` |
| `é-análogo-a` | `is-analogous-to` | `é-análogo-a` | `is-analogous-to` |
| `é-caso-especial-de` | `is-special-case-of` | `é-generalização-de` | `is-generalization-of` |
| `é-pré-requisito-de` | `is-prerequisite-of` | `pressupõe` | `presupposes` |
| `evolui-para` | `evolves-into` | `é-evolução-de` | `evolves-from` |

---

## Papéis funcionais

São direcionais: cada direção é registrada só se valer por conta própria.

| Papel | Em inglês | Significado |
|---|---|---|
| `habilita` | `enables` | Torna o outro possível |
| `restringe` | `constrains` | Limita o outro |
| `valida` | `validates` | Serve para verificar o outro |
| `amplifica` | `amplifies` | Potencializa o efeito do outro |
| `mitiga` | `mitigates` | Reduz os riscos do outro |
| `contextualiza` | `contextualizes` | Dá significado ao outro |

---

## Cabeçalhos da Rede Sináptica

| Português | Inglês |
|---|---|
| `## Rede Sináptica` | `## Synaptic Network` |
| `### Estruturais` | `### Structural` |
| `### Semânticas` | `### Semantic` |
| `### Funcionais` | `### Functional` |
| `### Tensões` | `### Tensions` |
| `**Pai:**`, `**Irmãos:**`, `**Filhos:**` | `**Parent:**`, `**Siblings:**`, `**Children:**` |

---

## Rede Sináptica

### Estruturais
- **Pai:** [Contexto de Execução e Axiomas](../contexto-de-execucao.md) — Axioma 6
- **Irmãos:** [Formato Agent Skills](formato-agent-skills.md)

### Semânticas
- `complementa` **forte** — [Rede Sináptica](../como-construir/rede-sinaptica.md): aquele documento explica o uso das relações; este fecha os rótulos e as inversas
- `complementa` **moderada** — [Anatomia do Documento](../como-construir/anatomia-do-documento.md): a anatomia explica cada campo; este documento lista os valores que cada um admite

### Funcionais
- `habilita` **moderada** — [Verificação em Mente Fresca](../como-construir/verificacao-em-mente-fresca.md): a auditoria mecânica reconhece exatamente estes rótulos
