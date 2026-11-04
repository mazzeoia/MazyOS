// Depoimentos — VAZIO DE PROPÓSITO.
//
// Nenhum depoimento real de contratante foi coletado ainda, e depoimento
// inventado num site institucional é fraude de prova social, não "conteúdo
// provisório". A seção da home lê este array: enquanto estiver vazio, ela
// simplesmente não é renderizada.
//
// Pra ligar: preencher com depoimentos reais (nome, cargo/empresa e evento).
// O layout já está pronto e aparece sozinho no próximo build.

export interface Testimonial {
  quote: string;
  author: string;
  role: string;
  event?: string;
}

export const testimonials: Testimonial[] = [];
