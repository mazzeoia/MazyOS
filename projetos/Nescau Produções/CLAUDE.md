# Nescau Produções — Site institucional

> Projeto criado em 01/08/2026. Pasta dedicada — instruções aqui
> sobrescrevem as da raiz quando relevantes.

## Sobre

Criar o site institucional novo da Nescau Produções, substituindo o site
atual (nescauproducoes.com.br) — vitrine do casting de artistas de
samba/pagode, história da produtora, serviços (booking, gestão de
carreira) e canal de contato pra contratantes (festivais, eventos
corporativos, festas particulares).

## Tipo

Projeto interno (a Nescau Produções é o próprio negócio registrado na
raiz do MazyOS, não um cliente externo).

## Entregas previstas

- Site institucional (Astro, deploy Netlify)

## Onde salvar o que

- Briefing e contexto coletado: `briefing.md`, nessa pasta
- Entrega: `site/astro-site/`

## Contexto que herda do MazyOS

Esse projeto herda automaticamente o tom de voz, marca e contexto do
negócio definidos em `C:/Users/Pichau/MazyOS/_memoria/` e
`C:/Users/Pichau/MazyOS/identidade/` — porque a Nescau Produções é a
própria empresa registrada na raiz (perfil: agência/consultoria), não uma
iniciativa separada como a Synapse. Não duplicar essas informações aqui.

## Específico desse projeto

- Arquitetura do site clonada do **padrão técnico** usado em
  `projetos/synapse/site/astro-site` (Astro 7 puro, `tokens.css`
  centralizado, componentes auto-contidos, deploy Netlify) — sem herdar
  conteúdo ou identidade visual da Synapse, só o padrão de código.
- Lançamento: substituir direto o domínio `nescauproducoes.com.br` quando
  pronto (decisão do usuário — sem staging).
- Copy: misturar — reaproveitar trechos institucionais do site atual
  (ex. história), reescrever as páginas de venda (home, contato).
- Contato: WhatsApp em destaque + formulário funcional (Netlify Forms).
- **Pendências antes de publicar:** confirmar lista final do casting
  (site oficial lista Vou Pro Sereno, Netinho de Paula, Projeto Samba 90
  Graus, Grupo do Bola, Marvvila; bio do Instagram marca Samba 90 Graus,
  Vou Pro Sereno e Dudu Nobre — reconciliar), fotos reais de cada
  artista, autorização de uso de logo dos clientes corporativos
  (Unilever, Fiat, Nestlé), WhatsApp/e-mail comercial oficiais, endereço
  da sede em São Paulo.
