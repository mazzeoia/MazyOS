/* ======================================================================
   Display formatters — currency, percentage, numbers, dates
   ====================================================================== */

export const fmt = {
  currency: (v: number) =>
    v.toLocaleString("pt-BR", { style: "currency", currency: "BRL" }),
  pct: (v: number) => `${v.toFixed(2)}%`,
  num: (v: number) => v.toLocaleString("pt-BR"),
  date: (iso: string) => {
    try {
      return new Date(iso).toLocaleDateString("pt-BR", {
        day: "2-digit",
        month: "short",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return iso;
    }
  },
};
