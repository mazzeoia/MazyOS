export interface Step {
  n: string;
  title: string;
  body: string;
}

export const steps: Step[] = [
  {
    n: "01",
    title: "Conversa",
    body: "Data, cidade, público estimado e formato do evento. Em geral resolvido numa conversa de WhatsApp, é o que basta pra saber se faz sentido seguir.",
  },
  {
    n: "02",
    title: "Proposta",
    body: "Indicamos o artista que combina com o evento e com o orçamento, e mandamos a proposta com o que está incluso, item por item.",
  },
  {
    n: "03",
    title: "Contrato",
    body: "Fechado o artista, vai contrato formal, com rider técnico e cronograma anexos. Nada de acerto verbal.",
  },
  {
    n: "04",
    title: "Produção",
    body: "Logística, hospedagem, transporte e alinhamento do rider com a produção local, tudo antes de a semana do evento começar.",
  },
  {
    n: "05",
    title: "Show",
    body: "Alguém da Nescau acompanha em campo, do desembarque ao fim do show. O contratante fala com uma pessoa só.",
  },
  {
    n: "06",
    title: "Depois",
    body: "Fechamento, material do evento e o próximo passo, porque a maior parte dos contratantes volta.",
  },
];
