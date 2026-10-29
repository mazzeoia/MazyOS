---
id: referencia.formato-agent-skills
nome: Formato Agent Skills
tipo: ferramenta
camada: 8-referência
status: ativo

essencia: >
  Regras de frontmatter, description como gatilho, divulgação progressiva,
  diretórios dos runtimes e distribuição que fazem a arquitetura canônica caber
  no padrão Agent Skills.

em-uma-palavra: Formato

certeza: estabelecido
maturidade: em-evolução
origem: empírica
---
# Formato Agent Skills

> O runtime só enxerga a `description` antes de ativar a skill e só carrega o `SKILL.md` ao ativá-la; os demais arquivos entram quando o agente decide abri-los. Este documento traz as regras de formato, descoberta e distribuição que fazem a arquitetura canônica funcionar dentro do padrão Agent Skills.

As regras abaixo foram conferidas na especificação de agentskills.io, na documentação do Claude Code e na documentação do instalador `npx skills` em outubro de 2026. Diante de um erro de validação, prevalecem a fonte oficial e o validador do runtime.

---

## Estrutura do diretório

```
nome-da-skill/
├── SKILL.md                  obrigatório: frontmatter + instruções
├── contexto-de-execucao.md   a raiz, quando é um documento próprio
├── como-pensar/              camadas em subdiretórios semânticos
├── como-executar/
├── como-.../
├── referencia/
└── scripts/                  executados, não carregados
```

Os nomes `references/`, `scripts/` e `assets/` que a especificação menciona são convenções, não exigências; qualquer estrutura é válida. A árvore tem um único `SKILL.md`: o upload para o claude.ai e para a API rejeita skills com um segundo `SKILL.md` aninhado.

---

## O frontmatter do `SKILL.md`

| Campo | Obrigatório | Regras |
|---|---|---|
| `name` | Sim | 1 a 64 caracteres; só letras minúsculas sem acento (`a`–`z`), dígitos e hífen; não começa nem termina com hífen; sem hífens consecutivos; idêntico ao nome do diretório |
| `description` | Sim | 1 a 1024 caracteres; diz o que a skill faz e quando usá-la; sem os caracteres `<` e `>`, que o validador da Anthropic rejeita |
| `license` | Não | Nome da licença ou referência ao arquivo de licença |
| `compatibility` | Não | Até 500 caracteres; requisitos de ambiente; a maioria das skills dispensa |
| `metadata` | Não | Mapa de chave para valor, ambos texto; é o lugar de qualquer campo extra |
| `allowed-tools` | Não | Experimental; ferramentas pré-aprovadas, separadas por espaço |

O frontmatter só é lido quando o `---` de abertura está na primeira linha do arquivo — sem linha em branco, sem marca de ordem de bytes antes. O YAML precisa ser válido: um valor que contém `: ` vai entre aspas ou num bloco dobrado (`>`).

O Claude Code aceita campos próprios além desses — `when_to_use`, `disable-model-invocation`, `user-invocable`, `argument-hint`, `context`, `agent`, `model`, `effort`, `paths`, `hooks`. Eles só cabem numa skill feita exclusivamente para o Claude Code e cujo comportamento os exija; o validador de empacotamento da Anthropic, usado para o upload no claude.ai e na API, recusa chaves fora da tabela acima. Os campos canônicos dos documentos — `id`, `tipo`, `camada`, `essencia` e os demais — não entram no frontmatter do `SKILL.md`.

---

## A `description` é o gatilho de ativação

A `description` entra na listagem de skills de toda sessão e é, junto com o `name`, tudo o que o agente vê da skill antes de decidir ativá-la. Ela cumpre, para a skill inteira, a função de gatilho de ativação, e por isso tem quatro partes:

