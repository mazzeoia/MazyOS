// Fonte única do casting — Home, /casting e o select do formulário de contato
// importam daqui.
//
// "Grupo do Bola" segue marcado como não confirmado: aparece no site oficial
// atual (nescauproducoes.com.br) mas não na bio do Instagram @nescauproducoes,
// que cita Samba 90 Graus, Vou Pro Sereno e Dudu Nobre. Os outros 5 nomes
// batem em pelo menos uma das duas fontes. Não remover a flag até o cliente
// fechar a lista (ver briefing.md).

export interface Artist {
  slug: string;
  name: string;
  genre: string;
  bio: string;
  /** Placa gerada em public/media. Trocar por foto real mantendo o nome. */
  image: string;
  confirmed: boolean;
}

export const artists: Artist[] = [
  {
    slug: "vou-pro-sereno",
    name: "Vou Pro Sereno",
    genre: "Pagode",
    bio: "Pagode romântico e atual, um dos nomes mais ouvidos do gênero na cena nacional.",
    image: "/media/artista-vou-pro-sereno.svg",
    confirmed: true,
  },
  {
    slug: "netinho-de-paula",
    name: "Netinho de Paula",
    genre: "Samba & Pagode",
    bio: "Cantor e compositor, uma das referências do samba e do pagode brasileiro.",
    image: "/media/artista-netinho-de-paula.svg",
    confirmed: true,
  },
  {
    slug: "samba-90-graus",
    name: "Projeto Samba 90 Graus",
    genre: "Samba",
    bio: "Samba de raiz com repertório que conversa com várias gerações de uma vez.",
    image: "/media/artista-samba-90-graus.svg",
    confirmed: true,
  },
  {
    slug: "marvvila",
    name: "Marvvila",
    genre: "Pagode",
    bio: "Uma das vozes em ascensão mais fortes do pagode e do samba atual.",
    image: "/media/artista-marvvila.svg",
    confirmed: true,
  },
  {
    slug: "dudu-nobre",
    name: "Dudu Nobre",
    genre: "Samba",
    bio: "Cantor e compositor, um dos nomes mais respeitados do samba nacional.",
    image: "/media/artista-dudu-nobre.svg",
    confirmed: true,
  },
  {
    slug: "grupo-do-bola",
    name: "Grupo do Bola",
    genre: "Samba & Pagode",
    bio: "Um dos grupos mais tradicionais do samba e do pagode nacional.",
    image: "/media/artista-grupo-do-bola.svg",
    confirmed: false,
  },
];
