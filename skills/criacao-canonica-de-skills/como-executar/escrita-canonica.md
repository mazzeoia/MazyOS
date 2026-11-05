---
id: como-executar.escrita-canonica
nome: Escrita Canônica
tipo: mecanismo
camada: 4-operacional
status: ativo

essencia: >
  Declarar o estado final como a única verdade, sem comparação nem histórico;
  nasce da integração, não da edição, e deixa sinais verificáveis que permitem
  caçar as costuras.

em-uma-palavra: Integridade

certeza: estabelecido
maturidade: consolidado
origem: empírica
---
# Escrita Canônica

> A escrita canônica declara o estado final como a única verdade — sem comparação, sem histórico, sem um "antes". Ela nasce de um estado mental, não de uma técnica de edição; mas deixa sinais verificáveis, e as costuras têm palavras, formas e gêneros que se podem caçar.

---

## O princípio

O executor-alvo não tem memória de versões. Todo trecho comparativo instala nele um modelo fantasma — o estado anterior — que ele passa a ter de reconciliar com o estado descrito. Essa reconciliação é a costura: um ponto em que o agente recebe dois modos de pensar e precisa adivinhar qual vale, adivinhação que ele refaz de um jeito diferente a cada sessão.

Escrever canonicamente é escrever do lugar de quem só conhece o estado final. Por isso nenhuma técnica de edição produz escrita canônica: se você está disfarçando uma mudança, a mudança ainda não foi integrada, e o caminho é voltar à imersão e à meta-cognição, não refinar o disfarce. Mas, uma vez que o estado integrado existe, a técnica ajuda a verificar o resultado e a limpar os resíduos que escapam.

---

## A anatomia de uma costura

Costuras aparecem em três escalas.

**Palavras.** Em português: `anteriormente`, `antes era`, `não é mais`, `passou a ser`, `agora é`, `versão anterior`, `atualizado de`, `reformulado`, `correção`, `em vez do antigo`. Em inglês: `previously`, `used to`, `no longer`, `now is`, `updated from`, `reframed`, `correction`. Nem toda ocorrência é costura, mas toda ocorrência merece ser lida no contexto.

**Formas.** Tabelas de antes e depois; seções chamadas "mudanças", "o que mudou" ou "changelog"; notas entre parênteses sobre o nome antigo de algo; justificativas de por que uma regra substitui outra; avisos do tipo "isto substitui o que diz o documento X".

**Gêneros e arquivos.** Documentos nomeados `x-vs-y`, `novo-x`, `x-v2`; documentos de sobrescrita, que mandam ignorar o que outros documentos dizem; um `CHANGELOG` dentro do diretório da skill; um README que narra a evolução do projeto. O gênero de um documento diz ao agente como pesá-lo: um changelog é lido como história, e história pressupõe um estado anterior que continua valendo em algum lugar.

---

## Contraste legítimo e costura

Nem todo contraste é costura. Contrastar dois conceitos que coexistem no presente é conteúdo: documentação e substrato são coisas diferentes, e dizer isso ensina. Uma tabela que mostra o comportamento do agente com e sem um princípio é conteúdo. Uma narrativa sobre um acontecimento real do passado — um caso histórico, um incidente — é conteúdo, porque descreve o mundo, não uma versão da skill.

O teste é um só: *o contraste exige saber que este documento, ou esta skill, já foi diferente?* Se exige, é costura. Se compara alternativas que existem hoje no mundo, é legítimo.

---

## Como escrever em Nível 3

1. **Enuncie a verdade final numa frase.** Antes de escrever o documento, formule para si o que ele afirma, sem nenhuma referência a como era. Se a frase não sai sem o contraste, a integração não terminou — volte aos Movimentos 1 e 2.
2. **Escreva a partir da frase, não a partir do texto antigo.** Numa refatoração, não edite a frase velha palavra por palavra até ela virar a nova: escreva a frase nova a partir da verdade final e então substitua. Editar o velho em direção ao novo preserva o esqueleto do velho — e é no esqueleto que a costura mora.
3. **Declare, explique, mostre, prescreva.** É a ordem em que um princípio se torna habitável: o que ele afirma, por que é verdade, como aparece na prática, o que fazer.
4. **Releia como o executor-alvo.** Um parágrafo de cada vez, isolado do resto: faz sentido para quem nunca viu outra coisa? Pressupõe algum "como era"?
5. **Cace os resíduos.** Procure as palavras-sintoma — a auditoria mecânica faz isso — e leia cada ocorrência no contexto. Costura se reescreve; contraste legítimo fica.

