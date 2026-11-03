# Creative Campaign OS SaaS

Base escalavel do produto:

- `frontend`: Next.js para a interface premium.
- `backend`: FastAPI para inteligencia, regras, integracoes e automacoes.
- `Supabase`: auth, banco, dados por cliente e historico.

O Streamlit atual continua como laboratorio em `campaign_optimizer/`.

## Desenvolvimento local

Backend:

```bash
cd saas/backend
uv sync
uv run fastapi dev app/main.py --port 8000
```

Frontend:

```bash
cd saas/frontend
npm install
npm run dev
```

## Variaveis

Use o `.env` da raiz do projeto. No frontend, apenas variaveis `NEXT_PUBLIC_*` podem ser expostas.
`SUPABASE_SECRET_KEY`, `OPENAI_API_KEY`, tokens Meta e tokens Google ficam somente no backend.

## Producao

Dominio planejado: `ads.creativeagenciamkt.com.br`

Guia de deploy na VPS:

```text
saas/deploy/DEPLOY_VPS.md
```
