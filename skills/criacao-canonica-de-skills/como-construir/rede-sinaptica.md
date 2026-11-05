---
id: como-construir.rede-sinaptica
nome: Rede Sináptica
tipo: padrão
camada: 7-prática
status: ativo

essencia: >
  Conexões tipadas com força declarada, em três categorias e três direções,
  semântica sempre recíproca e grafo fechado, fazem de cada link uma instrução
  para o raciocínio seguinte.

em-uma-palavra: Conexão

certeza: consensual
maturidade: consolidado
origem: derivada
---
# Rede Sináptica

> Conexões tipadas transformam a skill de uma pilha de documentos num grafo navegável: cada link diz ao agente se deve usar dois documentos juntos, entender um antes do outro ou tratar um como caso particular do outro. Três categorias, três direções, força declarada, semântica sempre recíproca, grafo fechado.

---

## O princípio

Um link sem tipo diz apenas que existe alguma relação. O agente não consegue saber se deve abrir o destino agora, depois ou nunca. Um link tipado é uma instrução para o raciocínio que vem a seguir: `é-pré-requisito-de` diz "entenda isto primeiro"; `habilita` diz "isto torna aquilo possível"; `é-caso-especial-de` diz "aquele é a regra geral, este é uma instância dela". A rede fica no fim de cada documento — posição de recência — exatamente onde o agente decide o que ler em seguida.

---

## As três categorias

**Estruturais.** A posição do documento na arquitetura: o pai (a raiz, ou o documento que abre a camada), os irmãos (documentos da mesma camada) e os filhos, quando existem. Servem ao movimento de zoom — subir para o contexto, descer para o detalhe — e não precisam de tipo, porque a própria posição os define.

**Semânticas.** Relações de significado entre conceitos: o mesmo fenômeno visto de ângulos diferentes, uma especialização, uma generalização, uma oposição, um pré-requisito. São recíprocas por princípio.

**Funcionais.** Relações de uso conjunto: conceitos que, na prática, são necessários ao mesmo tempo. São direcionais — "A habilita B" não implica "B habilita A".

---

## O formato

```markdown
## Rede Sináptica

### Estruturais
- **Pai:** [Contexto de Execução e Axiomas](../contexto-de-execucao.md) — Axioma 5
- **Irmãos:** [Os Sete Movimentos](sete-movimentos.md), [Escrita Canônica](escrita-canonica.md), [Divisão do Trabalho Cognitivo](divisao-do-trabalho-cognitivo.md)

### Semânticas
- `complementa` **forte** — [Divisão do Trabalho Cognitivo](divisao-do-trabalho-cognitivo.md): o relatório de um subagente é uma representação mediada

### Funcionais
- `habilita` **forte** — [Verificação em Mente Fresca](../como-construir/verificacao-em-mente-fresca.md): a auditoria mecânica é presença direta aplicada à skill inteira

### Tensões
- Presença direta e ritual — reverificar o que já falha de forma ruidosa é cerimônia, não presença
```

O exemplo é um recorte da rede de [Presença Direta](../como-executar/presenca-direta.md). Cada linha tipada tem a relação em código, a força em negrito, o link com o nome do destino e, depois dos dois-pontos, a razão em uma frase. A razão é o que transforma o link num caminho de raciocínio. A subseção de tensões é opcional e registra os conceitos com que o documento entra em conflito.

---

## A força

| Força | Critério | Comportamento esperado do agente |
|---|---|---|
| **forte** | Impossível entender ou usar um sem o outro | Ativar sempre junto |
| **moderada** | Frequentemente úteis juntos | Ativar quando o contexto sugerir |
| **sutil** | Ilumina, mas não é essencial | Ativar só em exploração profunda |

---

## As relações

**Semânticas — sempre com recíproca no destino:**

| Relação | Recíproca no destino | Significado |
|---|---|---|
| `complementa` | `complementa` | Juntos formam um quadro mais completo |
| `contrasta-com` | `contrasta-com` | Opostos que se iluminam mutuamente |
| `é-análogo-a` | `é-análogo-a` | O mesmo padrão em domínios diferentes |
| `é-caso-especial-de` | `é-generalização-de` | Instância de um conceito mais geral |
| `é-pré-requisito-de` | `pressupõe` | Precisa ser entendido antes |
| `evolui-para` | `é-evolução-de` | Forma mais desenvolvida do mesmo conceito |

**Funcionais — registradas na direção em que valem:**

| Papel | Significado |
|---|---|
| `habilita` | Este conceito torna o outro possível |
| `restringe` | Este conceito limita o outro |
| `valida` | Este conceito serve para verificar o outro |
| `amplifica` | Este conceito potencializa o efeito do outro |
| `mitiga` | Este conceito reduz os riscos do outro |
| `contextualiza` | Este conceito dá significado ao outro |

Uma skill usa só o subconjunto de que precisa — de três a cinco relações semânticas e de três a cinco papéis funcionais. Os predicados se parecem com os de ontologias formais de propósito: o modelo os processa com competência que já tem. O vocabulário completo, com os equivalentes em inglês para skills escritas nessa língua, está em [Vocabulário Tipado](../referencia/vocabulario-tipado.md).

---

## A topologia: três direções

**Vertical — entre camadas.** Do abstrato ao concreto: um princípio epistemológico habilita uma conduta operacional, que se materializa num padrão prático. É como a skill mantém a coerência derivativa. Relações típicas: `habilita`, `contextualiza`, `é-caso-especial-de`.

**Horizontal — dentro da mesma camada.** Princípios do mesmo nível de abstração que se completam, se tensionam ou se especializam. Relações típicas: `complementa`, `contrasta-com`, `é-caso-especial-de`.

