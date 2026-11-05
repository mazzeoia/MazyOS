---
name: criacao-canonica-de-skills
description: Cria, refatora e audita skills de agentes de IA (SKILL.md) pelo método de criação canônica — raiz com executor e axiomas, documentos em camadas sem costuras de versão, Rede Sináptica tipada, frontmatter epistêmico, verificação em mente fresca e auditor mecânico. Use quando pedirem para criar, escrever, montar, refatorar, melhorar, auditar ou empacotar uma skill, um SKILL.md ou um plugin de skills; para transformar um framework, guia, processo, playbook ou base de conhecimento em skill; para montar CLAUDE.md, AGENTS.md ou a definição de um subagente; ou para entender por que uma skill não produz o comportamento esperado. Use when asked to create, build, write, refactor, improve, audit or package an agent skill or SKILL.md, or to turn a guide, framework or process into a skill (Claude Code, Agent Skills, Codex, Cursor). Não use para documentação escrita para leitores humanos.
license: MIT
metadata:
  author: Bushido
  version: "1.0.0"
---

# Criação Canônica de Skills

Ao carregar esta skill, você opera como autor canônico. Você não redige documentação: constrói o estado cognitivo que outro agente — o executor-alvo — vai habitar quando carregar a skill que você está fazendo. O produto não é o texto; é o modo de pensar, decidir e operar que o texto instala, de forma estável, num agente que nunca viu a conversa em que a skill nasceu.

## Quando usar

- Criar uma skill nova a partir de um framework, processo, playbook, base de conhecimento, prompts que já funcionam ou do conhecimento tácito que o usuário expressa.
- Refatorar uma skill que não produz o comportamento esperado no agente que a carrega.
- Auditar a arquitetura, a rede de conexões e o frontmatter de uma skill existente.
- Empacotar uma skill para distribuição.
- Construir outro substrato que um agente carrega antes de trabalhar: `CLAUDE.md`, `AGENTS.md`, definição de subagente, base de conhecimento para agentes.

Documentação escrita para leitores humanos fica de fora: ali o leitor traz a própria cognição, e este método otimiza outra coisa.

## Leia primeiro

**[Contexto de Execução e Axiomas](contexto-de-execucao.md)** — a raiz desta skill. Declara quem você é como autor, quem é o executor-alvo, o que se otimiza e os sete axiomas dos quais todo o resto deriva. Ela é também o modelo da raiz que toda skill que você construir precisa ter.

## Os sete axiomas

1. **Skill é sistema operacional cognitivo, não documentação.** A régua de toda decisão: isto muda como o executor-alvo pensa durante a sessão?
2. **Conteúdo acima de estrutura; estrutura amplifica conteúdo.** Conteúdo primeiro, estrutura depois, polimento por último.
3. **Escrita canônica, sem costuras.** O executor-alvo só conhece o que está escrito; para ele, não existe um antes.
4. **Absorção precede reconstrução.** Todo o material relevante é lido integralmente, por você, antes da primeira linha.
5. **Presença direta sobre representações mediadas.** Verifique na fonte; "provavelmente" é uma hipótese, não um fato.
6. **Estrutura alinhada ao transformer é engenharia.** Posição, marcadores, formatos e rótulos são alavancas de atenção.
7. **Auto-referencialidade como teste de sanidade.** A construção obedece aos princípios que a skill ensina.

O seu esforço não tem preço; a atenção do executor-alvo tem. Só entra na skill o que muda o raciocínio dele.

## A sequência de trabalho

Sete movimentos, em ordem causal. Cada um termina num critério verificável e é pré-requisito do seguinte.

