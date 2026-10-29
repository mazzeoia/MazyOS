---
id: como-construir.da-fonte-ao-substrato
nome: Da Fonte ao Substrato
tipo: mecanismo
camada: 7-prática
status: ativo

essencia: >
  Fonte vira skill por reconstrução, não por cópia nem resumo: inventário,
  executor declarado, redecomposição por momentos de decisão, troca de registro
  e escrita em Nível 3.

em-uma-palavra: Transformação

certeza: consensual
maturidade: em-evolução
origem: empírica
---
# Da Fonte ao Substrato

> Transformar um framework, um processo ou uma base de conhecimento em skill não é copiar nem resumir: é redecompor o material pelos momentos de decisão do executor-alvo, refundar cada princípio para esse executor e trocar o registro de "documento sobre" pelo registro de "modo de operar".

---

## O princípio

Quase toda skill nasce de algo que já existe: um framework escrito como ensaio, um playbook, um conjunto de notas, prompts que funcionam, o conhecimento tácito de um especialista expresso em conversa, um livro. Essa fonte foi organizada para ser lida — em geral por um humano, em geral em sequência — e escrita num registro próprio: descritivo, dirigido "ao leitor", dividido em capítulos.

A skill precisa ser organizada para ser carregada pelo executor-alvo e escrita no registro de quem opera. Copiar a fonte preserva a organização e o registro errados. Resumi-la destrói as razões, que são justamente o que permite ao agente generalizar. A transformação que funciona é uma reconstrução: o material é absorvido inteiro e reescrito a partir do lugar de quem vai usá-lo.

---

## As fontes

**Documentos estruturados** — frameworks, manuais, playbooks. São ricos em princípios, organizados por tema e quase sempre escritos para humanos.

**Conhecimento tácito** — o que quem pediu sabe e nunca escreveu. Aparece no pedido, nas correções, nos exemplos de resultado bom e ruim. Faz parte da imersão ler esses sinais como fonte, e faz parte da meta-cognição articular o que eles intuem.

**Prompts e instruções que já funcionam** — conhecimento operacional comprimido, quase sempre sem as razões. As razões precisam ser reconstruídas, ou o agente não saberá estender a instrução a um caso novo.

**Material de domínio** — livros, artigos, documentação técnica. Pede seleção pelo critério de relevância para as decisões do executor-alvo.

**Sessões anteriores** — o histórico do que funcionou e do que falhou quando o trabalho foi feito sem a skill.

---

## O mecanismo

### 1 — Absorver e inventariar

Leia a fonte inteira (Movimento 1). Durante a leitura, inventarie cada afirmação e classifique-a:

- **universal** — vale para qualquer executor;
- **amarrada ao executor original** — tem a premissa na justificativa, no exemplo, no limiar ou na voz, e vai para a triagem da refundamentação;
- **convenção do autor da fonte** — estilo ou preferência, que fica só se servir ao executor-alvo;
- **andaime do documento** — frases que existem só porque a fonte é um texto para leitura ("como vimos na seção 3", "este framework apresenta", "para quem é este documento"). Não migram.

Inventarie também as contradições entre fontes e as lacunas: o que o executor-alvo vai precisar e a fonte não diz.

### 2 — Declarar o executor-alvo e escrever a raiz

Quem carrega a skill, em que runtime, com que capacidades, para que tarefas (Movimentos 2 e 3). O "para quem" da fonte vira a declaração do executor-alvo na raiz — e quase nunca coincide com ela.

### 3 — Redecompor pelos momentos de decisão

Os capítulos da fonte dão lugar aos momentos de decisão do agente, conforme o procedimento de desenho em [Arquitetura em Camadas](arquitetura-em-camadas.md). Um conceito da fonte pode se dividir numa lente da camada epistemológica e numa conduta da camada operacional. Um catálogo de anti-padrões da fonte pode se distribuir: cada anti-padrão vai para o documento em que mora a sua defesa, e o `SKILL.md` guarda uma tabela compacta que aponta para eles. Uma seção da fonte que não serve a nenhuma decisão do agente fica de fora.

### 4 — Trocar o registro

| Registro da fonte | Registro do substrato |
|---|---|
| "Para quem: qualquer pessoa que…" | A declaração do executor-alvo, na raiz |
| "O autor deve…", "recomenda-se…" | "Você faz…" — imperativo direto ao agente |
| "Este documento apresenta…" | O documento afirma, sem se anunciar |
| "Como vimos na seção 3" | Um link tipado para o documento que contém o conceito |
| Exemplos do mundo do executor original | Exemplos do mundo do executor-alvo, preservadas as narrativas históricas que ensinam |
| Justificativas pela escassez do executor original | Fundamentos refundados — ou o princípio sai |

### 5 — Decidir o que vai para onde

