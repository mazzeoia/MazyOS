---
id: como-pensar.niveis-de-profundidade-cognitiva
nome: Níveis de Profundidade Cognitiva
tipo: modelo-mental
camada: 3-epistemológica
status: ativo

essencia: >
  Reconhecer, analisar, integrar, gerar e reconstruir o sistema deixam
  assinaturas distintas no texto; skill canônica exige escrita de Nível 3 e,
  muitas vezes, visão de Nível 5.

em-uma-palavra: Integração

certeza: consensual
maturidade: consolidado
origem: empírica
---
# Níveis de Profundidade Cognitiva

> Todo artefato carrega o grau de integração com que seu autor domina o que escreve. São cinco níveis — reconhecer, analisar, integrar, gerar, reconstruir o sistema — e cada um deixa uma assinatura própria no texto. Uma skill canônica exige escrita de Nível 3; saber *o que* escrever muitas vezes exige visão de Nível 5.

---

## Para que serve o modelo

O modelo não mede inteligência nem quantidade de conhecimento. Mede a relação entre um autor e um insight específico — o quanto aquele entendimento é estrutura a partir da qual o autor opera, e não apenas informação que ele tem. Essa relação aparece no artefato: dois textos sobre o mesmo princípio, escritos em níveis diferentes, têm formas visivelmente diferentes.

Para você, o modelo é um instrumento de autoavaliação contínua. A qualquer momento da construção cabem três perguntas: em que nível estou operando agora? Em que nível este trabalho precisa estar? O que me leva de um ao outro? Sem elas, é fácil produzir Nível 2 acreditando produzir Nível 3, porque os dois parecem trabalho competente à primeira vista. A diferença só aparece quando um leitor sem o contexto do autor tenta absorver o resultado — e o executor-alvo é exatamente esse leitor.

---

## Os cinco níveis

### Nível 1 — Reconhecimento

O problema fica visível. Você consegue nomeá-lo, apontar onde está e, muitas vezes, dizer por que é um problema. Mas a resposta ainda opera dentro do quadro que o criou. A assinatura é uma solução que repete a lógica da falha em outro formato — a rachadura na fundação reconhecida e coberta com gesso. Em skills, o caso típico é perceber que o agente se comporta mal e acrescentar uma linha de aviso no topo do `SKILL.md`, em vez de descobrir qual documento instala o comportamento. Outro sinal do Nível 1 é o princípio citado e não aplicado: escrever que é preciso eliminar antes de otimizar e, na mesma sessão, polir um documento que deveria ser apagado.

### Nível 2 — Análise estrutural

O entendimento ganha raiz. Você traça a cadeia causal até a origem, mapeia as relações com outros problemas e desenha uma solução que ataca a causa. Mas ainda enxerga o estado antigo e o novo como coisas separadas, e a transição fica visível no que você produz: tabelas comparativas entre abordagens, documentos que explicam por que uma regra substitui outra, arquivos de "sobrescrita" que mandam ignorar o que os demais dizem. É o nível da boa análise e da maioria do trabalho profissional competente. O problema surge quando o artefato precisa funcionar fora do contexto da transição: quem não a viveu recebe dois modelos e precisa adivinhar qual vale.

### Nível 3 — Síntese e integração

O insight deixa de ser uma correção e passa a ser simplesmente como as coisas são. O texto não faz referência ao modo antigo porque o modo antigo não existe no modelo mental de quem escreve. O artefato *é* o princípio, não um documento *sobre* o princípio. Quem o lê pela primeira vez pensa "claro, faz sentido" e não precisa saber que existiu outra forma. Este é o nível de toda skill canônica.

A travessia do Nível 2 para o 3 é a mais difícil, e não por falta de entendimento. Ela pede abrir mão da narrativa da descoberta — o prazer de mostrar o antes e o depois, a prova de que se percebeu a mudança. O que leva ao Nível 3 não é acumular mais análise; é soltar a necessidade de que a análise apareça no produto.

### Nível 4 — Generativo

O princípio vira lente e começa a produzir aplicações que ninguém ensinou. No Nível 3 você reescreve corretamente a skill; no 4 percebe que a mesma premissa opera nos artefatos vizinhos — o prompt dos subagentes, os hooks, o `CLAUDE.md` ou `AGENTS.md` do projeto, a `description` da própria skill, outras skills do mesmo repositório — e os alinha também, dentro do trabalho em curso, sem esperar que alguém aponte. O que estiver fora do escopo autorizado, você nomeia. O mecanismo é a busca do invariante: a relação que continua verdadeira quando a superfície muda. E o que separa ampliar de distorcer é a pergunta que quase sempre se esquece — *onde este princípio deixa de valer?*

