---
id: como-construir.refatoracao-de-skills
nome: Refatoração de Skills
tipo: mecanismo
camada: 7-prática
status: ativo

essencia: >
  Diagnóstico pelo comportamento, imersão na skill inteira, triagem de cada
  documento em quatro destinos e cirurgia escrita a partir da verdade final; os
  remendos se dissolvem ou viram raiz.

em-uma-palavra: Cirurgia

certeza: consensual
maturidade: consolidado
origem: empírica
---
# Refatoração de Skills

> Refatorar uma skill começa por localizar onde a premissa quebrou — quase sempre numa raiz ausente ou num remendo que compete com o texto que tentou corrigir — e termina em edições cirúrgicas: a maioria dos documentos fica intocada, poucos se reconstroem, e os remendos se dissolvem ou se transformam em raiz.

---

## O princípio

Uma skill que deixou de produzir o comportamento esperado raramente tem todos os documentos errados. O mais comum é outra coisa: os documentos estão desancorados, sem uma raiz que declare o executor; ou um remendo foi posto por cima e agora compete com o texto que tentou corrigir; ou uma premissa que servia a outro executor sobrevive espalhada em justificativas e exemplos.

Dois instintos atrapalham. Reescrever tudo é excesso de engenharia: destrói o que já estava em Nível 3 e abre risco novo de costura em cada parágrafo tocado. Acrescentar uma correção por cima é Nível 1 ou 2: instala uma segunda premissa ao lado da primeira. A refatoração é a sequência dos sete movimentos numa forma específica — diagnóstico, triagem, cirurgia.

---

## O mecanismo

### 1 — Partir do comportamento

A evidência é comportamental: o que o agente fez, o que se esperava, em que sessões, diante de que pedidos. Para cada falha, procure o documento — ou a ausência — que instala aquele comportamento. Leia com uma pergunta: *se eu fosse um agente com apenas este texto, faria o que o agente fez?* Se sim, o documento é a causa. Se nenhum documento explica o comportamento, a causa é uma ausência — premissa não declarada, anti-gatilho que falta, camada que falta — ou um sinal externo: o `CLAUDE.md`, o `AGENTS.md`, o README, outra skill com descrição sobreposta.

### 2 — Imergir na skill inteira

Leia todos os documentos, integralmente — não só os suspeitos. A premissa concorrente costuma morar no documento de que ninguém desconfia. Leia também as correções que o usuário fez e o histórico disponível. Um subagente pode catalogar, linha a linha, as ocorrências da premissa suspeita, com arquivo, linha, trecho e razão; o catálogo orienta a cirurgia, e a leitura continua sendo sua.

### 3 — Questionar o plano antes de executá-lo

Antes de reescrever qualquer coisa, faça a pergunta do Nível 5: o problema está nos documentos ou na ausência de algo? A resposta mais frequente é uma raiz ausente. Com uma raiz explícita — executor, objetivo, axiomas —, a maioria dos documentos se revela universal, e as mudanças necessárias ficam óbvias e poucas.

### 4 — Triar os documentos

Cada documento recebe um de quatro destinos.

- **Intocado.** Já está em Nível 3 e é coerente com a raiz. Não se mexe nele: reescrevê-lo só criaria risco de costura.
- **Refinamento.** O princípio vale, mas exemplos, limiares, enquadramento ou voz carregam a premissa do executor errado. Edições cirúrgicas nesses pontos.
- **Reconstrução.** O princípio precisa de fundamento novo, ou a métrica ou o procedimento dele não sobrevive. O documento é reescrito a partir da verdade final.
- **Dissolução ou transformação.** Documentos de remendo — sobrescritas, "nova abordagem", versões numeradas, tabelas comparativas — nunca ficam como estão. O conteúdo se dissolve nos documentos que eles tentavam corrigir; ou, quando o remendo tateava em direção a uma raiz que faltava, ele se transforma nela, reescrito como declaração e não como registro de mudança.

A triagem dos documentos é análoga à triagem dos princípios na refundamentação pelo executor: lá, cada princípio sobrevive igual, sobrevive com fundamento novo ou não sobrevive; aqui, cada documento fica intocado, se refina, se reconstrói ou se dissolve.

### 5 — Operar cirurgicamente

Em cada documento refinado ou reconstruído, escreva o trecho novo a partir da verdade final, sem editar a frase velha em direção à nova. Mude só o que a triagem indicou. Atualize a Rede Sináptica onde as mudanças alteram relações entre documentos.

### 6 — Caçar as costuras que a própria refatoração criou

A refatoração é o momento de maior risco de costura, porque o texto que você está substituindo continua vivo no seu contexto — e as costuras aparecem exatamente nos trechos editados. Depois das edições, rode a auditoria, leia cada trecho editado isolado do resto e confira a terminologia: uma refatoração introduz com facilidade um nome novo para um conceito que os outros documentos continuam chamando pelo nome de sempre.