---

## Voz e terminologia

A voz acompanha quem carrega o documento e para quê. Numa skill, dirigir-se diretamente ao agente — "você" — é legítimo e quase sempre o mais claro: princípios em forma declarativa, diretrizes em forma imperativa. Ficam de fora a voz motivacional, que pressupõe um leitor cansado, e o metacomentário sobre o próprio documento ("neste documento veremos"), que gasta a posição mais valiosa do texto anunciando o que viria nele.

A prosa carrega as razões, porque são elas que permitem ao agente generalizar. E cada conceito tem um nome só, em toda a skill. Sinônimos que num ensaio seriam elegância, numa skill são dois conceitos: o agente que encontra "raiz" num documento e "documento fundacional" em outro não tem como saber que se trata da mesma coisa.

---

## Onde mora a história

A trilha das decisões existe e precisa ser preservada — só não dentro do substrato. Ela mora no controle de versão (mensagens de commit, descrições de pull request), em registros de decisão fora do diretório da skill e no relato a quem pediu o trabalho. Ali a forma de Nível 2 é a correta. Dentro do diretório da skill, que é o que o executor-alvo carrega, só existe o estado final.

---

## O que muda

| Sem escrita canônica | Com escrita canônica |
|---|---|
| O agente recebe o estado descrito e o fantasma do anterior | O agente recebe um estado só |
| As decisões variam conforme o trecho que ele leu por último | As decisões se repetem de sessão em sessão |
| A skill acumula camadas de remendos a cada ajuste | Cada ajuste é absorvido e desaparece no texto |
| Revisar a skill exige conhecer a história dela | Revisar a skill exige apenas ler o que está escrito |

---

## Exemplo

**Contexto.** Uma skill de orquestração mede a qualidade de uma execução pela cobertura dos aspectos do problema.

**Escrita com costura:**

```text
Diferentemente do índice usado anteriormente, que media turnos por decisão,
a métrica correta passa a ser a cobertura.
```

**Escrita canônica:**

```text
A qualidade de uma execução se mede pela cobertura: aspectos analisados sobre
aspectos existentes. O alvo é cem por cento; abaixo disso, há pontos cegos.
```

**Diferença.** A primeira versão instala duas métricas, uma delas marcada como errada mas ainda descrita, e um conflito que o agente resolve a cada sessão. A segunda instala uma métrica só.

---

## Tensões e limites

**Canônico não é dogmático.** Limites, exceções e tensões fazem parte do estado final e são declarados como tal. Um princípio que deixa de valer em certas condições diz quais são essas condições — no presente, sem narrar como elas foram descobertas.

**Canônico não apaga incerteza.** Um princípio ainda em evolução é declarado com a sua certeza calibrada — pelo campo `certeza` e pela formulação —, e não com a história do debate que o produziu.

---

## Rede Sináptica

### Estruturais
- **Pai:** [Contexto de Execução e Axiomas](../contexto-de-execucao.md) — Axioma 3
- **Irmãos:** [Os Sete Movimentos](sete-movimentos.md), [Presença Direta](presenca-direta.md), [Divisão do Trabalho Cognitivo](divisao-do-trabalho-cognitivo.md)

### Semânticas
- `é-caso-especial-de` **forte** — [Contexto de Execução e Axiomas](../contexto-de-execucao.md): o Axioma 3 transformado em técnica de escrita e de verificação
- `pressupõe` **forte** — [Níveis de Profundidade Cognitiva](../como-pensar/niveis-de-profundidade-cognitiva.md): escrever em Nível 3 exige reconhecer em que nível se está
- `complementa` **forte** — [Os Sete Movimentos](sete-movimentos.md): é a forma do Movimento 4
- `complementa` **forte** — [Divisão do Trabalho Cognitivo](divisao-do-trabalho-cognitivo.md): a escrita canônica é exatamente o que não se delega

### Funcionais
- `habilita` **forte** — [Refatoração de Skills](../como-construir/refatoracao-de-skills.md): escrever a partir da verdade final é a técnica das edições cirúrgicas
- `habilita` **moderada** — [Da Fonte ao Substrato](../como-construir/da-fonte-ao-substrato.md): a troca de registro termina na escrita de cada documento a partir da verdade que ele carrega

### Tensões
- Escrita canônica e trilha de decisões — a trilha existe e é preservada, só que fora do diretório da skill
