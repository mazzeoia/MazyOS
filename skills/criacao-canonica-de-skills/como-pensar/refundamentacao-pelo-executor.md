---
id: como-pensar.refundamentacao-pelo-executor
nome: Refundamentação de Princípios Pelo Executor
tipo: mecanismo
camada: 3-epistemológica
status: ativo

essencia: >
  Todo princípio importado traz escondido o executor original; cada um sobrevive
  igual, sobrevive com fundamento novo ou sai, e a premissa do executor mora só
  na raiz.

em-uma-palavra: Triagem

certeza: consensual
maturidade: consolidado
origem: empírica
---
# Refundamentação de Princípios Pelo Executor

> Todo princípio importado carrega, escondida, a figura de quem o executava. Antes de entrar numa skill, cada princípio passa por uma triagem — sobrevive com o mesmo fundamento, sobrevive com fundamento novo ou não sobrevive — e a premissa sobre o executor fica centralizada na raiz da skill, nunca espalhada pelos documentos.

---

## O princípio

Bons frameworks viajam. Princípios nascidos em fábricas, em equipes de engenharia, em consultorias ou em livros de método são transplantados para skills de agentes o tempo todo — e devem ser, porque condensam décadas de aprendizado. Mas nenhum princípio chega sozinho. Ele vem com uma justificativa, com exemplos, com limiares numéricos e com uma voz, e é nessas camadas que mora a figura do executor original: alguém com oito horas por dia, energia que acaba, memória de trabalho curta, orçamento apertado, emoções que resistem a mudança.

Quando o executor muda, a figura escondida não muda sozinha. Uma skill que importa princípios sem triagem instala no executor-alvo as limitações do executor original — e o faz de forma invisível, porque a premissa nunca foi declarada. O agente passa a amostrar onde poderia ler tudo, a adiar o que poderia fazer agora, a parar no terceiro porquê, a tratar como escasso o que para ele não é. E deixa de tratar como escasso o que para ele é: a janela de contexto, a ausência de memória entre sessões, a falta de acesso a uma ferramenta que o texto supõe disponível.

Executor, aqui, é mais que a espécie de quem executa. Inclui o modelo, o runtime e as capacidades concretas: se há shell, se há subagentes, se há rede, se há acesso de escrita, se o agente trabalha sozinho ou dentro de um time. Uma skill escrita para um agente com terminal e subagentes, carregada num ambiente sem nenhum dos dois, sofre a mesma ruptura que um manual de fábrica entregue a um robô.

---

## O mecanismo

### 1 — Localizar a premissa do executor

Todo princípio operacional supõe algo sobre quem o executa, e essa suposição raramente aparece como premissa declarada. Ela se esconde em quatro lugares: na **justificativa** ("porque o tempo é curto"), no **exemplo** (uma equipe de quinze pessoas numa sala), no **limiar numérico** ("pelo menos três porquês", "prompts de até quinhentas palavras") e na **voz** (conselhos de motivação, alertas sobre cansaço). Leia o material de origem procurando nesses quatro lugares.

### 2 — Separar o princípio da justificativa

Quase todo princípio tem duas camadas: uma afirmação causal e uma motivação. "Elimine antes de otimizar" afirma que otimizar algo que não deveria existir é trabalho perdido; a motivação usual é que o esforço é escasso. A triagem acontece nessa separação — a afirmação causal pode valer para qualquer executor enquanto a motivação vale só para o original.

### 3 — Aplicar os três destinos

**Sobrevive com o mesmo fundamento.** A afirmação causal vale para qualquer sistema cognitivo, e a justificativa também. Decompor por porquês funciona porque causalidade funciona para qualquer executor; separar fato de convenção é igualmente universal; a degradação de informação a cada camada intermediária continua verdadeira quando o intermediário é um agente, um pipeline ou uma camada de abstração. Nesses casos, no máximo exemplos e voz pedem ajuste.

