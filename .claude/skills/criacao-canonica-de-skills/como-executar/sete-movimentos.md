---
id: como-executar.sete-movimentos
nome: Os Sete Movimentos da Construção Canônica
tipo: mecanismo
camada: 4-operacional
status: ativo

essencia: >
  Imersão, meta-cognição, raiz, reconstrução, integração tipada, arquitetura de
  atenção e mente fresca, em ordem causal; cada movimento termina num critério
  verificável e é pré-requisito do seguinte.

em-uma-palavra: Sequência

certeza: estabelecido
maturidade: consolidado
origem: empírica
---
# Os Sete Movimentos da Construção Canônica

> A construção canônica acontece em sete movimentos de ordem causal: imersão, meta-cognição, raiz, reconstrução, integração tipada, arquitetura de atenção e mente fresca. Cada movimento tem um critério de término verificável e é pré-requisito do seguinte. Pular um deles produz um resultado hierarquicamente inferior, por mais polido que pareça.

---

## A ordem é causal

Cada movimento produz o que o seguinte consome. A imersão põe no seu contexto o material que a meta-cognição interroga. A meta-cognição produz a intenção declarada que a raiz formaliza. A raiz fixa os axiomas dos quais o conteúdo deriva. O conteúdo em Nível 3 é o que as conexões tipadas conectam. Conteúdo e conexões são o que a arquitetura de atenção posiciona. E só um artefato completo pode ser verificado por uma mente fresca.

Duas travas não se negociam:

- **Nenhum documento é escrito antes da raiz.** O Movimento 4 não começa enquanto o Movimento 3 não declarou o executor-alvo e os axiomas.
- **Nenhuma estrutura é polida antes do conteúdo.** Os Movimentos 5 e 6 não começam enquanto o Movimento 4 não estiver completo em todos os documentos relevantes.

A mesma sequência serve para criar uma skill e para refatorar uma existente. O que muda é o material do Movimento 1 e a forma do Movimento 4 — os dois caminhos estão detalhados em [Da Fonte ao Substrato](../como-construir/da-fonte-ao-substrato.md) e em [Refatoração de Skills](../como-construir/refatoracao-de-skills.md).

---

## Movimento 1 — Imersão total

**O que fazer.** Ler integralmente, no seu próprio contexto, todo o material relevante. Numa criação, o corpo de conhecimento de origem inteiro: os frameworks, as notas, os prompts existentes, as mensagens em que o usuário expressou a intenção, os conceitos correlatos em outras bases. Numa refatoração, todos os documentos atuais da skill, as falhas observadas no comportamento do agente e as correções que o usuário fez. Nos dois casos, o histórico de sessões anteriores sobre o tema, quando existir. Ler integralmente significa abrir o arquivo inteiro e lê-lo; uma busca localiza, não absorve.

Quando o volume excede a janela, leia em lotes sequenciais e, ao fim de cada lote, registre o argumento central de cada peça lida e as conexões entre elas. Esse registro serve para navegar e para testar a imersão. Na hora de escrever um documento, a fonte daquele documento é relida — não o registro.

**Por que.** Meta-cognição não opera sobre resumos. A qualidade da reconstrução é limitada pelo material que você mantém no contexto ao mesmo tempo, e a leitura delegada é a forma mais comum de cegueira estrutural na construção de skills.

**Quando termina.** Quando você consegue articular, sem reabrir nenhum arquivo, o argumento central de cada peça do material e como as peças se conectam — inclusive onde elas se contradizem. Se precisa voltar à fonte para lembrar o que algo diz, a imersão não terminou.

**Sinal de que foi pulado.** A skill reproduz a estrutura de capítulos da fonte; contradições entre fontes passam despercebidas; o mesmo conceito aparece com nomes diferentes em documentos diferentes.

---

## Movimento 2 — Meta-cognição sobre a intenção

**O que fazer.** Antes de escrever qualquer coisa, parar e responder explicitamente: qual é a intenção real por trás do pedido? O que quem pediu está intuindo sem conseguir articular? Em que nível cognitivo está a demanda — e em que nível você operaria se começasse agora? Quem vai carregar a skill, em que runtime, para fazer o quê? O que precisa mudar no comportamento do executor-alvo? Escreva a declaração em prosa completa, para quem pediu ou numa nota de trabalho fora da skill. Se duas leituras plausíveis do pedido levam a skills diferentes e nada no material decide entre elas, a pergunta a quem pediu faz parte deste movimento.

**Por que.** Pedidos chegam articulados abaixo da intenção real. Executar a versão literal produz um artefato no nível errado, e a versão profunda quase sempre exige um salto de nível — do 2 para o 3, do 3 para o 5.

**Quando termina.** Quando a declaração enuncia a intenção real, o nível que ela exige e o estado mental necessário para atendê-la — e é substancialmente diferente do pedido literal. Se for idêntica, a meta-cognição foi superficial.

