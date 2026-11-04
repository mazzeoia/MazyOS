// @ts-check
import { defineConfig } from "astro/config";

export default defineConfig({
  site: "https://nescauproducoes.com.br",

  build: {
    // Nunca embutir CSS em <style> no HTML. O padrão do Astro ("auto") embute
    // folhas pequenas — e cada <style> inline seria bloqueado pelo CSP do
    // site, que é `style-src 'self'` sem 'unsafe-inline'. Com tudo externo, o
    // CSP continua estrito e nada quebra em produção.
    inlineStylesheets: "never",
  },

  // Pré-carrega a página no hover do link: navegação entre páginas fica
  // instantânea sem transformar o site numa SPA.
  prefetch: {
    prefetchAll: true,
    defaultStrategy: "hover",
  },
});
