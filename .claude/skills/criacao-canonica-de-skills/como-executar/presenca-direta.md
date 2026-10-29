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
# Presença Direta

> Durante a construção de uma skill, só conta como verdade o que foi observado diretamente na fonte: o arquivo lido, o comando executado, o caminho resolvido. Toda frase interna que começa com "provavelmente" é uma verificação que ainda não foi feita.

---

## O princípio

Construir uma skill é encadear dezenas de operações, e muitas delas falham em silêncio. A skill é especialmente vulnerável a isso porque o runtime que a carrega quase nunca reclama: um frontmatter malformado faz a skill simplesmente não aparecer; um link quebrado simplesmente não é seguido; uma `description` longa demais é truncada sem aviso e passa a ativar menos. As consequências só aparecem sessões depois, como comportamento estranho de um agente, longe da causa e sem pista dela.

Dois modos de falha alimentam esse problema. O primeiro é a **confiança no sucesso silencioso**: a operação não retornou erro, então se presume que fez o que devia. O segundo é a **suposição sobre o estado das ferramentas**: raciocinar sobre o que "deve ter acontecido" a partir de um modelo mental de como a ferramenta se comporta, em vez de olhar o que aconteceu. Os dois têm a mesma raiz — trocar a fonte por uma representação dela — e a mesma defesa.

---

## Onde moram as falhas silenciosas

**Nos arquivos.** Uma substituição em massa cujo padrão não casou com nada. Uma edição que casou com a ocorrência errada. Uma escrita num caminho ligeiramente diferente, que cria um arquivo novo ao lado do certo. Caracteres invisíveis — marca de ordem de bytes, espaços de largura zero — que o executor-alvo lê como tokens e que você não vê.

**Nos links e caminhos.** Um link relativo calculado a partir do diretório errado. Um arquivo renomeado com links antigos ainda apontando para ele. Uma diferença de maiúsculas e minúsculas que funciona num sistema de arquivos e quebra em outro.

**No runtime.** Um frontmatter que não começa na primeira linha do arquivo e por isso é ignorado. Um YAML inválido — dois-pontos sem aspas dentro de um valor, uma tabulação — que derruba a skill sem mensagem. Um `name` diferente do nome do diretório. Uma `description` além do limite. Um segundo `SKILL.md` aninhado, que faz a skill ser rejeitada no upload. O cache de um plugin servindo a cópia antiga até um recarregamento.

**No controle de versão.** Um arquivo coberto pelo `.gitignore`, que `git add` não adiciona e sobre o qual não reclama. Um arquivo novo esquecido fora do commit.

**Nos testes.** Uma opção de isolamento passada a uma sessão de teste e ignorada sem aviso: a sessão herda as permissões e as ferramentas do ambiente que a abriu e passa a agir sobre arquivos e sistemas reais enquanto parece rodar numa caixa de areia.

**Na delegação.** Um subagente que relata ter feito o que não fez, ou que fez em outro arquivo. Edições paralelas que se sobrescrevem.

---

## O que fazer

Verifique diretamente onde a falha é silenciosa e a consequência é estrutural. Os instrumentos são simples:

| Afirmação | Verificação direta |
|---|---|
| O arquivo ficou com o conteúdo certo | Ler o arquivo, ou o trecho, depois da operação |
| A substituição aconteceu em todos os lugares | Buscar o padrão antigo (o resultado esperado é zero) e o novo (o resultado esperado é o total previsto) |
| Os links funcionam | Resolver cada caminho — a auditoria mecânica faz isso para a skill inteira |
| O frontmatter é válido | Rodar a auditoria e o validador do runtime |
| O arquivo está no repositório | `git status` e `git ls-files` sobre o arquivo |
| A sessão de teste está isolada | O modo de permissão, as ferramentas e as integrações informados no evento de início da própria sessão |
| O subagente terminou o que relatou | `git diff --stat` e a leitura dos arquivos que ele diz ter alterado |
| A skill carrega | Uma sessão nova em que a skill aparece listada e é ativada |

"Provavelmente" é o gatilho. Sempre que esse advérbio aparecer no seu raciocínio sobre o estado de alguma coisa, pare: a hipótese vira um comando antes de virar uma decisão.

---

## Calibração

