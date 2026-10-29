---
id: como-construir.verificacao-em-mente-fresca
nome: Verificação em Mente Fresca
tipo: ferramenta
camada: 7-prática
status: ativo

essencia: >
  A skill está pronta quando um agente que nunca a viu entra no modo pretendido;
  auditoria mecânica, sinais internos e uma sessão fresca real são os três
  instrumentos.

em-uma-palavra: Prova

certeza: consensual
maturidade: consolidado
origem: empírica
---
# Verificação em Mente Fresca

> A skill está pronta quando um agente que nunca a viu entra no modo pretendido ao carregá-la. A verificação combina três instrumentos — a auditoria mecânica do grafo e do frontmatter, a leitura dos sinais internos do texto e uma sessão fresca real diante de uma tarefa representativa — e termina só quando o entorno da skill emite os mesmos sinais que ela.

---

## O princípio

O autor é o pior leitor possível da própria skill. Ele lê cada frase com a conversa que a produziu na cabeça, preenche cada lacuna com o que sabe e não percebe as ambiguidades que só existem para quem chega sem contexto. O executor-alvo é exatamente quem chega sem contexto. A verificação, por isso, não pode consistir em reler: precisa simular — e, sempre que possível, executar — a chegada de alguém que nunca viu nada.

O teste definitivo é comportamental. Uma sessão nova do agente, sem histórico, carrega a skill e recebe uma tarefa representativa do domínio. O comportamento corresponde à intenção? As decisões refletem os axiomas? O resultado é nitidamente superior ao que sairia sem a skill? Se sim, a skill está canônica. Se não, a falha volta ao movimento em que nasceu.

---

## Instrumento 1 — Auditoria mecânica

O que é determinístico se verifica por script, sem custo de atenção e sem a falibilidade da leitura. O auditor fica em `scripts/auditar_skill.py`, relativo ao diretório desta skill — no Claude Code, `${CLAUDE_SKILL_DIR}/scripts/auditar_skill.py` —, usa só a biblioteca padrão do Python 3 e recebe como argumento o diretório da skill-alvo:

```bash
python3 scripts/auditar_skill.py caminho/da/skill-alvo
```

Ele confere o frontmatter do `SKILL.md` contra a especificação Agent Skills; o frontmatter canônico de cada documento e os vocabulários fechados; os links, que precisam resolver todos dentro da skill; os mínimos e máximos de conexões; a reciprocidade semântica e a consistência de força; o salto de camadas; os documentos fora do mapa do `SKILL.md`; as palavras-sintoma de costura e os nomes de arquivo com cara de versão; e os caracteres invisíveis. **Erros** reprovam a skill. **Avisos** pedem leitura no contexto: uma palavra-sintoma pode ser contraste legítimo, e o hub pode ser a raiz. Com `--estrito`, avisos também reprovam.

A auditoria mecânica garante a forma. Não garante que o conteúdo esteja em Nível 3, que a derivação axiomática seja real ou que o agente vá se comportar como se espera — para isso servem os outros dois instrumentos.

---

## Instrumento 2 — Sinais internos

São verificáveis no próprio material, por leitura atenta.

**Ausência de costuras.** Nenhum documento compara o que afirma com um estado que o executor-alvo nunca conheceu; o texto flui como se a verdade presente sempre tivesse sido a verdade.

**Derivabilidade axiomática.** Qualquer princípio de qualquer documento se rastreia até um axioma da raiz.

**Conectividade tipada.** Todo documento tem as conexões mínimas, e todo conceito importante aparece em mais de um contexto por meio delas.

**Densidade consistente.** Os documentos têm profundidade e rigor parecidos; nenhum é notavelmente mais raso ou mais rebuscado que os outros.

**Autossuficiência.** Cada documento é legível isoladamente por quem nunca viu a skill; nenhum depende de outro para fazer sentido básico.

O checklist arquitetural completa a leitura:

- **Camadas.** Há entrada, raiz com executor e axiomas explícitos, camada operacional e camada prática? A epistemológica existe ou sua ausência foi decidida? As condicionais — contratos, referência — foram decididas explicitamente?
- **Topologia.** Há conexões verticais, horizontais e diagonais? Nenhum documento é órfão ou hub? Nenhuma conexão vertical pula camadas?
- **Taxonomia.** Todo documento declara `tipo`, `certeza` e `maturidade`, e a distribuição faz sentido?
- **Derivação.** Os princípios das camadas de baixo derivam visivelmente dos de cima?
- **Cobertura.** Cada documento tem escopo único, os pares relacionados se complementam sem sobreposição destrutiva, e o conjunto cobre o espaço do problema?

---

## Instrumento 3 — A sessão fresca

**1. Mapear o caminho de entrada.** Descreva, passo a passo, o que um agente fresco encontra: a `description` na listagem de skills, a decisão de ativar, o `SKILL.md` inteiro, a raiz, os documentos que o mapa o leva a abrir. Em cada passo, pergunte que sinal ele recebe e se esse sinal é consistente com a intenção da skill.