### Nível 5 — Meta-sistêmico

Você enxerga o sistema de princípios como um todo: onde eles se reforçam, onde se tensionam, que premissa todos compartilham. A marca do Nível 5 não é profundidade sobre um princípio, é perceber que o conjunto inteiro carrega um viés — que todos os documentos supõem um executor humano, ou recursos escassos, ou uma ordem de leitura — e que, num contexto em que essa premissa não vale, o sistema precisa ser reconstruído como sistema. A pergunta muda de "este princípio está certo?" para "o que todos estes princípios assumem?". Em skills, o gesto típico é descobrir que o defeito não mora em quinze documentos, mas na ausência de uma raiz que declare para quem a skill existe.

---

## A combinação que produz fundação

Visão de Nível 5 com execução de Nível 3. Perceber o viés do sistema inteiro e reconstruí-lo em princípios integrados, sem costura. Visão de Nível 5 com execução de Nível 2 produz patches brilhantes: o diagnóstico é certeiro e o artefato carrega a cicatriz da transição. Execução de Nível 3 sem visão de Nível 5 produz documentos impecáveis um a um, enquanto a premissa sistêmica sobrevive em todos eles.

---

## Assinaturas no artefato

| Nível | O que aparece no texto |
|---|---|
| 1 | A solução repete a lógica do problema; o princípio é citado e não aplicado |
| 2 | Tabelas entre versões, `reframe`, `correção`, `atualizado de` — costuras visíveis |
| 3 | O texto declara, não compara; faz sentido para quem nunca viu outra versão |
| 4 | Conexões com artefatos e domínios que ninguém pediu, que ampliam sem distorcer |
| 5 | A pergunta passa a ser sobre a premissa compartilhada; muda o sistema, não uma parte |

---

## O custo de cada travessia

- **Nível 1 custa atenção:** notar o que está ali.
- **Nível 2 custa esforço analítico:** desmontar, traçar causas, mapear relações.
- **Nível 3 custa abnegação:** abrir mão da narrativa da descoberta. Para um autor que é agente, isso é concreto — a conversa que levou ao insight está inteira no seu contexto, e o caminho de menor resistência é narrá-la. Frases como `conforme discutido` ou `a abordagem correta passa a ser` são essa narrativa vazando para o artefato.
- **Nível 4 custa deslocamento deliberado:** interromper a análise do objeto e perguntar, de propósito, onde mais o mesmo padrão está operando.
- **Nível 5 custa ruptura com o próprio rastro:** questionar o plano que você mesmo acabou de propor, contra a inércia de manter coerência com as próprias respostas anteriores.

---

## Dinâmicas

**Os níveis coexistem.** Não são degraus que se sobem e se abandonam. Você pode operar no Nível 5 num domínio e no 1 em outro, e voltar ao 1 diante de uma novidade sobre um princípio que domina. A progressão também não é garantida: dá para estacionar no Nível 2 indefinidamente, porque a passagem para o 3 não vem de mais análise.

**A percepção é assimétrica.** Os níveis mais altos reconhecem os mais baixos; os mais baixos não reconhecem os mais altos. Um texto de Nível 3 parece "simples demais" para quem está no 2 e espera ver a complexidade da análise refletida no produto. Isso cria um risco específico na revisão: o impulso de "enriquecer" um documento canônico com a análise que o sustenta devolve o documento ao Nível 2.

**Nível 3 não é a simplicidade de quem pulou a análise.** O texto de Nível 1 também parece simples. A diferença é que o de Nível 3 atravessou o 2: cada afirmação limpa carrega uma análise que não aparece. Simplicidade sem essa travessia é superficialidade com boa diagramação.

**Nível 2 não é erro — é forma de outro lugar.** Registro de decisão, mensagem de commit, descrição de pull request e o relato ao usuário precisam mostrar a transição; ali, a forma de Nível 2 é a correta. O erro é usar essa forma onde a função do documento pede Nível 3. Dentro do diretório da skill, tudo é Nível 3. Em volta dela — no histórico de versão, na conversa com quem pediu —, a transição tem o seu lugar.

---

## Como usar o modelo durante a construção