### 7 — Verificar no comportamento

Repita os cenários de falha com um agente fresco e observe se o comportamento mudou. Repita também os cenários em que a skill já acertava: eles precisam continuar certos.

### 8 — Registrar a história fora da skill

A razão da refatoração vai para a mensagem de commit, para a descrição do pull request ou para um registro de decisão. O diretório da skill mostra só o estado final.

---

## Sintomas e onde procurar

| Sintoma no comportamento | Causa provável | Onde procurar |
|---|---|---|
| O agente oscila entre duas condutas | Duas premissas competindo | Documentos com regras incompatíveis; remendos |
| O agente age como um executor limitado — amostra, adia, prioriza por calendário | Premissa do executor original sobrevivendo | Justificativas, limiares e exemplos; raiz ausente |
| O agente aplica um princípio onde ele não cabe | Limites e anti-gatilhos ausentes | Tensões e limites; a seção de como o princípio aparece |
| A skill não é ativada quando deveria | `description` fraca ou sobreposta a outra | A `description`; as outras skills do ambiente |
| A skill é ativada quando não deveria | `description` sem anti-gatilhos | A `description` |
| O agente ignora documentos relevantes | Mapa incompleto, rede fraca, essências vagas | O `SKILL.md`, a Rede Sináptica, o frontmatter |
| O agente segue instruções externas que contradizem a skill | Sinal contraditório no entorno | `CLAUDE.md`, `AGENTS.md`, README, configurações |

---

## Exemplo

Uma skill de orquestração de agentes, com quinze documentos construídos a partir de princípios de engenharia de fábrica, faz o agente economizar turnos e priorizar tarefas por calendário. O primeiro impulso é criar um documento "nativo de IA", com tabelas que contrastam a conduta humana e a conduta do agente. A triagem mostra outra coisa. Os documentos epistemológicos — decomposição por porquês, separação entre fato e convenção — são universais e ficam intocados. Três documentos operacionais pedem refinamento nas justificativas: eliminar antes de otimizar continua valendo, agora para proteger o sinal e não o esforço. Quatro documentos práticos pedem reconstrução: a métrica de eficiência por turnos não sobrevive e dá lugar a métricas de cobertura e profundidade. E o documento comparativo não é mantido nem apagado: transforma-se na raiz que faltava — executor, objetivo, axiomas —, sem nenhuma tabela.

---

## Analogia

**A restauração de um prédio histórico.** O restaurador não demole para reconstruir nem passa massa nas rachaduras: diagnostica a estrutura, consolida a fundação, substitui só as partes comprometidas e preserva o que está são. Onde a analogia quebra: na restauração, a marca da intervenção costuma ser deliberadamente visível, para que se distinga o original do restaurado. Numa skill, a intervenção precisa ser invisível — o executor-alvo não pode saber que houve uma restauração.

---

## Tensões e limites

**Refatorar ou reconstruir do zero.** Quando a triagem manda a maioria dos documentos para reconstrução, ou quando o defeito está na própria decomposição — camadas ausentes, documentos organizados pelos capítulos da fonte —, cirurgia documento a documento não resolve. Nesse caso a skill é reconstruída pelo caminho da criação, a partir das fontes, aproveitando como material o que os documentos existentes têm de bom.

---

## Rede Sináptica

### Estruturais
- **Pai:** [Contexto de Execução e Axiomas](../contexto-de-execucao.md) — Axiomas 3 e 4
- **Irmãos:** [Arquitetura em Camadas](arquitetura-em-camadas.md), [Anatomia do Documento](anatomia-do-documento.md), [Rede Sináptica](rede-sinaptica.md), [Da Fonte ao Substrato](da-fonte-ao-substrato.md), [Verificação em Mente Fresca](verificacao-em-mente-fresca.md)

### Semânticas
- `é-caso-especial-de` **forte** — [Os Sete Movimentos](../como-executar/sete-movimentos.md): a sequência aplicada a uma skill que já opera, com o Movimento 4 em forma cirúrgica
- `é-análogo-a` **moderada** — [Refundamentação Pelo Executor](../como-pensar/refundamentacao-pelo-executor.md): a triagem dos documentos espelha a triagem dos princípios
- `contrasta-com` **moderada** — [Da Fonte ao Substrato](da-fonte-ao-substrato.md): a refatoração parte de um substrato que já opera; a criação, de material bruto

### Funcionais
- `contextualiza` **moderada** — [Verificação em Mente Fresca](verificacao-em-mente-fresca.md): os cenários de falha e os de acerto viram os testes da sessão fresca
