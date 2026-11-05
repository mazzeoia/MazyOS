---
id: como-construir.arquitetura-em-camadas
nome: Arquitetura em Camadas
tipo: padrão
camada: 7-prática
status: ativo

essencia: >
  Até oito camadas com funções insubstituíveis — entrada, raiz, operacional e
  prática sempre; epistemológica quase sempre —, cada documento com um tipo que
  calibra o peso que o agente lhe dá.

em-uma-palavra: Camadas

certeza: consensual
maturidade: em-evolução
origem: empírica
---
# Arquitetura em Camadas

> Uma skill madura se organiza em até oito camadas, cada uma com uma função cognitiva que nenhuma outra substitui: entrada, raiz, epistemológica, operacional, contratos, meta-engenharia, prática e referência. Entrada, raiz, operacional e prática nunca faltam; a epistemológica quase nunca. Cada documento assume um papel tipológico que diz ao agente como pesá-lo.

---

## Processo e estrutura

Saber construir e saber o que precisa existir no resultado são conhecimentos diferentes. Um autor pode dominar os movimentos — imersão, raiz, escrita em Nível 3, conexões tipadas — e ainda assim entregar uma skill estruturalmente incompleta, porque não sabia que camadas o resultado precisava ter. Os movimentos são a receita; a arquitetura é a anatomia do prato pronto. Quem cozinha precisa das duas: do processo e da capacidade de reconhecer o resultado correto.

O padrão de camadas descrito aqui é recorrente em skills que funcionam, e não por acaso: ele emerge das restrições de construir um corpo de conhecimento para ser carregado no contexto de um modelo de linguagem.

---

## As oito camadas

### Camada 1 — Entrada (obrigatória)

**Função.** Ponto de carregamento. Diz o que a skill faz, quando usá-la, que identidade o agente assume ao carregá-la e onde está cada um dos outros documentos, e oferece uma sequência operacional para uso imediato.

**Forma.** Um único documento, com o nome que o runtime espera — no padrão Agent Skills, o `SKILL.md`. É metadocumentação: não recebe `tipo`. Por ser o único arquivo carregado sempre que a skill é ativada, carrega também o núcleo comprimido — os axiomas em uma linha cada e a sequência de trabalho —, para que o modo de pensar se instale mesmo que o agente não abra mais nada.

### Camada 2 — Raiz (obrigatória)

**Função.** Declarar quem é o executor-alvo e com que capacidades opera, o que ele otimiza e quais axiomas governam todas as decisões da skill, com a ordem de precedência quando entram em tensão.

**Forma.** Um único documento na raiz do diretório da skill, fora de subdiretórios, citado por todos os outros como ancestral direto. Tipo `fundamento`. Numa skill pequena, pode ser uma seção do `SKILL.md`.

### Camada 3 — Epistemológica (quase obrigatória)

**Função.** Ensinar o agente a pensar: os princípios cognitivos que ele aplica para decidir bem dentro do domínio. Sem esta camada, a skill vira uma lista de procedimentos sem substrato de raciocínio — funciona nos cenários previstos e quebra em todos os outros.

**Forma.** De três a oito documentos num subdiretório de nome semântico, como `como-pensar/`. Tipos predominantes: `fundamento`, `modelo-mental`, `mecanismo`, `ferramenta`. A ausência desta camada só é aceitável em skills estritamente procedurais, e mesmo assim como decisão declarada, não como acidente.

### Camada 4 — Operacional (obrigatória)

**Função.** Traduzir os princípios em conduta durante a execução: o que fazer e o que não fazer enquanto o trabalho acontece.

**Forma.** De três a seis documentos, num subdiretório como `como-executar/`. Tipos predominantes: `mecanismo` e `heurística`. Cada documento deriva de um axioma da raiz e se conecta a pelo menos um princípio da camada epistemológica.

### Camada 5 — Contratos (condicional)

**Função.** Codificar os contratos de comunicação quando a skill envolve componentes que trocam trabalho — agentes, serviços, sessões, etapas: o que cada transição precisa carregar, como a continuidade se preserva, que garantias cada passagem oferece.

**Forma.** De um a quatro documentos, tipicamente do tipo `padrão`. Skills sobre o processo interno de um único agente podem dispensá-la; skills com qualquer forma de passagem entre componentes precisam dela.

### Camada 6 — Meta-engenharia (opcional)

**Função.** Operar no nível de cima: não como fazer X, mas como projetar o sistema que faz X. Aparece em skills que configuram componentes inferenciais, como prompts para outros agentes.

**Forma.** De um a três documentos, tipicamente `modelo-mental`.

### Camada 7 — Prática (obrigatória)