**Diagonal — atravessando camadas e tipos.** Documentos de contextos aparentemente distantes que compartilham uma estrutura. São as conexões mais ricas, porque permitem ao agente levar um insight de um contexto para outro. Relações típicas: `é-análogo-a`, `é-generalização-de`.

Só conexões verticais produzem uma árvore rígida, sem riqueza lateral. Só horizontais produzem camadas desconectadas, sem coerência derivativa. Só diagonais produzem um grafo caótico, sem hierarquia navegável. A skill canônica tem as três: um grafo dirigido com hierarquia nítida, conexões laterais densas e pontes de isomorfismo ocasionais.

Nesta skill, por exemplo, a refundamentação pelo executor `habilita` o caminho da fonte ao substrato (vertical); a escrita canônica `complementa` a divisão do trabalho cognitivo (horizontal); e a atenção do transformer `é-análogo-a` o formato Agent Skills (diagonal) — o runtime aplica aos arquivos a mesma economia que a atenção aplica dentro do contexto: o que está no topo pesa mais, o resto entra sob demanda.

---

## As regras de integridade

1. **Reciprocidade semântica.** Toda conexão semântica registrada em A apontando para B está registrada também em B apontando para A — com a mesma relação, se ela é simétrica, ou com a inversa, se é assimétrica.
2. **Direcionalidade funcional.** Uma conexão funcional é registrada na direção em que vale. A recíproca não é implícita e só é registrada se valer por conta própria.
3. **Consistência de força.** Se A marca a conexão com B como forte, B marca a conexão com A como forte ou moderada, nunca como sutil. Uma diferença de dois níveis revela avaliação inconsistente.
4. **Mínimos.** Todo documento, exceto a raiz, tem pai; todo documento tem pelo menos duas conexões semânticas e uma funcional. Um documento que não alcança esses mínimos está na camada errada, é redundante ou não pertence à skill.
5. **Máximo.** Mais de quinze conexões tipadas num documento indicam um hub, de escopo amplo demais. A raiz é a exceção, porque é ancestral de tudo.
6. **Grafo fechado.** Todo link resolve para um arquivo existente dentro da skill. Destinos fora dela — outros repositórios, notas pessoais, caminhos da máquina do autor — não existem no mundo do executor-alvo.
7. **Sem salto de camadas.** Conexões verticais não pulam a mediação das camadas intermediárias: um documento de prática se conecta a pelo menos um documento epistemológico ou operacional, e não só à raiz.
8. **Anti-gatilho recíproco.** Quando dois conceitos costumam ser confundidos, os dois documentos registram a confusão e apontam um para o outro: "se você chegou aqui por causa de X, o documento certo é Y".

---

## Anti-padrões da rede

**Documento órfão.** Menos de duas conexões semânticas ou nenhuma funcional. Ou está na camada errada, ou é conhecimento tangencial importado sem integração, ou é redundante com outro documento mais bem conectado. A correção é integrá-lo, movê-lo ou eliminá-lo.

**Conexão unidirecional.** O grafo muda conforme o documento por onde o agente entra, e o comportamento muda com ele.

**Salto de camadas.** Um axioma aplicado diretamente a um caso concreto, sem os princípios intermediários. O raciocínio que resulta pula níveis e perde robustez fora do caso previsto. A correção é criar a ponte que falta nas camadas 3 e 4.

**"Veja também".** Uma lista de links sem tipo e sem razão — o sinal mais fraco possível, ocupando a posição mais valiosa do documento.

---

## O que fazer

Construa a rede depois que o conteúdo de todos os documentos estiver em Nível 3. Para cada documento: registre o pai e os irmãos; escolha as conexões semânticas perguntando *qual é a relação de significado?* e as funcionais perguntando *quando uso este conceito, de que outro eu preciso?*; escreva a razão de cada uma; depois vá a cada destino e registre a recíproca semântica. Ao fim, rode a auditoria mecânica, que confere reciprocidade, força, mínimos, máximos e links.

---

## Analogia

**O mapa do metrô.** Linhas são camadas, estações são documentos, baldeações são as conexões diagonais que levam de uma linha a outra. O mapa funciona porque cada estação diz claramente para onde se pode ir dali. Onde a analogia quebra: o passageiro enxerga o mapa inteiro e escolhe a rota com os olhos; o agente só enxerga a estação em que está e a lista de saídas dela. Por isso cada saída precisa dizer, na própria placa, por que tomá-la — e é para isso que serve a razão escrita depois de cada link.

---

## Rede Sináptica

### Estruturais
- **Pai:** [Contexto de Execução e Axiomas](../contexto-de-execucao.md) — Axioma 6
- **Irmãos:** [Arquitetura em Camadas](arquitetura-em-camadas.md), [Anatomia do Documento](anatomia-do-documento.md), [Da Fonte ao Substrato](da-fonte-ao-substrato.md), [Refatoração de Skills](refatoracao-de-skills.md), [Verificação em Mente Fresca](verificacao-em-mente-fresca.md)

### Semânticas
- `pressupõe` **moderada** — [Atenção do Transformer](../como-pensar/atencao-do-transformer.md): rótulos tipados, predicados conhecidos e posição final exploram os mecanismos 1, 2 e 3
- `complementa` **forte** — [Arquitetura em Camadas](arquitetura-em-camadas.md): a rede dá os caminhos entre as camadas que a arquitetura define
- `complementa` **forte** — [Anatomia do Documento](anatomia-do-documento.md): a rede fecha a anatomia de cada documento
- `complementa` **forte** — [Vocabulário Tipado](../referencia/vocabulario-tipado.md): este documento explica o uso das relações; aquele fecha os rótulos e as inversas

### Funcionais
- `habilita` **moderada** — [Verificação em Mente Fresca](verificacao-em-mente-fresca.md): as regras de integridade são o que a auditoria mecânica confere
