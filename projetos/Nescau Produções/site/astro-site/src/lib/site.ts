// Dados de contato e navegação — fonte única. Qualquer número/endereço no
// site sai daqui, então trocar o WhatsApp é uma linha, não uma busca global.

export const site = {
  name: "Nescau Produções",
  tagline: "Gestão de carreira e venda de shows de samba e pagode",
  description:
    "Produtora de samba e pagode desde 1997. Gestão de carreira artística e venda de shows para festivais, eventos corporativos e festas privadas, no Brasil, na Europa e nos EUA.",
  url: "https://nescauproducoes.com.br",
  city: "São Paulo, SP",
  founded: 1997,

  // Número comercial único confirmado no briefing. O segundo número que
  // aparece no site antigo (94812-7718) foi descartado pelo cliente.
  whatsapp: "5511912270708",
  whatsappDisplay: "(11) 91227-0708",
  whatsappMessage:
    "Olá! Vim pelo site e quero falar sobre a contratação de um show.",

  email: "administracao@nescauproducoes.com.br",
  instagram: "https://www.instagram.com/nescauproducoes/",
  instagramHandle: "@nescauproducoes",
} as const;

export const whatsappUrl = `https://wa.me/${site.whatsapp}?text=${encodeURIComponent(site.whatsappMessage)}`;

export const nav = [
  { label: "Casting", href: "/casting" },
  { label: "Serviços", href: "/servicos" },
  { label: "Quem somos", href: "/quem-somos" },
  { label: "Portfólio", href: "/portfolio" },
] as const;