**Sinal de que foi pulado.** Arquivos começam a ser criados logo depois da leitura do pedido; a skill atende ao enunciado ("documentar o processo X") em vez da intenção ("fazer o agente decidir X como o especialista decide").

---

## Movimento 3 — Declaração do contexto de execução

**O que fazer.** Criar, ou identificar, o documento raiz da skill-alvo. Ele declara três coisas: quem é o executor-alvo — modelo, runtime, capacidades e limites concretos, nunca apenas "uma IA"; o que ele otimiza — a função objetivo e, quando houver, de quem é o tempo ou o dinheiro escasso; e os axiomas numerados que governam todas as decisões dentro da skill, com a ordem de precedência quando entrarem em tensão. Numa skill pequena, a raiz pode ser uma seção do `SKILL.md`; numa maior, é um documento próprio, lido antes de todos os outros.

**Por que.** Sem raiz explícita, cada documento opera com suposições implícitas sobre o executor, e essas suposições divergem entre documentos — uma incoerência invisível durante a escrita e destrutiva durante o uso. A raiz é a constituição da skill; todo o resto é lei ordinária que deriva dela. O erro clássico é pular este movimento porque "é óbvio quem é o executor". Nunca é: um humano lendo um livro, um humano seguindo um processo, um agente carregando uma skill em sessão, um agente recebendo fragmentos por busca e um subagente recebendo um briefing são executores diferentes, e cada um pede uma skill diferente.

**Quando termina.** Quando cada princípio que a skill vai conter — os já escritos, numa refatoração; os inventariados na imersão, numa criação — tem um axioma de origem identificável. Princípio sem axioma de origem indica um axioma faltando ou um princípio que não pertence à skill.

**Sinal de que foi pulado.** Documentos discordam sobre o que é escasso; aparece um documento de sobrescrita; o executor-alvo herda premissas do material de origem que ninguém declarou.

---

## Movimento 4 — Reconstrução canônica do conteúdo

**O que fazer.** Escrever, ou reescrever, cada documento em Nível 3: cada princípio articulado como se sempre tivesse sido a verdade, sem linguagem comparativa, sem referência a versões, cada documento autossuficiente para quem nunca viu outra versão. Releia as fontes de cada documento imediatamente antes de escrevê-lo. Escreva você mesmo — esta é a parte que não se delega. Numa refatoração, o movimento assume a forma de edições cirúrgicas nos pontos em que convenções foram importadas como universais; o que já está em Nível 3 fica intocado, e reescrita em massa é quase sempre excesso de engenharia.

**Por que.** O Nível 3 é o único em que a skill funciona como substrato habitável. Texto de Nível 2 serve a quem quer entender uma transição, mas, carregado como sistema operacional, entrega ao executor-alvo uma transição que ele nunca presenciou.

**Quando termina.** Quando qualquer parágrafo de qualquer documento faz sentido isolado, sem o contexto de como as coisas eram, e nenhum trecho carrega as palavras-sintoma de costura descritas em [Escrita Canônica](escrita-canonica.md).

**Sinal de que foi pulado.** Costuras visíveis; tabelas que comparam versões; arquivos nomeados por versão ("-v2", "-novo").

---

## Movimento 5 — Integração estrutural tipada

**O que fazer.** Conectar os documentos por links explicitamente tipados, em três categorias: estruturais (pai, irmãos, filhos), semânticas (relações de significado entre conceitos) e funcionais (relações de uso conjunto). Cada conexão recebe um tipo e uma força — forte, moderada ou sutil. Os tipos seguem predicados que o modelo já conhece, como os de ontologias formais; vocabulário inventado custa atenção e derrota o propósito. A anatomia completa das conexões está em [Rede Sináptica](../como-construir/rede-sinaptica.md).

**Por que.** Link sem tipo é sinal fraco: o agente percebe que há relação, mas não sabe se deve usar os dois documentos juntos, entender um antes do outro ou tratar um como caso particular do outro. O tipo transforma cada link numa instrução para o raciocínio que vem depois.

**Quando termina.** Quando todo documento tem no mínimo duas conexões semânticas e uma funcional, todas tipadas e com força declarada; quando toda conexão semântica tem a recíproca no documento de destino; quando nenhum link aponta para o vazio e nenhum documento está isolado.

**Sinal de que foi pulado.** Listas de "veja também"; links sem razão declarada; um grafo navegável numa direção só.

---

## Movimento 6 — Arquitetura de atenção

**O que fazer.** Posicionar a informação crítica nas zonas de atenção premium e dar a cada documento um frontmatter enxuto: identidade (`id`, `nome`, `tipo`, `camada`, `status`), essência comprimida, uma palavra mnemônica e metadados epistêmicos (`certeza`, `maturidade`, `origem`). Quando a skill tem mais de cinco ou seis documentos, organizá-los em subdiretórios semânticos, para que os próprios caminhos funcionem como pistas de contexto. Escrever o frontmatter do `SKILL.md` conforme a especificação do runtime e a `description` como gatilho de ativação.