1. **O que a skill faz**, em terceira pessoa, com o caso de uso principal primeiro. No Claude Code, `description` e `when_to_use` somadas são truncadas em 1.536 caracteres na listagem, e o que vem primeiro é o que sobrevive.
2. **Situações de ativação**, em forma afirmativa e abrangente — "use sempre que…", inclusive quando o pedido não nomeia a skill nem o tema dela com as palavras exatas.
3. **Sinais** — as palavras e expressões que o usuário usaria, inclusive em outra língua quando o público é misto.
4. **Anti-gatilhos** — as situações vizinhas em que a skill não deve ser ativada e, quando se sabe, o que usar no lugar.

Uma `description` vaga ("ajuda com skills") não ativa; uma ampla demais ativa no lugar errado e disputa espaço com outras skills instaladas.

Duas propriedades do runtime pesam na redação. A primeira: modelos tendem a subativar skills — a responder por conta própria quando a skill seria útil —, e é por isso que as situações de ativação são afirmativas. A segunda: quando há muitas skills instaladas, o Claude Code corta descrições para caber no orçamento da listagem (por padrão, 1% da janela de contexto), começando pelas skills menos usadas, e só o `name` aparece sempre. Uma skill recém-instalada, sem histórico de uso, é a primeira a perder a descrição. Daí duas regras: o `name` nomeia sozinho a função da skill, e o caso de uso principal ocupa a primeira frase da `description`. No ambiente do usuário, o orçamento sobe com a configuração `skillListingBudgetFraction`, e a skill pode sempre ser invocada pelo nome.

---

## Divulgação progressiva

1. **Metadados** (cerca de 100 tokens): `name` e `description` de todas as skills instaladas, carregados no início da sessão.
2. **Instruções** (recomendação de menos de 5.000 tokens e menos de 500 linhas): o corpo do `SKILL.md`, carregado na ativação e mantido no contexto pelo resto da sessão.
3. **Recursos** (sob demanda): os demais arquivos, lidos quando o agente decide; os scripts, executados.

Daí três regras. O `SKILL.md` carrega o núcleo que precisa estar presente mesmo que nada mais seja aberto. Todo documento é alcançável por um link direto a partir do `SKILL.md` — as referências ficam a um nível de profundidade, e a Rede Sináptica liga os documentos entre si sem substituir esse mapa. E todo caminho é relativo à raiz da skill.

---

## Scripts

Scripts são executados, não carregados: entregam verificação e transformação determinísticas sem custo de contexto. Devem ser autocontidos, ou declarar as dependências, e falhar com mensagens que digam o que fazer. O caminho é relativo ao diretório da skill; no Claude Code, `${CLAUDE_SKILL_DIR}` aponta para esse diretório, e `${CLAUDE_PLUGIN_ROOT}` aponta para a raiz do plugin quando a skill vem de um.

---

## Onde os runtimes procuram skills

Conforme a tabela de agentes do instalador `npx skills`:

| Runtime | Projeto | Global |
|---|---|---|
| Claude Code | `.claude/skills/` | `~/.claude/skills/` |
| Codex | `.agents/skills/` | `~/.agents/skills/` |
| Cursor | `.agents/skills/` | `~/.cursor/skills/` |
| OpenCode | `.agents/skills/` | `~/.config/opencode/skills/` |
| Gemini CLI | `.agents/skills/` | `~/.gemini/skills/` |
| GitHub Copilot | `.agents/skills/` | `~/.copilot/skills/` |

Cada skill ocupa um subdiretório com o próprio nome dentro desses diretórios.

---

## Testar uma skill numa sessão isolada

No Claude Code, a sessão fresca do teste roda a partir de um diretório temporário, que é o único lugar em que ela pode escrever:

```bash
cd "$(mktemp -d)"
env -u CLAUDECODE -u CLAUDE_CODE_CHILD_SESSION -u CLAUDE_CODE_SESSION_ATTENDED \
  claude -p "tarefa representativa, escrita como um usuário a escreveria" \
  --plugin-dir caminho/do/plugin \
  --restricted --strict-mcp-config \
  --tools "Read,Write,Edit,Glob,Grep,Skill" \
  --permission-mode acceptEdits \
  --output-format stream-json --verbose < /dev/null
```