**Sobrevive com fundamento novo.** A afirmação causal vale, mas por outra razão. Eliminar antes de otimizar deixa de proteger esforço e passa a proteger o sinal: trabalho desnecessário gera ruído que degrada o raciocínio do agente e de quem lê o resultado. Paralelizar deixa de servir à velocidade e passa a servir à diversidade cognitiva — caminhos independentes enxergam o que um caminho só não vê. Testar a capacidade de um agente antes de lhe dar uma tarefa deixa de economizar minutos e passa a evitar um turno de saída vazia que abre uma lacuna de cobertura. São os casos mais valiosos da triagem, e os mais traiçoeiros: o texto parece certo do jeito que está, porque a conclusão não muda; muda o porquê, e com ele os limites de aplicação.

**Não sobrevive.** A afirmação só fazia sentido para o executor original. Prioridade por calendário — "agora, esta semana, próxima sprint" — não sobrevive para quem consegue fazer tudo de uma vez; a ordem passa a vir do grafo de dependências. Uma métrica de eficiência que premia poucos turnos por decisão não sobrevive para um executor cuja escassez real é cobertura e profundidade; em seu lugar entram métricas do que é escasso para ele. Princípio que não sobrevive sai da skill — e não deixa nota de rodapé dizendo que saiu.

### 4 — Caçar os resíduos

Mesmo depois da triagem, a premissa antiga deixa rastros no texto, e eles se repetem em famílias reconhecíveis:

- triagem por escassez ("priorize pelo impacto", "na maioria dos casos não vale a pena");
- teto de conhecimento ("você não precisa entender os detalhes");
- limiares arbitrários de escala humana ("três porquês", "quinhentas palavras", "equipes de até vinte pessoas");
- justificativa por tempo economizado;
- argumento de custo num texto que declara que custo não importa;
- enquadramento de perfeccionismo ("não tente acertar tudo de uma vez");
- prioridade subjetiva ("isto é mais importante", "chegou a hora") no lugar de condição verificável;
- emoção usada como sinal ("ninguém ficou desconfortável com o novo desenho");
- fisiologia usada como razão ("o cérebro precisa fechar o ciclo");
- metáforas de esforço humano ("heroísmo operacional", "fôlego").

O padrão de troca nas boas reescritas é consistente. O critério de escopo deixa de ser magnitude e vira relevância: uma convenção barata pode esconder justamente a restrição que mais distorce o problema. Os obstáculos deixam de ser pressa e resistência e viram estruturais: explosão combinatória, parada prematura numa resposta plausível, circularidade disfarçada. E duas coisas se preservam: narrativas históricas sobre humanos, que descrevem humanos corretamente porque são sobre humanos, e analogias que funcionam dentro do próprio quadro.

### 5 — Centralizar a premissa na raiz

O passo mais estrutural não é reescrever princípios um a um. É dar à skill uma raiz que declare explicitamente quem é o executor-alvo, com que capacidades ele opera e o que ele otimiza. Documentos sem essa raiz não estão errados — estão desancorados: cada um carrega por conta própria uma suposição sobre o executor, e qualquer mudança de executor exige revisitar todos. Com a raiz declarada, a maior parte dos documentos se revela universal, e as poucas mudanças necessárias ficam óbvias e cirúrgicas.

---

## Como reconhecer que a triagem foi pulada

O executor errado aparece no comportamento do executor-alvo: um agente que amostra em vez de ler tudo, que adia o que poderia fazer, que encerra a análise no terceiro porquê; métricas que premiam a escassez antiga em vez da real; documentos que se contradizem — um manda minimizar turnos, outro diz que profundidade não tem custo; e, sinal mais nítido de todos, um documento de sobrescrita mandando ignorar o que os outros dizem, prova de que a premissa foi corrigida num lugar e continua viva nos demais.

---

## O que a refundamentação não é

**Não é relativismo.** As verdades causais ficam. O que muda são fundamentos, limiares e exemplos amarrados ao executor.

