// FAQ — respostas escritas dentro do que o briefing sustenta, sem prometer
// prazo, valor ou escopo que não foram confirmados. REVISAR COM O CLIENTE
// antes de publicar: são as frases que um contratante vai cobrar depois.

export interface Faq {
  q: string;
  a: string;
}

export const faqs: Faq[] = [
  {
    q: "Como funciona a contratação de um show?",
    a: "Você manda data, cidade e formato do evento pelo WhatsApp. A gente confere a agenda do artista e devolve uma proposta com o que está incluso. Fechado, segue contrato formal com rider técnico anexo.",
  },
  {
    q: "Vocês atendem fora de São Paulo?",
    a: "Sim. A sede é em São Paulo, mas os artistas rodam o Brasil inteiro e, desde 2018, também Europa e Estados Unidos em turnês voltadas à comunidade brasileira.",
  },
  {
    q: "Com quanta antecedência devo procurar?",
    a: "Quanto antes, melhor: agenda de artista de samba e pagode fecha cedo, principalmente em datas de alta temporada. Mesmo assim, vale consultar, janela de última hora acontece.",
  },
  {
    q: "O que está incluso no cachê?",
    a: "Varia por artista e por formato de evento. A proposta detalha item a item o que entra (show, equipe, deslocamento) e o que fica com a produção local.",
  },
  {
    q: "Vocês produzem o evento ou só vendem o show?",
    a: "A Nescau responde pela produção executiva do show: logística, cronograma de palco, equipe em campo e alinhamento do rider com a produção local. A estrutura do evento em si costuma ser contratada pelo próprio contratante.",
  },
  {
    q: "Dá para contratar para festa privada?",
    a: "Dá. Casamento, aniversário e festa grande entram com o mesmo contrato e a mesma estrutura de um show de festival, em alguns casos, com formato reduzido.",
  },
];
