---
id: como-pensar.atencao-do-transformer
nome: Atenção do Transformer e Estrutura da Skill
tipo: mecanismo
camada: 3-epistemológica
status: ativo

essencia: >
  Posição em U, marcadores, formatos aprendidos, estado inicial e rótulos
  epistêmicos governam o peso de cada parte da skill; estrutura que explora
  esses vieses amplifica o conteúdo.

em-uma-palavra: Atenção

certeza: consensual
maturidade: em-evolução
origem: empírica
---
# Atenção do Transformer e Estrutura da Skill

> O executor-alvo lê a skill através de um mecanismo de atenção com vieses previsíveis. Cinco deles governam as decisões estruturais: a curva em U da posição, os marcadores como âncoras, os formatos já aprendidos no treinamento, o estado inicial que colore o resto e os rótulos que calibram o peso epistêmico. Estrutura que explora esses vieses amplifica o conteúdo; estrutura que os ignora o dilui.

---

## O princípio

Decisões estruturais numa skill não são estéticas. O executor-alvo é um transformer, e a forma como um transformer distribui atenção sobre o contexto determina quais partes da skill de fato moldam o raciocínio e quais passam quase despercebidas. Posição, marcação, formato e rotulagem são, portanto, alavancas de engenharia — mecânicas, previsíveis e exploráveis, desde que usadas de propósito.

Os cinco mecanismos abaixo têm graus de evidência diferentes, e cada seção diz qual é o seu. As consequências de projeto se sustentam em todos os casos: mesmo onde o circuito interno é menos conhecido que o efeito, o efeito é o que importa para a construção.

---

## Mecanismo 1 — Atenção posicional em U

Em contextos longos, a informação no começo e no fim recebe mais atenção que a do meio. O fenômeno, conhecido como *lost in the middle*, é documentado empiricamente; modelos de contexto longo o atenuam, sem eliminá-lo.

A consequência opera em três escalas:

- **Na sessão.** O `SKILL.md` entra no contexto quando a skill é ativada e fica ali; à medida que a conversa cresce, ele vai sendo empurrado para o meio. O núcleo que precisa continuar valendo no fim de uma sessão longa — identidade, axiomas, critérios de término — tem de ser curto e forte o bastante para continuar colorindo o raciocínio, e por isso mora no `SKILL.md`, não apenas num documento lido uma vez.
- **Na skill.** O topo do `SKILL.md` (identidade e axiomas) e o seu fim (o teste final) são posições premium. O meio é lugar do que o agente consulta: a sequência de trabalho e o mapa dos documentos.
- **No documento.** O frontmatter e a essência ocupam o topo; a Rede Sináptica ocupa o fim, que é onde o agente decide para onde ir em seguida. Cabeçalhos quebram o meio em trechos ancorados.

Daí uma regra simples: a informação crítica nunca fica no meio de um parágrafo longo, no meio de um documento longo. Documento que cresce além do seu escopo se divide; documento longo dentro do escopo se ancora com cabeçalhos.

## Mecanismo 2 — Marcadores estruturais como âncoras

Tokens como `##`, negrito, crase de código, marcadores de lista e chaves de YAML funcionam como sinais aprendidos de densidade informacional, e o conteúdo logo após eles tende a receber mais peso. O efeito é consistente com o comportamento observado de modelos diante de texto estruturado; o mecanismo interno é menos estabelecido que o efeito.

A consequência é usar marcadores para o que precisa ser recuperado. Cabeçalhos semânticos, que nomeiam o conteúdo ("Quando o movimento termina"), e não decorativos ("Detalhes"). Rótulos tipados nas conexões — `complementa` **forte** — em vez de links nus. Negrito reservado ao termo ou à regra que o agente precisa encontrar de novo; quando tudo está em negrito, nada está.

## Mecanismo 3 — Padrões aprendidos no treinamento

Modelos foram treinados em volumes enormes de formatos específicos: frontmatter YAML (Jekyll, Hugo, Obsidian, MkDocs), markdown estruturado, ontologias formais (RDF, OWL, schema.org), relações tipadas em documentação técnica, grafos de conhecimento. Um formato familiar é processado com competência pré-existente; um formato inventado precisa ser aprendido durante a inferência e consome a atenção que deveria ir para o conteúdo. A familiaridade de formato com o desempenho é amplamente observada.

As consequências: metadados em frontmatter YAML; organização em markdown com cabeçalhos; predicados de relação parecidos com os de ontologias (`é-caso-especial-de`, `é-pré-requisito-de`, `complementa`); nenhuma notação idiossincrática — símbolos próprios, códigos de emoji, abreviações privadas.

O mesmo mecanismo tem um corolário que costuma passar despercebido: **forma sinaliza gênero, e gênero sinaliza como pesar o conteúdo.** Um documento com cara de changelog é lido como história. Uma tabela de antes e depois é lida como guia de migração, que pressupõe um estado anterior ainda vigente em algum lugar. Um texto com cara de RFC é lido como proposta. Antes de escolher o formato de um documento, pergunte que gênero ele evoca — porque o executor-alvo vai lê-lo segundo esse gênero.