**Não é reescrever a fonte.** O material original continua correto para o executor dele. A refundamentação acontece onde o princípio é carregado pelo executor novo — na skill.

**Não é trocar "pessoa" por "agente".** Substituir a palavra sem rederivar a justificativa deixa a premissa original intacta, apenas disfarçada.

**Não é purismo.** Apagar toda referência humana elimina junto os exemplos que davam chão aos princípios. Declarar que nada é escasso faz o sistema explodir em ruído, contrariando o próprio fundamento novo.

---

## A tensão que não some: de quem é esse tempo?

O esforço e o tempo do executor-alvo podem não ser escassos; o tempo de quem espera por ele e o dinheiro de quem paga por ele podem ser. Um agente de atendimento que responde a um cliente continua precisando de latência baixa, porque há uma pessoa do outro lado. Trabalho de agente já pago não se descarta por pressa. A pergunta certa nunca é "o custo importa?", e sim "de quem é esse tempo, de quem é esse dinheiro?". A raiz da skill responde a essa pergunta para o executor-alvo dela.

A voz segue a mesma lógica: acompanha quem carrega o documento e para quê. Segunda pessoa dirigida ao agente é legítima numa skill; o que não é legítimo é uma voz motivacional que pressupõe um leitor cansado.

---

## Analogias

**A receita na altitude.** Em cidades muito altas, a água ferve abaixo de cem graus. O princípio da receita — cozinhar até o amido gelatinizar — sobrevive; o fundamento operacional muda; e os tempos fixos não sobrevivem. Quem troca a panela e mantém o cronômetro come o macarrão cru. Onde a analogia quebra: a altitude muda a física igualmente para todos, enquanto a troca de executor muda capacidades de forma desigual — um agente não se cansa, mas tem janela finita e não lembra da sessão anterior —, então cada princípio precisa de triagem própria.

**O manual de direção no carro automático.** "Pise na embreagem antes de trocar a marcha" não sobrevive. "Antecipe a curva" sobrevive com o mesmo fundamento. "Mantenha o giro baixo para economizar" sobrevive com fundamento novo: o câmbio cuida da marcha, e a economia passa a depender de acelerar com suavidade. Onde a analogia quebra: carros são projetados sabendo como o motorista funciona; capacidades de agentes mudam rápido, e um princípio que não sobreviveu pode voltar a valer quando o executor mudar de novo — razão a mais para a premissa morar num lugar só.

---

## Rede Sináptica

### Estruturais
- **Pai:** [Contexto de Execução e Axiomas](../contexto-de-execucao.md) — Axioma 1 e a declaração do executor
- **Irmãos:** [Skill Como Substrato Cognitivo](substrato-cognitivo.md), [Níveis de Profundidade Cognitiva](niveis-de-profundidade-cognitiva.md), [Atenção do Transformer](atencao-do-transformer.md)

### Semânticas
- `complementa` **moderada** — [Skill Como Substrato Cognitivo](substrato-cognitivo.md): a premissa que a skill não declara é preenchida pelo material de origem
- `complementa` **moderada** — [Níveis de Profundidade Cognitiva](niveis-de-profundidade-cognitiva.md): perceber a premissa compartilhada por todos os princípios é visão de Nível 5
- `é-análogo-a` **moderada** — [Refatoração de Skills](../como-construir/refatoracao-de-skills.md): a triagem dos princípios em três destinos espelha a triagem dos documentos em quatro

### Funcionais
- `habilita` **forte** — [Da Fonte ao Substrato](../como-construir/da-fonte-ao-substrato.md): a triagem é o que permite transformar material escrito para outro executor
- `contextualiza` **moderada** — [Os Sete Movimentos](../como-executar/sete-movimentos.md): explica por que a raiz vem antes de qualquer documento — é nela que a premissa do executor se centraliza

### Tensões
- Refundamentação e purismo — apagar toda referência humana elimina os exemplos que davam chão aos princípios