Esta é uma heurística, não um ritual. Nem toda operação pede reverificação: uma ferramenta que falha de forma ruidosa — um editor que devolve erro quando não encontra o trecho — já carrega a própria verificação, e reler o arquivo depois de cada edição bem-sucedida é cerimônia, não presença. A atenção vai para onde a falha é muda: operações em massa, substituições por shell, caminhos, arquivos gerados, trabalho delegado e tudo o que o runtime vai interpretar sem avisar se falhou.

A assimetria de custo sustenta a regra. Verificar diretamente é barato. Depurar uma falha silenciosa sessões depois é caro — e, numa skill, essa depuração tem a forma de um agente que se comporta mal sem que ninguém saiba por quê.

---

## Representações mediadas

Representação mediada é tudo o que está entre você e a fonte: a sua lembrança do que fez mais cedo na sessão; o resumo de um contexto compactado; o relatório de um subagente; uma métrica; a documentação de uma ferramenta, diante do comportamento real dela nesta máquina. Todas são hipóteses até serem conferidas na fonte. Vale até para a especificação do runtime: quando a documentação e o validador discordam, rode o validador e leia o erro.

Vale também para o pedido. O que quem pediu escreveu, nas palavras dele, é a fonte; a sua paráfrase do pedido é uma representação dela.

---

## O que muda

| Sem presença direta | Com presença direta |
|---|---|
| A skill parece funcionar até o dia em que um agente se comporta mal | A falha aparece no momento em que nasce |
| O autor raciocina sobre um estado imaginado | O autor raciocina sobre o estado real |
| Erros silenciosos se acumulam e se mascaram uns aos outros | Cada operação crítica deixa evidência |

---

## Exemplo

**Contexto.** O documento `principios.md` é renomeado para `axiomas.md`, e os links são atualizados com um comando de substituição sobre a skill inteira.

**Sem presença direta.** O comando roda sem erro e o trabalho segue. Dois documentos, porém, apontavam para `../principios.md`, forma que o padrão não cobria. Os links ficam quebrados, e o executor-alvo, ao seguir a rede, nunca chega à raiz.

**Com presença direta.** Depois da substituição, uma busca por `principios.md` na skill deve dar zero, e a auditoria deve acusar zero links quebrados. A busca acha duas ocorrências; elas são corrigidas antes do passo seguinte.

---

## Analogia

**O piloto e o indicador.** Um piloto não confia que os flapes baixaram porque puxou a alavanca: ele olha o indicador. Onde a analogia quebra: a cabine tem indicadores projetados para isso, e a maior parte das operações na construção de uma skill não tem nenhum. O indicador precisa ser criado na hora — uma busca, um comando, uma auditoria.

---

## Rede Sináptica

### Estruturais
- **Pai:** [Contexto de Execução e Axiomas](../contexto-de-execucao.md) — Axioma 5
- **Irmãos:** [Os Sete Movimentos](sete-movimentos.md), [Escrita Canônica](escrita-canonica.md), [Divisão do Trabalho Cognitivo](divisao-do-trabalho-cognitivo.md)

### Semânticas
- `é-caso-especial-de` **forte** — [Contexto de Execução e Axiomas](../contexto-de-execucao.md): o Axioma 5 calibrado como heurística de verificação
- `complementa` **forte** — [Divisão do Trabalho Cognitivo](divisao-do-trabalho-cognitivo.md): o relatório de um subagente é uma representação mediada
- `complementa` **moderada** — [Os Sete Movimentos](sete-movimentos.md): cada movimento tem operações cuja falha é silenciosa
- `complementa` **moderada** — [Verificação em Mente Fresca](../como-construir/verificacao-em-mente-fresca.md): a presença direta verifica durante a construção; a mente fresca, no fim

### Funcionais
- `habilita` **forte** — [Verificação em Mente Fresca](../como-construir/verificacao-em-mente-fresca.md): a auditoria mecânica é presença direta aplicada à skill inteira
- `mitiga` **moderada** — [Refatoração de Skills](../como-construir/refatoracao-de-skills.md): renomeações e substituições em massa são as operações mais silenciosas de uma refatoração

### Tensões
- Presença direta e ritual — reverificar o que já falha de forma ruidosa é cerimônia, não presença
