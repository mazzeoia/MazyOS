---
id: como-executar.divisao-do-trabalho-cognitivo
nome: Divisão do Trabalho Cognitivo
tipo: heurística
camada: 4-operacional
status: ativo

essencia: >
  Subagentes analisam; o autor lê e escreve. Catálogos, mapas, conferências e o
  teste de mente fresca se delegam; leitura profunda, escrita canônica e
  arquitetura, não.

em-uma-palavra: Delegação

certeza: consensual
maturidade: consolidado
origem: empírica
---
# Divisão do Trabalho Cognitivo

> Subagentes analisam; o autor lê e escreve. A leitura profunda e a escrita canônica não se delegam, porque a integração que elas exigem não atravessa um briefing. Catálogos exatos, mapas estruturais, verificações de consistência e o teste de mente fresca se delegam — e o último só funciona delegado.

---

## O princípio

Quando o ambiente oferece subagentes, delegar é uma ferramenta poderosa: perspectivas independentes, trabalho em paralelo, contextos livres dos vieses do autor. Mas a construção de uma skill canônica tem duas atividades em que a delegação destrói justamente o que está sendo construído — a leitura que absorve o material e a escrita que expressa o estado integrado.

O critério que separa uma coisa da outra é uma pergunta: *o resultado desta atividade depende de um estado integrado que só existe no meu contexto?* Se depende, ela não se delega. Se o resultado pode ser especificado como uma saída verificável que aponta de volta para a fonte, ela se delega.

---

## O que não se delega

### A leitura profunda

**Sintoma.** Diante de um corpo grande de material, o autor despacha subagentes para "ler tudo e devolver um resumo" e reconstrói a skill a partir dos resumos.

**Por que acontece.** Para um autor que é agente, a pressão não é cansaço — é a janela de contexto. Delegar a leitura parece poupá-la. Por baixo disso há uma confusão entre ter um resumo e ter o conteúdo.

**Por que falha.** A compressão remove exatamente a nuance sobre a qual a reconstrução trabalha: as contradições entre fontes, as condições de validade de cada princípio, os exemplos que revelam a premissa do executor original, as palavras exatas com que o usuário expressou a intenção. Um resumo é a leitura que outro agente fez do material, não o material.

**Defesa.** Ler pessoalmente, em lotes quando for preciso. A janela se administra sequenciando o trabalho — ler as fontes dos documentos que serão escritos agora, escrevê-los, ler o lote seguinte —, nunca terceirizando a compreensão.

### A escrita canônica

**Sintoma.** O autor fez a meta-cognição com o contexto inteiro e então instrui subagentes a "reescrever cada documento removendo as premissas X e Y". Os documentos voltam com costuras: `o princípio anterior afirmava X; entende-se agora que…`.

**Por que acontece.** Subagentes são bons executores, e paralelizar a escrita parece natural.

**Por que falha.** Escrever canonicamente não é seguir uma instrução; é expressar um estado mental. O subagente que não viveu a integração recebe a ordem de escrever sem costuras — e uma ordem de escrever sem costuras é, ela mesma, a descrição da costura. É como pedir a alguém que aja com naturalidade: o esforço para parecer natural é o que torna o gesto artificial. Um briefing mais refinado não resolve, porque o briefing carrega as conclusões da integração, não a integração.

**Defesa.** O Nível 3 é escrito pelo autor, documento por documento. Quando o volume é grande, o autor escreve em lotes ao longo de várias sessões, reentrando sempre pela raiz e pelas fontes.

### A arquitetura e a raiz

Decidir que documentos a skill terá, que axiomas a governam e quem é o executor-alvo exige a visão do sistema inteiro — o Nível 5 que enxerga a premissa compartilhada. Essa visão é, por definição, a do autor que absorveu tudo.

---

## O que se delega

A regra do delegável é esta: **a saída é verificável e ancorada na fonte — aponta para o material, não o substitui.**

**Catálogos exatos.** Um subagente analista lê cada documento linha a linha e devolve as ocorrências de um padrão definido — premissas de executor, palavras-sintoma de costura, termos inconsistentes — no formato arquivo, linha, trecho literal e razão. O catálogo não substitui a leitura do autor: é um índice para o trabalho cirúrgico, e cada item é conferido na fonte.

