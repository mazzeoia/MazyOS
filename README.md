# MazyOS: o sistema operacional do seu negócio no Claude Code

> Plugin do Claude Code, em português. Memória da sua empresa, identidade
> visual e 17 skills de marketing, SEO, Google Ads e prospecção de clientes.
> Você dirige, o Claude trabalha.

Você instala uma vez. Depois, em qualquer pasta que seja o seu negócio, o
Claude já começa a conversa sabendo quem você é, como você fala e o que
importa essa semana. Pede um carrossel, ele sai na sua identidade. Pede
leads, ele busca no Google Maps e monta o site de prévia. Pede o relatório
dos anúncios, ele lê o CSV e te mostra onde o dinheiro tá vazando.

Bora voar.

---

## O que é o MazyOS

O Claude Code é a ferramenta da Anthropic que roda o Claude dentro do seu
computador, numa pasta sua. O MazyOS é um plugin pra ele: um pacote de
skills (roteiros que o Claude segue) mais um mod (um pedaço de código que
muda o próprio Claude Code enquanto você trabalha).

Juntos, eles transformam o Claude num agente de IA que conhece o seu
negócio. Na prática:

**Ele lembra.** Três arquivos de texto em `_memoria/` guardam quem é a
empresa, o tom de voz e o foco atual. Toda sessão começa com eles no
contexto. Quando você corrige algo ("não escreve assim", "esse cliente
saiu"), o Claude pergunta se quer salvar, e salva no lugar certo.

**Ele tem a sua cara.** `identidade/design-guide.md` guarda cores, fontes e
logo. Carrossel, proposta, slide: tudo sai com a marca.

**Ele faz o trabalho repetitivo.** 17 skills prontas, e um jeito de criar as
suas: você conta o que repete toda semana e o Claude transforma em skill.

Não precisa saber programar. Precisa saber responder perguntas sobre o seu
negócio.

---

## Como instalar o MazyOS no Claude Code

Abre o Claude Code em qualquer pasta e cola:

```
/plugin install mazyos --marketplace mazzeoia/MazyOS
```

Ele pergunta se pode adicionar o marketplace (`y`) e em qual escopo.
Escolhe `user`, que vale pra todas as suas pastas. Depois aparecem três
opções (painel, linha de status, freio no git). Pode deixar tudo ligado;
dá pra mudar no `/config` quando quiser.

Prefere o terminal? Dá no mesmo:

```bash
claude plugin install mazyos --marketplace mazzeoia/MazyOS
```

No app do Claude pra desktop, onde o `/plugin` não existe: clica no `+`
do lado da caixa de texto, depois Plugins, Add marketplace com
`mazzeoia/MazyOS`, e Add plugin.

Ainda não tem o Claude Code? É da Anthropic, instala pelo site
([code.claude.com](https://code.claude.com)), funciona no Mac, Windows e
Linux, e precisa de um plano pago do Claude (Pro, Max, Team) ou de uma
chave da API.

---

## Ligando o sistema na sua empresa

Cria uma pasta com o nome do seu negócio (ou usa uma que já existe), abre
o Claude Code nela e roda:

```
/mazyos:instalar
```

Ele monta a estrutura (`_memoria/`, `identidade/`, `marketing/`,
`saidas/`, `dados/`, `scripts/`) e faz uma entrevista de uns cinco
minutos: o que você vende, pra quem, como você escreve, qual o gargalo de
hoje, quais as cores da marca. Você só responde. No fim, a memória tá
preenchida e o sistema te conhece.

Roda uma vez só. Depois é abrir o Claude na pasta e pedir as coisas.

---

## O que muda no Claude Code com o MazyOS

Essa é a parte do mod. Dentro de uma pasta do MazyOS:

- **A memória entra sozinha.** Empresa, preferências e estratégia vão pro
  contexto como instruções do projeto, do lado do `CLAUDE.md`. Mudou o
  arquivo, o Claude recebe a versão nova. Ninguém precisa pedir pra ler.
- **As regras vêm junto.** Ler a memória antes de responder, perguntar
  antes de salvar uma correção, avisar quando o contexto mudou, sugerir
  skill pra tarefa que se repete. Tudo isso entra em toda sessão, direto
  do plugin, sem depender de um arquivo que você pode apagar sem querer.
- **Painel do lado do chat.** Mostra o negócio, o foco, o tom, quais
  arquivos de memória estão preenchidos e quando foram atualizados, e
  botões de atalho: abrir sessão, atualizar memória, salvar no GitHub.
  Abre sozinho em terminal largo. `/mazyos` abre a qualquer hora.
- **Linha de status.** `MazyOS · Acme · foco: fechar 3 clientes` fica
  embaixo do prompt, pra você não perder o fio.
- **Aviso quando a memória muda.** O Claude editou `estrategia.md`? O
  painel e o status atualizam na hora, e aparece um aviso.
- **Freio no git.** `git push --force`, `git reset --hard` e parentes só
  rodam depois que você confirma. Se não tiver como perguntar, não roda.

Fora de uma pasta do MazyOS, o plugin fica quieto. Só avisa uma vez, por
pasta, que o `/mazyos:instalar` existe.

---

## As skills

São 17 skills do Claude Code, prontas pra usar. Digita `/mazyos:` e a
lista aparece.

### Pra tocar o dia a dia

- `/mazyos:abrir` resume o contexto em cinco linhas e pergunta o que vamos fazer.
- `/mazyos:salvar` faz commit e push no GitHub, até pra quem nunca usou git.
- `/mazyos:atualizar` compara a memória com o que tá na pasta e propõe o que atualizar.
- `/mazyos:novo-projeto` cria uma pasta isolada pra cada cliente ou iniciativa, com contexto próprio.
- `/mazyos:mapear-rotinas` pergunta o que você repete toda semana e cria uma skill pra cada coisa.
- `/mazyos:criacao-canonica-de-skills` cria, refatora e audita skills com um método mais profundo.

### Conteúdo e SEO

- `/mazyos:carrossel` cria carrossel pro Instagram (1080×1350) na identidade da marca, com ou sem foto gerada por IA, e já deixa a legenda pronta.
- `/mazyos:publicar-tema` pega um tema e entrega artigo de blog, carrossel e três legendas (Instagram, Facebook, LinkedIn), tudo amarrado.
- `/mazyos:seo` roda o fluxo de SEO em 8 passos: demanda, concorrência, Google Meu Negócio, on-page, conteúdo, Google Ads, monitoramento e GEO (aparecer no ChatGPT, Gemini e Perplexity).
- `/mazyos:responder-avaliacoes` escreve respostas humanas pras avaliações do Google.
- `/mazyos:aprovar-post` publica blog, Instagram e Facebook num comando só.

### Google Ads e Meta Ads

- `/mazyos:anuncio-google` monta a campanha inteira num CSV pronto pra importar no Google Ads Editor.
- `/mazyos:relatorio-ads` lê os exports do Google Ads e do Meta Ads e devolve o relatório da semana, com alertas e o que fazer.

### Prospecção de clientes

- `/mazyos:prospecta-maps` parte de um nicho e uma cidade, busca as empresas no Google Maps, confere o CNPJ na Receita, monta um site de prévia pra cada lead e deixa a primeira mensagem e os follow-ups prontos. A proposta em PDF sai quando você pedir. Sem chave de API.

### Produção

- `/mazyos:analisar-dados` lê CSV, planilha ou PDF e devolve um resumo executivo.
- `/mazyos:email-profissional` rascunha um email a partir do que você contar.

As skills que você criar pro seu negócio ficam em `.claude/skills/` da sua
pasta, fora do plugin, e você chama como `/<nome>`.

---

## Perguntas que sempre aparecem

**O MazyOS é grátis?** O plugin é aberto e gratuito. O que você paga é o
Claude Code: plano Pro, Max ou Team do Claude, ou a API da Anthropic.

**Precisa saber programar?** Não. Você conversa em português e responde
perguntas sobre o seu negócio. Os comandos são uma barra e um nome.

**Funciona no Windows?** Sim. Mac, Windows e Linux, no terminal, no VS
Code ou no app do Claude.

**Onde ficam os meus dados?** Na sua pasta, no seu computador. Memória,
identidade e tudo que o sistema gera são arquivos de texto seus, que você
pode abrir, editar e versionar no GitHub. O plugin é só leitura e se
atualiza pelo `/plugin`.

**O que é um plugin do Claude Code?** Um pacote que adiciona skills,
comandos e comportamento ao Claude Code, instalado com uma linha. O MazyOS
é um deles.

**Dá pra ver o que o plugin faz no meu Claude?** Dá, é tudo código aberto
aqui. `hooks/sistema.ts` tem as regras que entram no contexto;
`hooks/register.tsx` tem o mod.

**Eu usava o MazyOS clonando este repositório. E agora?** Instala o plugin
e, na pasta do negócio: apaga `.claude/skills/` (as skills vêm do plugin;
as que você criou podem ficar), tira do `CLAUDE.md` as regras gerais do
MazyOS (o plugin já injeta todas) e troca `/abrir` por `/mazyos:abrir` no
hábito. Memória, identidade e saídas ficam como estão.

---

## A tese

IA não é uma ferramenta que a sua empresa usa. É o sistema operacional em
que ela roda.

A diferença não é velocidade. É capacidade nova: uma pessoa com IA constrói
o que antes exigia um time inteiro. Cada processo que hoje roda em malha
aberta (decide, executa, não mede, repete cego) vira malha fechada dentro
do MazyOS (decide, executa, captura, realimenta, ajusta sozinho).

O sistema não substitui você. Vira parte da sua empresa.

---

## Pra quem quer mexer no código

Este repositório é o plugin e o marketplace ao mesmo tempo.

```
.claude-plugin/   plugin.json e marketplace.json
hooks/            register.tsx (o mod), memoria.ts (lê o workspace), sistema.ts (as regras)
types/            contrato do estado do mod
tests/            testes do mod
skills/           as 17 skills
templates/        perfis de CLAUDE.md, catálogos e o esqueleto do workspace
```

```bash
claude plugin validate .     # manifesto, marketplace e hooks
claude plugin test .         # testes do mod
claude --plugin-dir .        # numa pasta de negócio, carrega este checkout
```

---

[mazyos.com.br](https://mazyos.com.br)