**2. Conferir o entorno.** A skill nunca é lida sozinha. Leia o que o agente vai carregar junto: o `CLAUDE.md` ou `AGENTS.md` do projeto, o README, arquivos de configuração (`.env.example`, manifestos, `docker-compose`), outras skills instaladas com descrições sobrepostas — que disputam a mesma ativação. Qualquer sinal contraditório ali recria, vindo de fora, a incoerência eliminada dentro.

**3. Isolar a sessão de teste.** O agente fresco vai agir de verdade: uma tarefa representativa ("cria uma skill para…", "refatora a minha skill…") leva-o a escrever arquivos, e às vezes a procurá-los fora da pasta do teste. Uma sessão aberta a partir do ambiente do usuário herda as permissões, as ferramentas e as integrações desse ambiente, e pode alterar skills reais, configurações ou sistemas externos. Por isso a sessão de teste roda isolada: ferramentas reduzidas às de arquivo e à de ativação de skills, escrita confinada a um diretório descartável, nenhuma integração externa. E o isolamento se confirma na própria sessão — no evento de início, que informa modo de permissão e ferramentas —, antes de qualquer tarefa: uma opção de isolamento pedida pode ser ignorada em silêncio. O procedimento concreto para o Claude Code está em [Formato Agent Skills](../referencia/formato-agent-skills.md).

**4. Rodar o agente fresco.** Entregue a skill a um agente sem histórico — um subagente ou uma sessão nova, isolada — com duas tarefas: uma representativa do domínio, que deve ativar a skill, e uma vizinha, parecida na superfície, que não deve. Entregue a tarefa como um usuário a escreveria, sem as conclusões que você espera nem a sua hipótese sobre o resultado. Ativação é probabilística: uma amostra não mede taxa, e cada tarefa roda mais de uma vez.

**5. Observar os sinais externos.**
- **Ativação correta.** A skill é ativada na tarefa representativa e não na vizinha.
- **Invocação natural dos princípios.** O agente usa os axiomas no raciocínio sem ser lembrado deles.
- **Precisão epistêmica.** Trata fundamentos como firmes e heurísticas com julgamento, conforme o `tipo` e a `certeza`.
- **Navegação fluida.** Quando precisa de profundidade, segue a Rede Sináptica até o documento certo.
- **Comportamento replicável.** Duas sessões frescas com a mesma tarefa tomam decisões consistentes entre si.

**6. Corrigir na origem.** Cada ambiguidade encontrada volta ao movimento em que nasceu — quase sempre o 4, uma reconstrução incompleta, ou o 7, um sinal de contexto não alinhado — e é corrigida ali. Uma falha de substrato nunca se corrige com uma instrução acrescentada por cima.

---

## O que muda

| Verificação por releitura do autor | Verificação em mente fresca |
|---|---|
| O autor completa as lacunas sem perceber que elas existem | As lacunas aparecem como comportamento |
| A skill parece pronta porque o texto parece bom | A skill está pronta porque o agente se comporta como pretendido |
| Sinais contraditórios do entorno passam despercebidos | O entorno é lido junto, como o agente o lê |

---

## Analogia

**O teste de usabilidade com quem nunca viu o produto.** Um designer não descobre os defeitos da própria interface usando-a, porque já sabe onde cada botão está; descobre observando alguém que nunca a viu tentar cumprir uma tarefa. Onde a analogia quebra: o usuário de um teste de usabilidade pode dizer o que está pensando e, no mundo real, perguntar a alguém quando se perde. O executor-alvo, na sessão real, não pergunta nada à skill — decide e segue. Por isso o raciocínio do agente fresco, e não só o resultado, é o que se observa.

---

## Rede Sináptica

### Estruturais
- **Pai:** [Contexto de Execução e Axiomas](../contexto-de-execucao.md) — Axiomas 5 e 7
- **Irmãos:** [Arquitetura em Camadas](arquitetura-em-camadas.md), [Anatomia do Documento](anatomia-do-documento.md), [Rede Sináptica](rede-sinaptica.md), [Da Fonte ao Substrato](da-fonte-ao-substrato.md), [Refatoração de Skills](refatoracao-de-skills.md)

### Semânticas
- `é-caso-especial-de` **moderada** — [Contexto de Execução e Axiomas](../contexto-de-execucao.md): o Axioma 7 aplicado ao artefato — a skill é conferida pelas regras que ensina
- `complementa` **moderada** — [Presença Direta](../como-executar/presenca-direta.md): a mente fresca verifica no fim o que a presença direta verifica durante

### Funcionais
- `valida` **moderada** — [Arquitetura em Camadas](arquitetura-em-camadas.md): o checklist arquitetural confere camadas, topologia, taxonomia, derivação e cobertura
- `valida` **moderada** — [Rede Sináptica](rede-sinaptica.md): a auditoria confere reciprocidade, força, mínimos, máximos e links