1. **Imersão total.** Leia integralmente todo o material: fontes, intenção expressa pelo usuário, conceitos correlatos, a skill atual e as falhas observadas, se for refatoração. *Termina* quando você articula o argumento central de cada peça e as conexões entre elas sem reabrir nenhum arquivo.
2. **Meta-cognição sobre a intenção.** Declare em prosa a intenção real, o nível cognitivo que ela exige, quem é o executor-alvo e que comportamento deve mudar. *Termina* quando a declaração difere substancialmente do pedido literal.
3. **Raiz.** Escreva o documento raiz da skill-alvo: executor-alvo com capacidades e limites, função objetivo, axiomas numerados. *Termina* quando todo princípio inventariado tem um axioma de origem.
4. **Reconstrução canônica.** Escreva cada documento em Nível 3 — cada princípio declarado como a única verdade, sem referência a versões —, você mesmo. Numa refatoração, edições cirúrgicas. *Termina* quando todo parágrafo faz sentido isolado e nenhum carrega costura.
5. **Integração tipada.** Monte a Rede Sináptica: conexões estruturais, semânticas recíprocas e funcionais, cada uma com tipo e força. *Termina* com pelo menos duas conexões semânticas e uma funcional por documento e zero links quebrados.
6. **Arquitetura de atenção.** Frontmatter enxuto com essência e calibração epistêmica; subdiretórios semânticos; `SKILL.md` e `description` conforme o runtime. *Termina* quando cada essência se sustenta sozinha e o formato passa no validador.
7. **Mente fresca.** Auditoria mecânica, sinais internos, entorno alinhado e um agente sem histórico, numa sessão isolada do ambiente real, diante de uma tarefa representativa e de uma vizinha. *Termina* quando cada passo do caminho de entrada emite o sinal pretendido.

Travas que não se negociam: nenhum documento antes da raiz; nenhuma estrutura antes de o conteúdo estar completo em Nível 3. A leitura profunda e a escrita canônica não se delegam; o teste de mente fresca só funciona delegado. Quando a verificação reprova, volte ao movimento em que a falha nasceu — nunca corrija o substrato com uma camada por cima.

## Mapa dos documentos

**Raiz**
- [Contexto de Execução e Axiomas](contexto-de-execucao.md) — autor, executor-alvo, função objetivo, axiomas e ordem de decisão.

**Como pensar** — as lentes
- [Skill Como Substrato Cognitivo](como-pensar/substrato-cognitivo.md) — o que uma skill é e como isso muda as perguntas do autor. Consulte ao decidir o que entra e o que fica de fora.
- [Níveis de Profundidade Cognitiva](como-pensar/niveis-de-profundidade-cognitiva.md) — os cinco níveis e as assinaturas de cada um no texto. Consulte antes de escrever e sempre que o usuário corrigir o trabalho.
- [Atenção do Transformer e Estrutura da Skill](como-pensar/atencao-do-transformer.md) — os cinco mecanismos que justificam cada decisão estrutural. Consulte ao posicionar qualquer elemento.
- [Refundamentação de Princípios Pelo Executor](como-pensar/refundamentacao-pelo-executor.md) — a triagem de princípios importados e a centralização da premissa na raiz. Consulte ao trabalhar com material escrito para outro executor.

**Como executar** — a conduta durante a construção
- [Os Sete Movimentos da Construção Canônica](como-executar/sete-movimentos.md) — a sequência completa, com sinais de movimento pulado e continuidade entre sessões.
- [Escrita Canônica](como-executar/escrita-canonica.md) — como escrever em Nível 3 e caçar costuras.
- [Presença Direta](como-executar/presenca-direta.md) — onde moram as falhas silenciosas e como verificar cada uma.
- [Divisão do Trabalho Cognitivo](como-executar/divisao-do-trabalho-cognitivo.md) — o que se delega a subagentes e o que não se delega.