**Função.** Ensinar a aplicar: padrões, fluxos de trabalho, estratégias de decomposição, protocolos específicos do domínio. É onde os princípios abstratos viram decisões concretas.

**Forma.** De três a oito documentos, num subdiretório nomeado pelo verbo principal da skill — `como-orquestrar/`, `como-revisar/`, `como-construir/`. É a camada de maior diversidade tipológica: `padrão`, `mecanismo`, `ferramenta`, `heurística`.

### Camada 8 — Referência (condicional a ferramentas técnicas)

**Função.** Oferecer o que o agente consulta durante a execução: catálogos de comandos, parâmetros, APIs, vocabulários fechados. É estritamente informativa.

**Forma.** Um ou dois documentos em `referencia/`, do tipo `ferramenta`. Scripts executáveis pertencem funcionalmente a esta camada: são executados, não carregados, e por isso entregam verificação determinística sem custo de contexto.

### Camadas são funções, não arquivos

Numa skill pequena, várias camadas convivem no mesmo arquivo. Um `SKILL.md` com dois documentos pode abrigar entrada e raiz no próprio `SKILL.md`, a camada operacional num documento e a prática no outro. O que não pode acontecer é uma função faltar. Uma função ganha arquivo próprio quando o seu conteúdo excede o que o `SKILL.md` comporta dentro do tamanho recomendado pelo runtime, ou quando o agente só precisa dela em parte das tarefas — é aí que a abertura sob demanda passa a economizar atenção.

---

## Os papéis dos documentos

Cada documento declara um `tipo`, e o tipo diz ao agente como pesá-lo.

- **`fundamento`** — verdade irredutível, que não deriva de nenhum outro documento da skill. Pode ser enunciado sem referência a outros conceitos, é citado por muitos documentos como ancestral, e alterá-lo forçaria reescrita em cascata. Aparece nas camadas 2 e 3.
- **`mecanismo`** — como algo funciona: um processo causal, com fases encadeadas, que explica o como e o porquê e se aplica sem julgamento subjetivo adicional. Camadas 3, 4 e 7.
- **`padrão`** — estrutura recorrente, reconhecível em muitas instâncias, com forma identificável e repetível; costuma vir acompanhada dos anti-padrões correspondentes. Camadas 5 e 7.
- **`heurística`** — regra prática que funciona na maioria dos casos e tem exceções claras; o uso correto exige calibração ao contexto. Camada 4, às vezes 7.
- **`ferramenta`** — instrumento diretamente aplicável, com entradas e saídas claras: um filtro, um teste, uma matriz de decisão, um catálogo. Camadas 3, 7 e 8.
- **`modelo-mental`** — lente interpretativa que muda como o agente enxerga um tipo de situação e, com isso, que perguntas ele faz. Camadas 3 e 6.
- **`lei`** — relação formal e testável entre variáveis. Rara em skills; aparece quando o domínio a tem, como uma fórmula financeira ou uma restrição física.

O tipo só funciona como pista se for aplicado com coerência: conteúdos de natureza semelhante recebem o mesmo tipo, e todo `mecanismo` descreve de fato um processo causal.

---

## Os princípios de sinergia do conjunto

**Derivação axiomática completa.** Todo princípio de qualquer documento pode ser rastreado até um axioma da raiz. Para verificar, tome um princípio qualquer e pergunte de que axioma ele deriva. Se a resposta exige forçar o axioma, há uma lacuna: falta um axioma, ou sobra um princípio.

**Cobertura exaustiva sem sobreposição destrutiva.** Os documentos cobrem todo o espaço do problema que a skill endereça, e cada um tem escopo próprio. Sobreposição parcial com ângulos diferentes é redundância benéfica; dois documentos dizendo a mesma coisa de formas incompatíveis é falha de arquitetura. Para verificar, tome cada par de documentos relacionados e pergunte o que um diz que o outro não diz. Resposta vaga pede fusão, eliminação ou diferenciação.

**Gradiente de abstração limpo.** Há um gradiente nítido da raiz e da epistemologia, mais abstratas, até a prática e a referência, mais concretas. O agente sobe o gradiente para entender o porquê de uma decisão e desce para saber o como. Para verificar, tome documentos de camadas diferentes e pergunte qual é mais abstrato e por quê; se a resposta não for óbvia, um deles está na camada errada.

A reciprocidade das conexões e a calibração epistêmica uniforme completam a sinergia; elas pertencem à rede e à anatomia de cada documento.

---

## Como desenhar a arquitetura de uma skill-alvo

O material de origem está organizado para ser lido; a skill precisa ser organizada para ser carregada. Por isso o desenho parte dos momentos de decisão do executor-alvo, não dos capítulos da fonte.