- `--plugin-dir` carrega a skill em teste sem instalá-la. Um `.claude/skills/` de outra pasta, passado com `--add-dir`, põe na mesma sessão as skills concorrentes que disputam a ativação.
- `--restricted` ignora os arquivos de configuração do usuário, remove as ferramentas que executam comandos, confina as ferramentas de arquivo aos diretórios de trabalho e recusa o modo que dispensa permissões; `--strict-mcp-config` deixa a sessão sem nenhum servidor MCP.
- Uma sessão aberta de dentro de outra sessão do Claude Code herda variáveis de ambiente dela (`CLAUDECODE`, `CLAUDE_CODE_CHILD_SESSION` e afins); o `env -u` as remove.
- O primeiro evento da saída (`type: system`, `subtype: init`) informa `permissionMode`, `tools`, `mcp_servers` e `skills`. O teste só vale depois de conferidos esses campos.
- A ativação aparece como um evento `tool_use` de nome `Skill`, com o nome da skill em `input.skill`.
- Para medir a `description` sem o corte da listagem, a variável `SLASH_COMMAND_TOOL_CHAR_BUDGET` eleva o orçamento; sem ela, o teste mede o comportamento num ambiente com muitas skills.

---

## Distribuição

**Repositório como plugin e marketplace do Claude Code.** O repositório tem `.claude-plugin/plugin.json` (`name`, `version`, `description`, `author`, `license`), `.claude-plugin/marketplace.json` (`name`, `owner` e `plugins`, cada entrada com `name` e `source` — `"./"` quando o plugin é a própria raiz do repositório) e as skills em `skills/<nome>/SKILL.md`. O `name` da entrada no marketplace é igual ao `name` do `plugin.json`. A instalação é `/plugin marketplace add dono/repositorio` seguida de `/plugin install plugin@marketplace`, e a skill passa a ser invocada como `/plugin:skill`. A validação é `claude plugin validate .` na raiz do repositório.

**Instalador universal.** `npx skills add dono/repositorio` descobre as skills em `skills/<nome>/SKILL.md` e nos manifestos de plugin, detecta os agentes instalados e copia para cada um; `-g` instala globalmente, e `--skill nome` escolhe uma skill específica.

**claude.ai.** Upload de um zip da pasta da skill, com um único `SKILL.md`.

**Cópia direta.** A pasta da skill copiada para o diretório do runtime, conforme a tabela acima.

---

## Checklist de formato

- O `SKILL.md` começa com `---` na primeira linha.
- `name` é igual ao nome do diretório e usa só caracteres válidos.
- `description` tem até 1024 caracteres, sem `<` nem `>`, e cobre o que a skill faz, as situações, os sinais e os anti-gatilhos.
- O frontmatter usa só os campos da especificação, com extras dentro de `metadata`, se a skill vai para o claude.ai ou para a API.
- O `SKILL.md` tem menos de 500 linhas.
- Todo documento é alcançável por link direto a partir do `SKILL.md`.
- Todos os caminhos são relativos, e nenhum link aponta para fora da skill.
- Existe um único `SKILL.md` na árvore.
- Os scripts funcionam a partir de qualquer diretório, recebendo os caminhos como argumento.

---

## Rede Sináptica

### Estruturais
- **Pai:** [Contexto de Execução e Axiomas](../contexto-de-execucao.md) — Axioma 6
- **Irmãos:** [Vocabulário Tipado](vocabulario-tipado.md)

### Semânticas
- `é-análogo-a` **moderada** — [Atenção do Transformer](../como-pensar/atencao-do-transformer.md): a divulgação progressiva faz com os arquivos o que a atenção faz com o contexto
- `complementa` **moderada** — [Arquitetura em Camadas](../como-construir/arquitetura-em-camadas.md): o formato do runtime é a forma concreta da camada de entrada

### Funcionais
- `restringe` **forte** — [Anatomia do Documento](../como-construir/anatomia-do-documento.md): o frontmatter do `SKILL.md` segue a especificação, não a anatomia canônica