**Mapas estruturais.** Quem aponta para quem, que conceito aparece em quais documentos, onde a terminologia diverge.

**Verificações de consistência.** Depois da escrita, um subagente confere terminologia uniforme, links íntegros, ausência de costuras e densidade parecida entre documentos. A auditoria mecânica complementa esse trabalho.

**O teste de mente fresca.** É a única delegação obrigatória. Você não consegue desaprender o contexto: vai sempre ler a skill com a conversa que a produziu na cabeça. Um subagente sem histórico, ou uma sessão nova, é o mais perto do executor-alvo que você tem. Entregue a ele a skill e uma tarefa representativa — nunca as conclusões que você espera nem a sua hipótese, porque um agente que recebe a hipótese tende a devolvê-la confirmada.

---

## Como delegar bem

Diga ao subagente o formato exato da saída (arquivo, linha, trecho literal, razão), o escopo preciso e o que você já descartou. No teste de mente fresca, entregue a skill e a tarefa, e nada mais. E trate todo relatório como representação mediada: antes de agir sobre ele, confira na fonte o que ele afirma.

---

## Tabela de decisão

| Atividade | Delegável? | Por quê |
|---|---|---|
| Ler o material de origem para reconstruir | Não | A compressão destrói a nuance que a reconstrução usa |
| Escrever ou reescrever documentos canônicos | Não | Nível 3 é expressão de estado, não execução de instrução |
| Decidir a arquitetura, a raiz e o executor-alvo | Não | Exige a visão do sistema inteiro |
| Catalogar ocorrências de um padrão com arquivo e linha | Sim | Saída verificável que aponta para a fonte |
| Mapear o grafo de links e a terminologia | Sim | Saída verificável |
| Conferir consistência depois da escrita | Sim | É verificação, não autoria |
| Testar a skill numa mente fresca | Sim, obrigatoriamente | O autor nunca é um leitor fresco |

---

## Analogia

**O cirurgião e a equipe.** A equipe prepara os instrumentos, acompanha os sinais vitais, conta as compressas — tudo verificável, tudo delegável. A incisão não se delega a quem não examinou o paciente. Onde a analogia quebra: na cirurgia, a divisão segue competência e habilitação. Aqui, segue contexto: um subagente pode escrever tão bem quanto o autor; o que lhe falta é o estado integrado, não a habilidade.

---

## Tensões e limites

**Quando o ambiente impõe a delegação da escrita.** Há operações em que a redação, por regra de quem opera, é feita por agentes redatores. Nesse caso, o redator recebe o máximo do estado integrado que se consegue transmitir — a raiz, as próprias fontes e não um resumo delas, o lugar exato do documento na arquitetura — e cada entrega é revisada pelo autor contra o critério de Nível 3, com as costuras reescritas por ele. A delegação imposta muda quem digita; não muda quem responde pela integração.

---

## Rede Sináptica

### Estruturais
- **Pai:** [Contexto de Execução e Axiomas](../contexto-de-execucao.md) — Axioma 4
- **Irmãos:** [Os Sete Movimentos](sete-movimentos.md), [Escrita Canônica](escrita-canonica.md), [Presença Direta](presenca-direta.md)

### Semânticas
- `é-caso-especial-de` **forte** — [Contexto de Execução e Axiomas](../contexto-de-execucao.md): o Axioma 4 transformado em critério do que se delega
- `complementa` **forte** — [Escrita Canônica](escrita-canonica.md): a escrita canônica é o que não se delega
- `complementa` **forte** — [Presença Direta](presenca-direta.md): todo relatório delegado é conferido na fonte antes de virar decisão
- `complementa` **moderada** — [Os Sete Movimentos](sete-movimentos.md): define, em cada movimento, a parte do autor e a parte delegável

### Funcionais
- `habilita` **forte** — [Verificação em Mente Fresca](../como-construir/verificacao-em-mente-fresca.md): o teste de mente fresca só existe delegado a um agente sem histórico
- `restringe` **moderada** — [Da Fonte ao Substrato](../como-construir/da-fonte-ao-substrato.md): a leitura da fonte e a escrita dos documentos não saem das mãos do autor

### Tensões
- Escrita não delegável e ambiente que impõe redatores — a delegação imposta muda quem digita, não quem responde pela integração
