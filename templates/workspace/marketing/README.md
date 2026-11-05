# marketing/ — saídas do MazyOS

Tudo que as skills de marketing produzem cai aqui. Skills do MazyOS já sabem onde salvar — você raramente precisa criar pasta manualmente.

## Estrutura padrão

```
marketing/
├── conteudo/                    saídas do /mazyos:carrossel e /mazyos:publicar-tema
│   └── <tipo>-<tema>-<YYYY-MM-DD>/
│       ├── carrossel.html
│       ├── render.js
│       ├── instagram/slide-XX.png
│       ├── legenda.md
│       └── legenda-linkedin.md
│
├── seo/                         saídas do /mazyos:seo (8 passos)
│   ├── 01-pesquisa-demanda.md
│   ├── 02-analise-concorrencia.md
│   ├── 03-google-meu-negocio.md
│   ├── 04-otimizacao-on-page.md
│   ├── 05-estrategia-conteudo.md
│   ├── 06-google-ads.md
│   ├── 07-checklist-monitoramento.md
│   └── 08-geo-otimizacao-ia.md
│
├── campanhas/                   saídas do /mazyos:anuncio-google e /mazyos:relatorio-ads
│   ├── google-ads-<YYYY-MM-DD>/  CSVs prontos pra importar
│   └── relatorios/               relatórios semanais
│
└── avaliacoes-google/           histórico do /mazyos:responder-avaliacoes (opcional)
```

## Como funciona

- **`/mazyos:carrossel` ou `/mazyos:publicar-tema`** → cria pasta em `conteudo/<tipo>-<tema>-<data>/`
- **`/mazyos:seo`** → preenche os 8 arquivos numerados em `seo/`
- **`/mazyos:anuncio-google`** → cria pasta em `campanhas/google-ads-<data>/` com CSVs
- **`/mazyos:relatorio-ads`** → cria arquivo em `campanhas/relatorios/<data>-relatorio.md`
- **`/mazyos:responder-avaliacoes`** → opcionalmente salva histórico em `avaliacoes-google/`

## Versionamento

Tudo aqui versiona no git pelo `/mazyos:salvar`. Útil pra comparar evolução de SEO entre meses, rever copies antigas, ou recuperar peça depois de mexer no Insta.