- **`SKILL.md`** — o que precisa estar presente mesmo que o agente não abra mais nada: identidade, quando usar, os axiomas comprimidos, a sequência de trabalho, o mapa e o critério de término.
- **Documentos** — a profundidade sob demanda: razões, mecanismos, exemplos, analogias, limites.
- **Scripts** — tudo o que é determinístico e verificável mecanicamente: validar, contar, formatar, gerar. São executados, não carregados, e não custam contexto.
- **Fora da skill** — a história da fonte, a justificativa da própria transformação, o material tangencial, a bibliografia além do essencial. Uma linha de proveniência no README do repositório basta.

### 6 — Escrever em Nível 3 e conectar

O texto da fonte não é editado até virar a skill: cada documento é escrito a partir da verdade final que carrega, como descreve [Escrita Canônica](../como-executar/escrita-canonica.md). O que você acrescenta além da fonte — derivações, generalizações, resoluções de contradição — recebe `origem: derivada` e uma `certeza` honesta.

---

## Armadilhas

**Espelhar a estrutura da fonte.** Um documento por capítulo organiza para a leitura: o agente carrega capítulos de que não precisa e não encontra os momentos que a fonte não cobriu.

**Resumir.** Preserva as conclusões e perde as razões; o agente aplica a regra onde ela não cabe.

**Herdar o executor da fonte.** O "qualquer pessoa" da fonte, ou as suas premissas humanas, viram premissas do agente sem que ninguém as tenha declarado.

**Preservar o andaime.** "Neste framework", "como veremos adiante" — metatexto ocupando as posições mais valiosas.

**Copiar a inconsistência da fonte.** Fontes também se contradizem — um framework pode, numa frase, chamar de obrigatórias as três primeiras camadas de uma arquitetura e, na descrição de cada camada, marcar outra combinação. A skill resolve a contradição pela leitura que o resto da fonte sustenta e declara só a resolução.

**Inventar sem calibrar.** Acrescentar princípios que a fonte não sustenta sem marcar a origem e a certeza deles.

---

## Exemplo

Um framework de criação de skills, escrito como ensaio para qualquer leitor, com seções de axiomas, níveis de profundidade, movimentos, anti-padrões e mecanismos do transformer, vira uma skill assim: os axiomas vão para a raiz, rederivados para um autor que é agente; os níveis e os mecanismos viram lentes da camada epistemológica; os movimentos viram o mecanismo central da camada operacional; os anti-padrões não ficam juntos num catálogo — cada um vai para o documento em que mora a sua defesa, e o `SKILL.md` guarda a tabela que aponta para eles; e a justificativa que a fonte dava em tempo do autor ("o custo em tempo é real e deve ser aceito") é refundada para as limitações reais de um agente: a janela de contexto e a memória que não atravessa sessões.

---

## O que muda

| Fonte copiada para a skill | Fonte reconstruída como substrato |
|---|---|
| Organizada por capítulos | Organizada por momentos de decisão |
| Escrita para "qualquer pessoa" | Escrita para um executor-alvo declarado |
| Conclusões sem razões, ou razões soterradas em andaime | Razões em prosa onde o agente generaliza; conclusões compactas onde ele precisa lembrar |
| Premissas do executor original instaladas em silêncio | Premissas refundadas e centralizadas na raiz |

---

## Analogia

**O romance adaptado para roteiro.** O roteiro não copia os capítulos nem resume a trama: reconstrói a história para outro meio. O que o romance contava em monólogo interior vira ação e diálogo, porque a câmera não lê pensamentos. Onde a analogia quebra: o roteiro é lido por uma equipe inteira, que preenche as lacunas com o próprio ofício; a skill é lida por um agente sozinho, sem equipe para completar o que falta — tudo o que o filme precisa tem de estar na página.

---

## Rede Sináptica

### Estruturais
- **Pai:** [Contexto de Execução e Axiomas](../contexto-de-execucao.md) — Axiomas 1 e 4
- **Irmãos:** [Arquitetura em Camadas](arquitetura-em-camadas.md), [Anatomia do Documento](anatomia-do-documento.md), [Rede Sináptica](rede-sinaptica.md), [Refatoração de Skills](refatoracao-de-skills.md), [Verificação em Mente Fresca](verificacao-em-mente-fresca.md)

### Semânticas
- `é-caso-especial-de` **forte** — [Os Sete Movimentos](../como-executar/sete-movimentos.md): a sequência aplicada a material que ainda não é skill
- `contrasta-com` **moderada** — [Refatoração de Skills](refatoracao-de-skills.md): a criação parte de material bruto; a refatoração, de um substrato que já opera

### Funcionais
- `habilita` **moderada** — [Verificação em Mente Fresca](verificacao-em-mente-fresca.md): o inventário da fonte revela as tarefas representativas e as vizinhas do teste final