1. **Liste os momentos do trabalho do executor-alvo** — recebe o pedido, decide isto, executa aquilo, confere aquilo outro.
2. **Para cada momento, pergunte o que precisa estar no contexto:** uma lente (camada 3), uma conduta (camada 4), um padrão ou procedimento (camada 7), um fato de consulta (camada 8), um contrato de passagem (camada 5).
3. **Agrupe por função em camadas** — um escopo por documento, cada documento nomeado pela sua função.
4. **Separe o que precisa estar presente mesmo que o agente não abra mais nada.** Isso vai para o `SKILL.md`.
5. **Confira as camadas obrigatórias** e decida explicitamente as condicionais.
6. **Confira o dimensionamento.** Uma camada com um único documento enorme provavelmente esconde um hub; uma com dez documentos finos provavelmente fragmenta um conceito só.

---

## Anti-padrões arquiteturais

**Camada crítica ausente.** Documentos de prática sem nenhum documento epistemológico, ou axiomas sem nenhum documento operacional. O agente recebe instruções sem substrato ou princípios sem aplicação, e a skill fica frágil fora dos cenários exatos. Correção: criar a camada que falta, com prioridade para a epistemológica, sem a qual a skill não generaliza.

**Documento hub.** Um documento carrega vários conceitos que deveriam estar separados; o sinal é uma rede com mais de quinze conexões tipadas e uma leitura confusa. Correção: dividir por escopo e redistribuir as conexões.

**Derivação axiomática quebrada.** Um princípio opera sobre premissas que não estão na raiz, e o agente pode ser puxado por dois princípios em direções opostas. Correção: acrescentar o axioma que falta, se o princípio é legítimo, ou eliminar o princípio, se ele é um acidente que sobreviveu sem razão.

O documento isolado, a conexão unidirecional e o salto de camadas são falhas da rede; a tipologia inconsistente é falha da anatomia.

---

## Exemplos

**Esta skill.** A entrada é o `SKILL.md`; a raiz é `contexto-de-execucao.md`; a camada epistemológica está em `como-pensar/`, a operacional em `como-executar/`, a prática em `como-construir/`, a referência em `referencia/` e `scripts/`. Não há camada de contratos porque a única passagem entre componentes — o briefing a um subagente e o relatório de volta — cabe numa seção da divisão do trabalho cognitivo; não há meta-engenharia separada porque o domínio inteiro da skill já é o desenho de substrato para agentes.

**Uma skill de revisão de código.** Raiz: o executor-alvo é um agente com acesso ao repositório e permissão para rodar testes, que otimiza defeitos reais encontrados por mudança. Epistemológica: separar defeito de preferência (`fundamento`); ler a mudança no contexto do sistema (`modelo-mental`). Operacional: revisar tudo o que mudou (`heurística`); evidência antes de opinião (`mecanismo`). Prática: padrões de defeito por linguagem (`padrão`); protocolo de comentário (`ferramenta`). Referência: os comandos de teste e lint do projeto (`ferramenta`).

---

## Rede Sináptica

### Estruturais
- **Pai:** [Contexto de Execução e Axiomas](../contexto-de-execucao.md) — Axiomas 1 e 6
- **Irmãos:** [Anatomia do Documento](anatomia-do-documento.md), [Rede Sináptica](rede-sinaptica.md), [Da Fonte ao Substrato](da-fonte-ao-substrato.md), [Refatoração de Skills](refatoracao-de-skills.md), [Verificação em Mente Fresca](verificacao-em-mente-fresca.md)

### Semânticas
- `pressupõe` **forte** — [Skill Como Substrato Cognitivo](../como-pensar/substrato-cognitivo.md): a arquitetura organiza para carregamento porque a skill é carregada, não consultada
- `complementa` **forte** — [Anatomia do Documento](anatomia-do-documento.md): a arquitetura desenha o conjunto; a anatomia, cada unidade dele
- `complementa` **forte** — [Rede Sináptica](rede-sinaptica.md): as camadas dão a hierarquia; a rede dá os caminhos entre elas
- `complementa` **moderada** — [Formato Agent Skills](../referencia/formato-agent-skills.md): a camada de entrada se materializa no formato que o runtime exige

### Funcionais
- `habilita` **forte** — [Da Fonte ao Substrato](da-fonte-ao-substrato.md): o desenho por momentos de decisão é o passo que redecompõe a fonte
- `contextualiza` **moderada** — [Refatoração de Skills](refatoracao-de-skills.md): camada ausente ou decomposição errada indicam reconstrução, não cirurgia
