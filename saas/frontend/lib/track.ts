/* ======================================================================
   Instrumentação leve de uso do produto — dispara um evento pro backend
   sem nunca bloquear nem quebrar o fluxo do usuário (fire-and-forget).
   ====================================================================== */

import { apiFetch } from "./api";

export function track(evento: string, metadata: Record<string, unknown> = {}) {
  apiFetch("/events", {
    method: "POST",
    body: JSON.stringify({ evento, metadata }),
  }).catch(() => {
    /* instrumentação nunca deve incomodar o usuário */
  });
}