**Por que.** Atenção posicional em U, estado latente inicial, formatos aprendidos e calibração epistêmica — os mecanismos de [Atenção do Transformer](../como-pensar/atencao-do-transformer.md) — fazem do topo de cada documento a posição mais valiosa da skill. A essência ali colocada decide se o agente precisa ler o resto e colore a leitura de tudo o que vem depois.

**Quando termina.** Quando cada documento tem frontmatter de dez a quinze linhas, nunca mais de vinte; quando cada essência é legível isoladamente e captura o núcleo; quando a estrutura de diretórios reflete distinções semânticas reais; quando o `SKILL.md` e a `description` cumprem a especificação do runtime.

**Sinal de que foi pulado.** Essências que parafraseiam o título; frontmatter de trinta linhas; pastas organizadas por data ou por origem em vez de por função.

---

## Movimento 7 — Verificação em mente fresca

**O que fazer.** Simular — e, sempre que o ambiente permitir, executar — um leitor que nunca viu a skill. O que ele vê primeiro? Em que ordem encontra os documentos? Há ambiguidade nos pontos de entrada? Os artefatos ao redor — README, `CLAUDE.md`, `AGENTS.md`, arquivos de configuração, outras skills com descrições sobrepostas — estão alinhados ou emitem sinais contraditórios? Rode a auditoria mecânica. Depois entregue a um agente sem histórico — um subagente ou uma sessão nova, isolada do ambiente real — uma tarefa representativa do domínio e uma tarefa vizinha que não deveria ativar a skill, e observe o comportamento. O protocolo completo está em [Verificação em Mente Fresca](../como-construir/verificacao-em-mente-fresca.md).

**Por que.** A skill nunca é lida isolada. Um sinal contraditório em qualquer artefato ao redor recria, vindo de fora, a mesma incoerência que você eliminou dos documentos.

**Quando termina.** Quando você consegue descrever, passo a passo, o que um agente fresco encontra ao abrir o projeto pela primeira vez, e em cada passo o sinal recebido é consistente com a intenção da skill. Ambiguidades descobertas aqui são corrigidas na origem antes de a skill ser declarada pronta.

**Sinal de que foi pulado.** A verificação consistiu em você mesmo reler os documentos — o único leitor que jamais será fresco.

---

## Quando a verificação reprova

Volte ao movimento em que a falha nasceu. Na maioria das vezes é o 4, uma reconstrução incompleta, ou o 7, uma ambiguidade de contexto; às vezes é o 3, um axioma que falta, ou o 2, uma intenção lida no nível errado. Nunca corrija uma falha de substrato com uma camada por cima: o remendo é Nível 2 por construção.

---

## Continuidade entre sessões

Quando a construção atravessa mais de uma sessão, ou quando o contexto é compactado, o estado integrado não sobrevive. Sobrevive o que está escrito: a raiz, os documentos prontos, a declaração de intenção. Retome relendo a raiz e as fontes do próximo documento — nunca a partir de um resumo da sessão anterior. Resumo é representação mediada, e a reconstrução que parte dele sai em Nível 2. Essa é mais uma razão para a raiz ser escrita primeiro: além de constituição da skill, ela é o seu próprio ponto de reentrada.

---

## Rede Sináptica

### Estruturais
- **Pai:** [Contexto de Execução e Axiomas](../contexto-de-execucao.md) — Axioma 2
- **Irmãos:** [Escrita Canônica](escrita-canonica.md), [Presença Direta](presenca-direta.md), [Divisão do Trabalho Cognitivo](divisao-do-trabalho-cognitivo.md)

### Semânticas
- `é-caso-especial-de` **forte** — [Contexto de Execução e Axiomas](../contexto-de-execucao.md): o Axioma 2 desdobrado em sequência causal com critérios de término
- `complementa` **forte** — [Escrita Canônica](escrita-canonica.md): o Movimento 4 se executa pela escrita canônica
- `complementa` **moderada** — [Presença Direta](presenca-direta.md): a verificação direta atravessa todos os movimentos, não só o último
- `complementa` **moderada** — [Divisão do Trabalho Cognitivo](divisao-do-trabalho-cognitivo.md): decide, em cada movimento, o que se delega e o que fica com o autor
- `é-generalização-de` **forte** — [Da Fonte ao Substrato](../como-construir/da-fonte-ao-substrato.md): a criação a partir de uma fonte é a sequência aplicada a material bruto
- `é-generalização-de` **forte** — [Refatoração de Skills](../como-construir/refatoracao-de-skills.md): a refatoração é a sequência aplicada a uma skill que já opera

### Funcionais
- `contextualiza` **forte** — [Verificação em Mente Fresca](../como-construir/verificacao-em-mente-fresca.md): situa a verificação como o último movimento, depois do conteúdo e da estrutura
- `restringe` **moderada** — [Rede Sináptica](../como-construir/rede-sinaptica.md): a rede só começa depois que todo o conteúdo está em Nível 3
