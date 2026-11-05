---
id: como-construir.anatomia-do-documento
nome: Anatomia do Documento
tipo: padrão
camada: 7-prática
status: ativo

essencia: >
  Frontmatter enxuto com identidade, essência e calibração no topo; prosa que
  declara, explica, mostra e prescreve; Rede Sináptica no fim. Nada entra que não
  mude o raciocínio do agente.

em-uma-palavra: Forma

certeza: consensual
maturidade: consolidado
origem: derivada
---
# Anatomia do Documento

> Cada documento da skill tem uma anatomia fixa: frontmatter enxuto no topo, com identidade, essência e calibração epistêmica; prosa que declara, explica, mostra e prescreve; Rede Sináptica tipada no fim. Nada entra que não mude o raciocínio do executor-alvo.

---

## O princípio

Se a skill é um sistema operacional, cada documento é um módulo com interface conhecida. A anatomia fixa existe para que o agente saiba, em qualquer documento que abra, onde está a identidade, onde está o núcleo, onde está a aplicação e para onde ir depois — sem gastar atenção descobrindo o formato. A ordem das partes segue a lógica cognitiva da leitura: primeiro localizar, depois entender, depois aplicar, depois conectar.

```
┌─────────────────────────────────────────────┐
│  FRONTMATTER       quem sou, o que sou em   │  topo: posição premium
│                    uma frase, quanto confiar │
├─────────────────────────────────────────────┤
│  TÍTULO + ESSÊNCIA EM DESTAQUE              │
├─────────────────────────────────────────────┤
│  CORPO EM PROSA                             │
│    o que afirma → por que é verdade →       │
│    como aparece → o que fazer → o que muda  │
│    analogias (com onde quebram)             │
│    tensões e limites                        │
├─────────────────────────────────────────────┤
│  REDE SINÁPTICA    pai, irmãos, conexões    │  fim: posição premium
│                    semânticas e funcionais  │
└─────────────────────────────────────────────┘
```

---

## O frontmatter

Dez a quinze linhas de conteúdo, nunca mais de vinte — as linhas em branco que agrupam os campos não contam —, em YAML, um formato que o modelo conhece de sobra. O frontmatter real de [Presença Direta](../como-executar/presenca-direta.md):

```yaml
---
id: como-executar.presenca-direta
nome: Presença Direta
tipo: heurística
camada: 4-operacional
status: ativo

essencia: >
  Durante a construção, só conta como verdade o que foi observado diretamente
  na fonte; todo "provavelmente" sobre o estado de algo é uma verificação que
  ainda não foi feita.

em-uma-palavra: Verificação

certeza: estabelecido
maturidade: consolidado
origem: empírica
---
```

**`id`** espelha o caminho do arquivo dentro da skill: o caminho relativo sem a extensão, com `/` trocado por `.`. É único na skill.

**`nome`** é o nome legível do conceito, com acentos e espaços; o mesmo que aparece no título.

**`tipo`** é o papel do documento — `fundamento`, `mecanismo`, `padrão`, `heurística`, `ferramenta`, `modelo-mental` ou `lei` — e diz ao agente como pesá-lo.

**`camada`** é a posição arquitetural, com número e nome (`2-raiz`, `3-epistemológica`, `4-operacional`, `7-prática`, `8-referência`). Ela torna o gradiente de abstração legível na própria identidade do documento.

**`status`** é `ativo` ou `maduro` em tudo o que é entregue. Um documento em rascunho ou em revisão não pertence à skill entregue; um documento superado não fica marcado como superado — é dissolvido ou removido.

**`essencia`** captura o documento inteiro numa formulação densa, de uma a três linhas. Se o agente ler só a essência, apreende o núcleo; e, como ela vem antes da prosa, enquadra a leitura de todo o resto. Uma essência que parafraseia o título não cumpre a função: ela precisa afirmar algo.

**`em-uma-palavra`** é um exercício de compressão máxima e uma âncora mnemônica.

**`certeza`**, **`maturidade`** e **`origem`** calibram o peso epistêmico, conforme a seção seguinte.

O `SKILL.md` não recebe esses campos: o frontmatter dele segue a especificação do runtime, e campos extras ali, quando necessários, vão dentro de `metadata`.

Logo depois do título vem a essência em destaque: um parágrafo que enuncia a tese inteira do documento, um pouco mais desenvolvida que a `essencia` do frontmatter. É o primeiro trecho que o agente lê como prosa e, junto com a essência comprimida, o enquadramento de tudo o que vem depois.

---

## A calibração epistêmica

| `certeza` | Significado | Postura que instala no agente |
|---|---|---|
| `estabelecido` | Amplamente aceito, vasta evidência | Tratar como fato |
| `consensual` | A maioria das fontes qualificadas concorda | Tratar como provável |
| `debatido` | Há visões concorrentes legítimas | Considerar múltiplas perspectivas |
| `experimental` | Evidência preliminar e promissora | Aplicar com cautela |
| `especulativo` | Hipótese ou extrapolação | Usar só como exploração |

`maturidade` diz quão testado e estável o conhecimento está (`seminal`, `consolidado`, `em-evolução`, `em-revisão`); `origem` diz de onde ele vem (`empírica`, `teórica`, `heurística`, `derivada`). A distribuição precisa fazer sentido: fundamentos com certeza alta; heurísticas com certeza calibrada; nada marcado como `estabelecido` só porque o autor confia nele. A calibração uniforme em todos os documentos é o que impede o agente de tratar uma regra prática como lei.