## Mecanismo 4 — Estado latente inicial e coloração

Um transformer processa cada token à luz de todos os anteriores. O que vem primeiro enquadra a interpretação de tudo o que vem depois. A direção do efeito decorre da própria arquitetura autorregressiva; a magnitude é empírica.

A essência no topo de cada documento, por isso, não é redundante com a prosa que segue: ela cria um enquadramento prévio que colore a leitura inteira. Quando o agente lê primeiro que "a escrita canônica declara o estado final como única verdade", ele lê o resto do documento carregando esse quadro; sem a essência, precisa derivá-lo da prosa, o que é mais lento e mais sujeito a desvio. O mesmo vale nas outras escalas: as primeiras linhas do `SKILL.md` — a identidade que o agente assume — colorem a interpretação de cada instrução posterior, e a `description` enquadra a própria decisão de ativar a skill.

## Mecanismo 5 — Calibração epistêmica por metadado explícito

Modelos treinados em corpus técnico aprenderam a pesar afirmações conforme o status declarado delas: uma lei com evidência estabelecida é tratada como fato; uma heurística experimental, com cautela. Declarar `tipo` e `certeza` em cada documento permite ao agente aplicar fundamentos com firmeza e heurísticas com julgamento. Sem esses rótulos, tudo é lido com o mesmo peso — e então uma regra prática vira lei, ou um fundamento vira sugestão. O efeito é plausível e consistente com o modo como modelos tratam texto assertivo e texto qualificado; como o custo é de dois campos por documento, a escolha de projeto se sustenta mesmo sob essa incerteza. Ela é decisiva em skills que misturam princípios universais com regras contextuais.

---

## Como os mecanismos se combinam

| Elemento estrutural | Mecanismos que explora |
|---|---|
| `description` da skill | 1 (presente em toda sessão), 3 (forma de resumo funcional), 4 (enquadra a ativação) |
| Identidade no topo do `SKILL.md` | 1, 4 |
| Frontmatter com essência | 1, 3, 4, 5 |
| `tipo` e `certeza` | 3, 5 |
| Cabeçalhos semânticos | 2 |
| Rede Sináptica tipada no fim | 1 (recência), 2, 3 |
| Teste final no fim do `SKILL.md` | 1 (recência) |

---

## O que fazer

Antes de posicionar qualquer elemento estrutural, faça quatro perguntas. Ele vai ocupar uma posição premium? Usa um padrão que o modelo já conhece? Cria uma âncora útil? Calibra o peso de alguma afirmação? Se todas as respostas forem não, o elemento é ornamental e sai. A pergunta inversa vale para o conteúdo: a regra mais importante deste documento está numa posição premium? Se não está, mova-a.

---

## Tensões e limites

**Os mecanismos são razões de projeto, não dogmas.** Modelos mudam, e a intensidade de cada viés muda com eles. O que confirma uma decisão estrutural é o comportamento de um agente que carregou a skill, não a teoria que a motivou.

**Estrutura tem retorno decrescente.** A primeira camada de frontmatter traz ganho grande de atenção; cada campo a mais custa tokens e rende menos. A inflação estrutural é o modo de falha simétrico à estrutura ausente.

**Posição não resgata conteúdo fraco.** Um princípio mal formulado no topo do documento continua mal formulado — apenas com mais influência.

---

## Rede Sináptica

### Estruturais
- **Pai:** [Contexto de Execução e Axiomas](../contexto-de-execucao.md) — Axioma 6
- **Irmãos:** [Skill Como Substrato Cognitivo](substrato-cognitivo.md), [Níveis de Profundidade Cognitiva](niveis-de-profundidade-cognitiva.md), [Refundamentação Pelo Executor](refundamentacao-pelo-executor.md)

### Semânticas
- `é-caso-especial-de` **forte** — [Contexto de Execução e Axiomas](../contexto-de-execucao.md): desenvolve o Axioma 6 nos cinco mecanismos
- `complementa` **forte** — [Skill Como Substrato Cognitivo](substrato-cognitivo.md): aquele documento diz o que a skill é; este, como a atenção a lê
- `é-pré-requisito-de` **forte** — [Anatomia do Documento](../como-construir/anatomia-do-documento.md): a anatomia põe cada parte onde os mecanismos lhe dão mais peso
- `é-pré-requisito-de` **moderada** — [Rede Sináptica](../como-construir/rede-sinaptica.md): rótulos tipados, predicados conhecidos e posição final são os mecanismos 1, 2 e 3 aplicados às conexões
- `é-análogo-a` **moderada** — [Formato Agent Skills](../referencia/formato-agent-skills.md): a divulgação progressiva aplica aos arquivos a economia que a atenção aplica ao contexto

### Funcionais
- `contextualiza` **moderada** — [Os Sete Movimentos](../como-executar/sete-movimentos.md): dá a razão do Movimento 6 e de cada posição escolhida nele

### Tensões
- Exploração da atenção e inflação estrutural — cada elemento que explora um viés também custa atenção; o controle está em [Anatomia do Documento](../como-construir/anatomia-do-documento.md)
