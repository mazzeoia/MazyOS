---
name: instalar
description: >
  Instala o MazyOS na pasta do negócio do usuário. Cria o esqueleto do workspace
  (`_memoria/`, `identidade/`, `marketing/`, `saidas/`, `dados/`, `scripts/`) a partir
  dos templates do plugin quando ele ainda não existe, entrevista sobre empresa, tom de
  voz, foco atual e identidade visual, e preenche `_memoria/empresa.md`,
  `_memoria/preferencias.md`, `_memoria/estrategia.md`, `identidade/design-guide.md`
  e o `CLAUDE.md` do negócio conforme o perfil. Use quando o usuário acabou de instalar
  o plugin e quer ligar o sistema numa pasta, ou quando pedir "rodar /mazyos:instalar",
  "instalar o MazyOS", "primeiro setup", "liga o MazyOS aqui".
---

# /mazyos:instalar — Instalação inicial do MazyOS

Esse é o primeiro comando que o usuário roda depois de instalar o plugin. Não pode falhar e não pode soar burocrático. Trata como conversa de descoberta — pergunta uma coisa por vez, escuta de verdade, não enfileira tudo. O objetivo é o sistema sair daqui sabendo quem é a empresa, como ela fala, e onde tá o atrito do dia a dia.

A pasta do plugin é `${CLAUDE_PLUGIN_ROOT}`. Os templates ficam em `${CLAUDE_PLUGIN_ROOT}/templates/`.

## Pré-checagem

### 1. Esqueleto do workspace

Conferir se existe `_memoria/` na pasta atual. Se não existir, copiar o esqueleto que vem com o plugin, sem sobrescrever nada que já exista:

Mac / Linux:
```bash
cp -Rn "${CLAUDE_PLUGIN_ROOT}/templates/workspace/." .
```

Windows (PowerShell ou cmd):
```powershell
robocopy "${CLAUDE_PLUGIN_ROOT}\templates\workspace" . /E /XC /XN /XO
```

Isso cria `_memoria/` (empresa, preferências, estratégia), `identidade/` (design-guide), `marketing/`, `saidas/`, `dados/` e `scripts/` (cada uma com seu README) e um `.gitignore` que protege chaves e dados de terceiros.

Se a pasta atual for claramente um projeto de código já existente (tem `package.json`, `src/`, `.git` de outro projeto com muitos arquivos), avisar antes de copiar:
> "Essa pasta parece ser um projeto de código. O MazyOS cria pastas de memória e saída aqui dentro. Quer instalar nessa pasta mesmo ou prefere criar uma pasta só pro negócio?"

### 2. Nome da pasta

Conferir o nome da pasta atual (`basename "$(pwd)"`). Se for `mazyos`, `MazyOS`, `MazyOS-main`, `mazyos-main`, `negocio`, `novo`, `teste` ou outro nome genérico:

> "Notei que a pasta atual ainda tem nome genérico ('<nome-atual>'). O ideal é a pasta ter o nome do seu negócio. Quando terminarmos o setup, te lembro de renomear (é rápido — fechar o editor, renomear a pasta no Finder/Explorer, abrir de novo). Bora seguir?"

Registrar mentalmente o nome atual pra usar na Fase 5.

### 3. Arquivos de contexto

Conferir se algum arquivo de memória já está preenchido (não é placeholder):
- `_memoria/empresa.md`
- `_memoria/preferencias.md`
- `_memoria/estrategia.md`
- `identidade/design-guide.md`

Se algum já tiver conteúdo real, perguntar:
> "Já tem algum contexto preenchido aqui. Quer que eu sobrescreva (recomeçar do zero) ou complemente o que falta?"

Se for setup limpo, seguir direto.

---

## Fase 1 — Escolha do perfil

Perguntar qual perfil mais combina com o negócio:

1. **Solopreneur / criador solo** — uma pessoa só, mistura de marca pessoal e negócio
2. **Freelancer** — atende clientes, organiza por projeto/cliente
3. **Agência / consultoria** — equipe pequena entregando pra vários clientes
4. **Empresa** — empresa estabelecida com setores (marketing, comercial, financeiro, etc.)

A resposta determina qual template de `CLAUDE.md` aplicar (ver `${CLAUDE_PLUGIN_ROOT}/templates/perfis/`).

---

## Fase 2 — Entrevista

Fazer essas perguntas em ordem, esperando a resposta de cada uma antes de seguir. Se vier resposta vaga, repetir uma vez pedindo concretude. Não insistir mais que isso — registrar o que vier.

**Sobre o negócio:**
1. "Como você chama o que você faz? (nome da empresa, ou seu nome se for marca pessoal)"
2. "O que sua empresa entrega, em uma frase do jeito que você falaria pro vizinho?"
3. "Quem te paga? (perfil de cliente real — descreve em uma ou duas frases, sem persona genérica)"
4. "Você toca sozinho ou tem equipe? Se tem, quantos e cada um fazendo o quê?"

**Sobre voz:**
5. "Me cola um exemplo da tua escrita — uma legenda do Insta, um email pra cliente, qualquer coisa real e recente. Assim eu calibro o jeito de escrever sem precisar adivinhar."
6. "O que te dá ranço quando alguém escreve assim? (ex: 'vamos juntos!', emoji em email formal, 'caro cliente', jargão de guru, 'alavancar', 'sinergia')"

**Sobre foco:**
7. "Qual o gargalo do teu negócio hoje? O que tá segurando ele de crescer?"
8. "Se eu pudesse tirar UMA coisa que você repete toda semana das tuas costas, qual seria?"

