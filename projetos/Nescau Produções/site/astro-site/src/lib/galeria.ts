// Galeria — placas geradas (public/media/g-*.svg) com categoria e proporção.
// A proporção fica no dado, não no CSS: é ela que dá o ritmo irregular do
// mosaico. Ao substituir por foto real, manter a proporção declarada aqui ou
// atualizar as duas coisas juntas.

export interface Shot {
  src: string;
  cat: "palco" | "luz" | "publico" | "bastidores" | "estrutura";
  alt: string;
  caption: string;
  /** "tall" = 4:5 · "wide" = 3:2 · "square" = 1:1 */
  ratio: "tall" | "wide" | "square";
}

export const categories = [
  { id: "todos", label: "Tudo" },
  { id: "palco", label: "Palco" },
  { id: "luz", label: "Luz" },
  { id: "publico", label: "Público" },
  { id: "bastidores", label: "Bastidores" },
  { id: "estrutura", label: "Estrutura" },
] as const;

export const shots: Shot[] = [
  {
    src: "/media/g-palco-01.svg",
    cat: "palco",
    alt: "Treliça de palco iluminada por refletores âmbar",
    caption: "Montagem de palco",
    ratio: "tall",
  },
  {
    src: "/media/g-publico-01.svg",
    cat: "publico",
    alt: "Plateia em contraluz durante um show",
    caption: "Plateia em contraluz",
    ratio: "wide",
  },
  {
    src: "/media/g-luz-01.svg",
    cat: "luz",
    alt: "Fachos de luz cruzando a fumaça de palco",
    caption: "Desenho de luz",
    ratio: "square",
  },
  {
    src: "/media/g-bastidores-01.svg",
    cat: "bastidores",
    alt: "Mesa de som durante a passagem",
    caption: "Passagem de som",
    ratio: "tall",
  },
  {
    src: "/media/g-led-01.svg",
    cat: "estrutura",
    alt: "Painel de LED aceso ao fundo do palco",
    caption: "Painel de LED",
    ratio: "wide",
  },
  {
    src: "/media/g-luz-02.svg",
    cat: "luz",
    alt: "Fachos frios e quentes cruzando sobre o palco",
    caption: "Corte de luz",
    ratio: "tall",
  },
  {
    src: "/media/g-palco-02.svg",
    cat: "palco",
    alt: "Estrutura de palco vista de frente com refletores acesos",
    caption: "Palco montado",
    ratio: "wide",
  },
  {
    src: "/media/g-som-01.svg",
    cat: "estrutura",
    alt: "Line array suspenso sobre o palco",
    caption: "Line array",
    ratio: "tall",
  },
  {
    src: "/media/g-publico-02.svg",
    cat: "publico",
    alt: "Público de braços erguidos durante o show",
    caption: "Público",
    ratio: "square",
  },
  {
    src: "/media/g-bastidores-02.svg",
    cat: "bastidores",
    alt: "Operação de som durante o show",
    caption: "Operação",
    ratio: "wide",
  },
  {
    src: "/media/g-som-02.svg",
    cat: "estrutura",
    alt: "Caixas de som suspensas em contraluz",
    caption: "P.A.",
    ratio: "square",
  },
  {
    src: "/media/g-luz-03.svg",
    cat: "luz",
    alt: "Refletores abrindo sobre a plateia",
    caption: "Abertura de show",
    ratio: "wide",
  },
];