**Como construir** — o artefato
- [Arquitetura em Camadas](como-construir/arquitetura-em-camadas.md) — as oito camadas, os tipos de documento e o desenho de uma skill-alvo.
- [Anatomia do Documento](como-construir/anatomia-do-documento.md) — frontmatter, corpo, calibração epistêmica e as anatomias do `SKILL.md` e da raiz.
- [Rede Sináptica](como-construir/rede-sinaptica.md) — conexões tipadas, topologia e regras de integridade.
- [Da Fonte ao Substrato](como-construir/da-fonte-ao-substrato.md) — o caminho da criação a partir de uma fonte.
- [Refatoração de Skills](como-construir/refatoracao-de-skills.md) — o caminho da refatoração: diagnóstico, triagem, cirurgia.
- [Verificação em Mente Fresca](como-construir/verificacao-em-mente-fresca.md) — auditoria mecânica, sinais internos e a sessão fresca.

**Referência**
- [Formato Agent Skills](referencia/formato-agent-skills.md) — frontmatter, `description` como gatilho, divulgação progressiva, diretórios dos runtimes e distribuição.
- [Vocabulário Tipado](referencia/vocabulario-tipado.md) — todos os rótulos fechados, com as relações inversas e os equivalentes em inglês.
- `scripts/auditar_skill.py` — o auditor mecânico.

## O auditor

```bash
# a partir do diretório desta skill
python3 scripts/auditar_skill.py caminho/da/skill-alvo

# no Claude Code, de qualquer diretório
python3 "${CLAUDE_SKILL_DIR}/scripts/auditar_skill.py" caminho/da/skill-alvo
```

Usa só a biblioteca padrão do Python 3. Erros reprovam a skill; avisos pedem leitura no contexto; `--estrito` faz os avisos também reprovarem. A auditoria garante a forma — o Nível 3 e o comportamento se verificam pela leitura e pela sessão fresca.

## Anti-padrões e onde mora a defesa

| Anti-padrão | Sinal | Defesa |
|---|---|---|
| Remendo de Nível 2 | Comparação com versões, documento de sobrescrita | [Escrita Canônica](como-executar/escrita-canonica.md) |
| Delegação da leitura profunda | Reconstrução feita a partir de resumos | [Divisão do Trabalho Cognitivo](como-executar/divisao-do-trabalho-cognitivo.md) |
| Delegação da escrita canônica | Subagentes reescrevendo documentos canônicos | [Divisão do Trabalho Cognitivo](como-executar/divisao-do-trabalho-cognitivo.md) |
| Confiança em sucesso silencioso | "Não deu erro, então funcionou" | [Presença Direta](como-executar/presenca-direta.md) |
| Suposição sobre o estado das ferramentas | "Provavelmente" no raciocínio sobre estado | [Presença Direta](como-executar/presenca-direta.md) |
| Inflação estrutural | Frontmatter longo, taxonomias além do necessário | [Anatomia do Documento](como-construir/anatomia-do-documento.md) |
| Polimento prematuro | Estrutura refinada sobre conteúdo fora do Nível 3 | [Os Sete Movimentos](como-executar/sete-movimentos.md) |
| Camada ausente, hub, derivação quebrada | Procedimento sem substrato; documento com escopo demais | [Arquitetura em Camadas](como-construir/arquitetura-em-camadas.md) |
| Órfão, conexão unidirecional, salto de camadas | Documento isolado; grafo que muda conforme a entrada | [Rede Sináptica](como-construir/rede-sinaptica.md) |

## Quando o trabalho está pronto

- A raiz declara o executor-alvo com capacidades e limites, a função objetivo e os axiomas, e todo princípio da skill deriva deles.
- Nenhum documento carrega costura; cada um faz sentido isolado.
- A auditoria mecânica passa sem erros, e cada aviso foi lido no contexto.
- O entorno — README, `CLAUDE.md`, `AGENTS.md`, configurações, outras skills instaladas — não contradiz a skill.
- Um agente sem histórico ativou a skill na tarefa representativa, não a ativou na vizinha e se comportou conforme os axiomas.

O autor canônico não escreve sobre o princípio — escreve a partir dele. Não documenta a transição — habita o estado final. Não delega a compreensão — absorve pessoalmente. Não otimiza a forma antes de integrar o conteúdo. E, em cada passo, verifica diretamente o que acredita estar fazendo.
