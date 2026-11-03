# Creative Ads OS

Sistema local para otimizar campanhas da Creative Agencia Marketing.

## Rodar

```powershell
cd "C:\Users\ELIELETRO\Desktop\Creative Agencia LTDA\Creative Agencia Marketing"
python -m pip install -r campaign_optimizer\requirements.txt
python -m streamlit run campaign_optimizer\app.py
```

## Fluxo da V1

1. Cadastre um cliente.
2. Configure `.env` na raiz do projeto para Meta e Google Ads quando for usar API.
3. Importe CSV do Meta Ads ou Google Ads enquanto a API nao estiver pronta.
4. Abra o Dashboard para ver KPIs.
5. Rode a Rotina diaria para gerar diagnostico, alertas e acoes.
6. Gere o relatorio HTML para revisar e enviar ao cliente.

## Regras de seguranca

- Nao aumenta orcamento automaticamente.
- Nao ativa campanha automaticamente.
- Pausa real por API fica bloqueada nesta V1.
- Pausas recomendadas entram primeiro como dry-run no log.
- Instagram Ads e tratado dentro de Meta Ads.
- Sem CRM integrado, o sistema otimiza por lead de WhatsApp/formulario, nao por venda fechada.

## Variaveis futuras para API

Meta:

```env
META_ACCESS_TOKEN=
META_AD_ACCOUNT_ID=
```

Google Ads:

```env
GOOGLE_ADS_DEVELOPER_TOKEN=
GOOGLE_ADS_CLIENT_ID=
GOOGLE_ADS_CLIENT_SECRET=
GOOGLE_ADS_REFRESH_TOKEN=
GOOGLE_ADS_LOGIN_CUSTOMER_ID=
GOOGLE_ADS_CUSTOMER_ID=
```

## Setup por API

Copie `campaign_optimizer/.env.example` para `.env` na raiz do projeto.

Google Ads API:

- Precisa de `developer token`, OAuth 2.0 e IDs da conta manager e da conta cliente.
- Doc oficial: https://developers.google.com/google-ads/api/docs/get-started/make-first-call
- OAuth: https://developers.google.com/google-ads/api/docs/oauth/overview

Meta Marketing API:

- Precisa de app no Meta for Developers, token e conta de anuncios.
- Para leitura: `ads_read`
- Para alteracoes: `ads_management`
- Doc oficial: https://developers.facebook.com/docs/marketing-api/
