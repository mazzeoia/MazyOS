import { artists } from "./casting";
import { site } from "./site";

// Só números verificáveis a partir do briefing. Quantidade de eventos, público
// somado e cidades atendidas seriam os números mais fortes aqui — mas nenhum
// deles existe em fonte confirmada, e número de vitrine chutado é o tipo de
// coisa que um contratante cobra depois. Entram quando o cliente passar.

const currentYear = new Date().getFullYear();

export interface Stat {
  value: number;
  suffix?: string;
  prefix?: string;
  label: string;
  note: string;
}

export const stats: Stat[] = [
  {
    value: currentYear - site.founded,
    suffix: "",
    label: "Anos de estrada",
    note: `Desde ${site.founded}`,
  },
  {
    value: artists.length,
    label: "Artistas no casting",
    note: "Samba e pagode",
  },
  {
    value: 2,
    label: "Continentes",
    note: "Brasil, Europa e EUA",
  },
  {
    value: currentYear - 2018,
    label: "Anos de turnê internacional",
    note: "Desde 2018",
  },
];