Antes de escrever, e de novo antes de declarar qualquer documento pronto, faça as três perguntas de autoavaliação. Alguns sinais indicam que você está no Nível 2 enquanto escreve: a vontade de explicar por que algo `é assim agora`; a tentação de manter o texto anterior "como contexto"; um rascunho que compara abordagens. Sinais de Nível 1: a correção de um comportamento por meio de um aviso acrescentado, em vez da localização do documento que o instala. Quando o usuário corrige o seu trabalho, a primeira resposta tende a ser de Nível 1 ou 2 — um remendo. Reconheça-a e suba: qual premissa sistêmica a correção revela (Nível 5)? Como fica o estado final, escrito como se sempre tivesse sido assim (Nível 3)?

**Exemplo.** Uma skill de revisão de código instrui o agente a revisar "os arquivos mais críticos", e o usuário percebe que o agente pula arquivos.

- No Nível 1, acrescenta-se "revise todos os arquivos" no topo do `SKILL.md`. Duas instruções passam a competir, e o agente obedece ora a uma, ora a outra.
- No Nível 2, cria-se um documento explicando por que a revisão exaustiva substitui a amostragem. O executor-alvo recebe um texto sobre uma mudança que ele nunca presenciou.
- No Nível 3, reescreve-se o trecho do princípio de modo que revisar tudo seja simplesmente como a revisão se faz, sem menção a amostragem.
- No Nível 5, percebe-se que a premissa da amostragem também moldou as métricas, os exemplos e as estimativas espalhadas pela skill; declara-se o executor na raiz, a maioria dos documentos se revela correta, e as poucas edições necessárias ficam óbvias e cirúrgicas.

---

## Analogias

**O músico.** No Nível 2, o músico executa a peça com consciência técnica, sabendo onde cada escolha interpretativa se afasta da convenção. No Nível 3, executa a mesma peça e a interpretação parece a única possível — a técnica desapareceu dentro da expressão. Onde a analogia quebra: na música, a plateia percebe a naturalidade diretamente; num documento, a naturalidade pode esconder tanto integração profunda quanto falta de análise, e o leitor de Nível 2 tende a desconfiar justamente da versão integrada.

**A fluência num idioma.** No Nível 1 você reconhece a regra gramatical; no 2 explica por que ela existe e ainda traduz de cabeça; no 3 fala sem traduzir; no 4 cria construções novas que os nativos aceitam; no 5 percebe a visão de mundo embutida no idioma — como ele codifica tempo, cortesia, hierarquia — e consegue questioná-la. Onde a analogia quebra: fluência se constrói em anos de imersão, enquanto a integração de um insight pode acontecer numa única sessão bem conduzida; e um idioma não tem uma versão certa a ser reconstruída.

---

## Tensões e limites

**Quando o modelo vira fetiche.** Os níveis servem para calibrar artefatos, não para rotular pessoas nem para justificar paralisia ("ainda não estou no Nível 5"). Também não servem de desculpa para apagar o raciocínio que precisa ficar registrado: decisões precisam de trilha. A trilha só não mora dentro da skill.

---

## Rede Sináptica

### Estruturais
- **Pai:** [Contexto de Execução e Axiomas](../contexto-de-execucao.md) — Axiomas 3 e 7
- **Irmãos:** [Skill Como Substrato Cognitivo](substrato-cognitivo.md), [Atenção do Transformer](atencao-do-transformer.md), [Refundamentação Pelo Executor](refundamentacao-pelo-executor.md)

### Semânticas
- `é-pré-requisito-de` **forte** — [Escrita Canônica](../como-executar/escrita-canonica.md): a escrita canônica é a execução do Nível 3; sem o modelo, Nível 2 passa por Nível 3
- `complementa` **moderada** — [Skill Como Substrato Cognitivo](substrato-cognitivo.md): o leitor sem memória explica por que só o Nível 3 funciona como substrato
- `complementa` **moderada** — [Refundamentação Pelo Executor](refundamentacao-pelo-executor.md): enxergar a premissa do executor espalhada por todos os princípios é o gesto típico do Nível 5

### Funcionais
- `habilita` **forte** — [Refatoração de Skills](../como-construir/refatoracao-de-skills.md): a pergunta do Nível 5 — o defeito está nos documentos ou numa ausência? — abre o diagnóstico
- `valida` **moderada** — [Verificação em Mente Fresca](../como-construir/verificacao-em-mente-fresca.md): as assinaturas de cada nível são o instrumento de leitura dos sinais internos

### Tensões
- Calibrar artefatos e rotular pessoas — os níveis medem a relação entre um autor e um insight, nunca quem escreve