**Sobre identidade visual:**
9. "Tem identidade visual definida ou tá no zero? Se tem, me passa as cores principais e a fonte."
10. "Tem logo? Se sim, joga o arquivo em `identidade/logo.png` (ou `.svg`) e me confirma."

---

## Fase 3 — Preenchimento dos arquivos

Manter os campos em negrito dos templates (`**Nome:**`, `**O que faz:**`, `## Prioridade principal`, `## Tom de voz`): o painel do MazyOS lê esses campos pra mostrar o negócio, o foco e o tom.

### `_memoria/empresa.md`
Preencher com base nas perguntas 1-4. Manter formato simples — nome, o que faz, perfil de cliente, equipe.

### `_memoria/preferencias.md`
Preencher com base nas perguntas 5-6. Estrutura:
- **Tom de voz:** derivar do exemplo de escrita real da pergunta 5 (descrever em 2-3 frases o jeito de escrever, com referência ao exemplo)
- **O que evitar:** lista direta da resposta 6
- **Estilo geral:** síntese do que combina e o que destoa

### `_memoria/estrategia.md`
Preencher com base nas perguntas 7-8. Estrutura:
- **Prioridade principal:** o que ataca o gargalo direto (uma frase)
- **Gargalo atual:** [resposta da 7]
- **Pra tirar das costas:** [resposta da 8] — registrar como candidata a virar skill via `/mazyos:mapear-rotinas`

### `identidade/design-guide.md`
Se o usuário forneceu cores/fontes/logo (perguntas 9-10), preencher os campos correspondentes. Se não, deixar como está e avisar:
> "Deixei o `identidade/design-guide.md` em branco. Sempre que você definir uma identidade visual, edita lá — as skills de carrossel, proposta e slide leem esse arquivo antes de criar qualquer visual."

### `CLAUDE.md`
Pegar o template correspondente ao perfil escolhido na Fase 1 (`${CLAUDE_PLUGIN_ROOT}/templates/perfis/claude-md-<perfil>.md`), adaptar com o nome do negócio e a estrutura de pastas mencionada nas respostas, e gravar como `CLAUDE.md` na raiz do workspace. Se já existir um `CLAUDE.md` com conteúdo real, perguntar antes de sobrescrever.

As regras gerais do MazyOS (ler a memória, aprender com correções, manter o contexto, criar skills) já vêm do plugin e entram em toda sessão. O `CLAUDE.md` do negócio guarda só o que é específico dele: estrutura de pastas, clientes, regras do dia a dia.

---

## Fase 4 — Resumo

Mostrar pro usuário o que foi configurado:

```
✓ Workspace criado em: [pasta]
✓ Perfil aplicado: [perfil]
✓ Contexto do negócio: _memoria/empresa.md
✓ Tom de voz: _memoria/preferencias.md
✓ Foco atual: _memoria/estrategia.md
✓ Marca: identidade/design-guide.md  [preenchida | em branco — preencher depois]
✓ CLAUDE.md do negócio adaptado pro perfil [perfil]
```

---

## Fase 5 — Renomear pasta (se necessário)

Se a pasta atual ainda tem nome genérico (detectado na Pré-checagem), gerar slug do nome da empresa (resposta da pergunta 1):
- minúsculas
- sem acentos
- espaços viram hífen
- caracteres especiais removidos

Ex: "Acme Empresa Ltda" → `acme-empresa-ltda`

Mostrar:

> "Última coisa: a pasta ainda tá com nome genérico ('<nome-atual>').
> Pra ter cara do seu negócio, recomendo renomear pra '<slug>'.
>
> Como fazer:
> 1. Fecha o editor
> 2. Renomeia a pasta no Finder (Mac) ou Explorer (Windows) — ou no
>    terminal fora dela: `mv <nome-atual> <slug>`
> 3. Abre o editor de novo na pasta renomeada
>
> Se preferir outro nome, me fala que eu ajusto a sugestão."

Se a pasta já tem nome próprio (não genérico), pular essa fase.

---

## Fase 6 — Próximos passos

> "Pronto. O MazyOS já te conhece.
>
> A partir de agora a memória do negócio entra sozinha em toda sessão
> aberta nessa pasta. Se quiser um resumo rápido antes de começar o dia,
> roda `/mazyos:abrir`. O painel ao lado do chat (`/mazyos`) mostra o
> estado da memória e os atalhos.
>
> Quando quiser fazer um carrossel, plano de SEO, campanha ou qualquer
> outra coisa, é só chamar a skill que cabe: digita `/mazyos:` e escolhe.
>
> Você mencionou que repete '<resposta da pergunta 8>' toda semana.
> Quando quiser tirar isso das costas de vez, roda `/mazyos:mapear-rotinas`
> que eu transformo em skill própria."

Se o usuário quiser publicar o trabalho no GitHub, mencionar `/mazyos:salvar`.

---

## Regras

- Não inventar dados — se a resposta for vaga, registrar do jeito que veio (ou deixar placeholder claro)
- Não escrever "este arquivo será preenchido pelo /mazyos:instalar" nos arquivos finais — esse aviso só existe nos placeholders, sai depois da instalação
- O setup deve durar 5-7 minutos no máximo. Se o usuário estiver enrolando numa pergunta, registra o que tem e segue
- Não fazer perguntas extras além das listadas acima sem motivo claro
- Nunca escrever dentro de `${CLAUDE_PLUGIN_ROOT}`: é a pasta do plugin, substituída a cada atualização
