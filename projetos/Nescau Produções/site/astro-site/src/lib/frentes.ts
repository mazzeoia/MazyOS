// "Frentes" ocupa, na narrativa da home, o lugar de uma seção de cases.
//
// Deliberadamente NÃO é uma lista de cases: a Nescau ainda não liberou
// nenhum evento real (nome, praça, público, foto) pra publicação. Case
// inventado num site que vai substituir o domínio ativo é risco alto e
// desnecessário — então a seção mostra os quatro contextos reais de
// contratação. Quando houver material de evento aprovado, cada frente vira
// um case com número e foto sem mudar o layout.

export interface Frente {
  n: string;
  kicker: string;
  title: string;
  body: string;
  meta: { label: string; value: string }[];
  image: string;
}

export const frentes: Frente[] = [
  {
    n: "01",
    kicker: "Festival",
    title: "Palco grande, horário fechado",
    body: "Grade de festival não perdoa atraso. O artista chega com rider alinhado, passagem marcada e uma pessoa da Nescau em campo do desembarque ao fim do show.",
    meta: [
      { label: "Contratante", value: "Produtora de festival" },
      { label: "Formato", value: "Show completo" },
    ],
    image: "/media/case-festival.svg",
  },
  {
    n: "02",
    kicker: "Corporativo",
    title: "A marca no comando do palco",
    body: "Confraternização e ação de marca pedem outra coisa: duração ajustada, repertório alinhado e contrato que passa pelo jurídico sem travar.",
    meta: [
      { label: "Contratante", value: "Empresa / agência" },
      { label: "Formato", value: "Sob medida" },
    ],
    image: "/media/case-corporativo.svg",
  },
  {
    n: "03",
    kicker: "Internacional",
    title: "Samba fora do país",
    body: "Desde 2018 a Nescau leva seus artistas para a comunidade brasileira na Europa e nos Estados Unidos: documentação, rota e produção local resolvidas aqui.",
    meta: [
      { label: "Praças", value: "Europa e EUA" },
      { label: "Desde", value: "2018" },
    ],
    image: "/media/case-turne.svg",
  },
  {
    n: "04",
    kicker: "Privado",
    title: "Festa que precisa dar certo",
    body: "Casamento e aniversário grande têm uma chance só. Atendimento direto com a assessoria, formato reduzido quando faz sentido, contrato formal do mesmo jeito.",
    meta: [
      { label: "Contratante", value: "Assessoria / anfitrião" },
      { label: "Formato", value: "Reduzido ou completo" },
    ],
    image: "/media/case-privado.svg",
  },
];