---

## O corpo em prosa

O corpo cumpre funções numa ordem cognitiva. Os títulos das seções variam com o conteúdo — eles nomeiam o que a seção diz —, mas as funções estão sempre lá.

1. **O que afirma.** O princípio, a definição ou o padrão, declarado no presente.
2. **Por que é verdade.** O mecanismo, a evidência, a derivação a partir da raiz. É a parte que permite ao agente generalizar.
3. **Como aparece.** Os sinais pelos quais o agente reconhece a situação em que o documento se aplica — e as situações parecidas em que ele não se aplica, com o redirecionamento para o documento certo.
4. **O que fazer.** A diretriz, em forma imperativa, escrita para ser usada durante a execução, não durante o estudo.
5. **O que muda.** O contraste entre o comportamento com e sem o princípio, de preferência num exemplo concreto: contexto, conduta sem o conhecimento, conduta com o conhecimento, diferença no resultado.
6. **Analogias.** Imagens de um domínio diferente do da skill, cada uma com a declaração de onde ela quebra. A analogia sem o ponto de quebra ensina o agente a estendê-la além do que ela aguenta.
7. **Tensões e limites.** Onde o princípio falha, entra em conflito com outro ou deixa de valer, e o que usar nesses casos.

A Rede Sináptica fecha o documento.

---

## As anatomias especiais

**O `SKILL.md`.** Frontmatter do runtime (`name`, `description` e os opcionais); identidade que o agente assume ao carregar a skill; quando usar e quando não usar; o apontamento para a raiz, a ser lida primeiro; o núcleo comprimido — axiomas e sequência de trabalho; o mapa de todos os documentos, cada um com uma linha que diz quando consultá-lo; e, no fim, o critério que define o trabalho como pronto. Todo documento da skill é alcançável por um link direto a partir do `SKILL.md`.

**A raiz.** O executor-alvo, com capacidades e limites; a função objetivo; os axiomas numerados; a ordem de decisão; as implicações para os demais documentos. A Rede Sináptica da raiz liga cada axioma ao documento que o desenvolve.

---

## O controle da inflação estrutural

Estrutura é visível e mensurável, e por isso seduz: cada campo acrescentado dá a sensação de progresso. Mas o retorno é decrescente — a primeira camada de frontmatter traz ganho grande de atenção, a décima é custo puro. A pergunta de controle, para cada elemento, é uma só: *se eu remover isto, o raciocínio do executor-alvo piora de forma detectável?* Se não piora, o elemento sai.

Os limites práticos: frontmatter de dez a quinze linhas; um vocabulário de três a cinco relações semânticas e três a cinco papéis funcionais em uso na skill; no máximo três níveis de diretório.

O modo de falha vizinho é a tipologia inconsistente — documentos parecidos com tipos diferentes, ou o mesmo tipo aplicado a naturezas diferentes. Ela torna o `tipo` uma pista ruidosa, e o agente deixa de poder confiar nele. A correção é auditar o frontmatter de todos os documentos lado a lado.

---

## O que muda

| Sem anatomia fixa | Com anatomia fixa |
|---|---|
| O agente gasta atenção descobrindo o formato de cada documento | O agente sabe onde está cada parte antes de abrir o arquivo |
| Lê o documento inteiro para saber se precisava dele | Decide pela essência se precisa do resto |
| Pesa uma heurística e um fundamento da mesma forma | Calibra o peso pelo `tipo` e pela `certeza` |
| Termina a leitura sem saber para onde ir | Segue a Rede Sináptica para o próximo documento |

---

## Analogia

**O formulário padronizado de prontuário.** Num hospital, qualquer médico abre o prontuário de qualquer paciente e encontra a alergia no mesmo lugar, a medicação em uso no mesmo lugar, a evolução no mesmo lugar. A padronização não é burocracia: é o que permite decidir rápido sem deixar passar o crítico. Onde a analogia quebra: o prontuário é preenchido por muitas mãos ao longo do tempo e registra história; um documento de skill é escrito para declarar um estado, e a história fica fora dele.

---

## Rede Sináptica

### Estruturais
- **Pai:** [Contexto de Execução e Axiomas](../contexto-de-execucao.md) — Axiomas 2 e 6
- **Irmãos:** [Arquitetura em Camadas](arquitetura-em-camadas.md), [Rede Sináptica](rede-sinaptica.md), [Da Fonte ao Substrato](da-fonte-ao-substrato.md), [Refatoração de Skills](refatoracao-de-skills.md), [Verificação em Mente Fresca](verificacao-em-mente-fresca.md)

### Semânticas
- `pressupõe` **forte** — [Atenção do Transformer](../como-pensar/atencao-do-transformer.md): cada parte da anatomia ocupa a posição que um mecanismo de atenção valoriza
- `complementa` **forte** — [Arquitetura em Camadas](arquitetura-em-camadas.md): a unidade e o conjunto
- `complementa` **forte** — [Rede Sináptica](rede-sinaptica.md): a rede é a última parte da anatomia de todo documento
- `complementa` **moderada** — [Vocabulário Tipado](../referencia/vocabulario-tipado.md): este documento explica cada campo; aquele lista os valores que cada um admite

### Funcionais
- `habilita` **moderada** — [Verificação em Mente Fresca](verificacao-em-mente-fresca.md): a anatomia fixa é o que torna cada documento auditável por script

### Tensões
- Estrutura e inflação estrutural — a pergunta de controle decide cada campo: removê-lo piora o raciocínio do executor-alvo?
