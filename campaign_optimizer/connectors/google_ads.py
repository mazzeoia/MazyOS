from .base import BaseAdsConnector


class GoogleAdsConnector(BaseAdsConnector):
    platform = "google_ads"
    docs_url = "https://developers.google.com/google-ads/api/docs/get-started/make-first-call"
    required_env = (
        "GOOGLE_ADS_DEVELOPER_TOKEN",
        "GOOGLE_ADS_CLIENT_ID",
        "GOOGLE_ADS_CLIENT_SECRET",
        "GOOGLE_ADS_REFRESH_TOKEN",
        "GOOGLE_ADS_LOGIN_CUSTOMER_ID",
        "GOOGLE_ADS_CUSTOMER_ID",
    )
    setup_items = (
        "Criar ou usar uma conta Google Ads Manager",
        "Solicitar developer token no API Center",
        "Criar credenciais OAuth 2.0 no Google Cloud",
        "Gerar refresh token com acesso adwords",
        "Informar login customer ID e customer ID do cliente",
    )
