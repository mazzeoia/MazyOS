// Serviços — escopo tirado do briefing (booking, gestão de carreira, marketing,
// execução em rádio/TV, turnês internacionais desde 2018) e dos três tipos de
// contratante citados: festival, corporativo, festa privada.
//
// O card "Rider e estrutura" descreve coordenação do rider técnico junto à
// produção local. Se a Nescau também VENDER estrutura, som, luz e painel de
// LED como serviço próprio, cada um vira um item novo nesta lista — mas isso
// não está no briefing e não pode ser afirmado no site sem confirmação.

export interface Service {
  n: string;
  title: string;
  short: string;
  body: string;
  bullets: string[];
  image: string;
}

export const services: Service[] = [
  {
    n: "01",
    title: "Contratação de shows",
    short: "O artista certo para a data certa",
    body: "Intermediação completa da contratação: disponibilidade de agenda, proposta, contrato e alinhamento com a produção do evento.",
    bullets: ["Consulta de agenda", "Proposta e contrato", "Alinhamento com a produção"],
    image: "/media/svc-booking.svg",
  },
  {
    n: "02",
    title: "Gestão de carreira",
    short: "Carreira conduzida, não improvisada",
    body: "Direção de carreira do artista no dia a dia: posicionamento, calendário de shows, imagem e as decisões que sustentam a agenda cheia.",
    bullets: ["Posicionamento", "Calendário de turnê", "Relação com contratantes"],
    image: "/media/svc-gestao.svg",
  },
  {
    n: "03",
    title: "Produção executiva",
    short: "Do contrato ao palco",
    body: "Coordenação de tudo que precisa acontecer entre o aceite da proposta e o artista entrar no palco no horário combinado.",
    bullets: ["Logística e hospedagem", "Cronograma de palco", "Equipe em campo"],
    image: "/media/svc-producao.svg",
  },
  {
    n: "04",
    title: "Rider e estrutura",
    short: "Alinhamento técnico sem surpresa",
    body: "O rider técnico do artista chega antecipado e alinhado com a produção local: som, luz, palco e backline conferidos antes da passagem.",
    bullets: ["Rider antecipado", "Conferência com a produção local", "Passagem de som"],
    image: "/media/svc-estrutura.svg",
  },
  {
    n: "05",
    title: "Eventos corporativos",
    short: "Show dentro da agenda da marca",
    body: "Confraternização, ação de marca e evento de empresa: formato, duração e repertório ajustados ao que a companhia precisa entregar.",
    bullets: ["Formato sob medida", "Nota fiscal e contrato", "Interlocutor único"],
    image: "/media/svc-corporativo.svg",
  },
  {
    n: "06",
    title: "Festas privadas",
    short: "Casamento, aniversário, festa grande",
    body: "Atendimento para assessorias e produtores de festa particular, com a mesma estrutura contratual de um show de festival.",
    bullets: ["Atendimento a assessorias", "Formatos reduzidos", "Contrato formal"],
    image: "/media/svc-privado.svg",
  },
  {
    n: "07",
    title: "Turnês internacionais",
    short: "Europa e Estados Unidos desde 2018",
    body: "Turnês voltadas à comunidade brasileira no exterior, com toda a operação de documentação, rota e produção local.",
    bullets: ["Documentação e vistos", "Rota e logística", "Produção local"],
    image: "/media/svc-internacional.svg",
  },
  {
    n: "08",
    title: "Marketing e execução",
    short: "O show existe antes da data",
    body: "Marketing digital dos artistas e trabalho de execução em rádio e TV, aberta e fechada, o que faz o público chegar antes do dia do show.",
    bullets: ["Marketing digital", "Execução em rádio", "TV aberta e fechada"],
    image: "/media/svc-luz.svg",
  },
];
