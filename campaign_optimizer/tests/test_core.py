from __future__ import annotations

from io import StringIO
import shutil
import unittest

from campaign_optimizer.core.database import CLIENTS_DIR, slugify
from campaign_optimizer.core.importers import read_csv
from campaign_optimizer.core.reports import generate_html_report
from campaign_optimizer.core.rules import evaluate_rows, summarize_kpis


class CampaignOptimizerTest(unittest.TestCase):
    def tearDown(self):
        shutil.rmtree(CLIENTS_DIR / slugify("Cliente Teste"), ignore_errors=True)

    def test_meta_csv_import_with_missing_secondary_columns(self):
        csv = StringIO("Campanha,Impressoes,Cliques no link,Valor gasto,Resultados,CTR\nLead WhatsApp,1000,20,150,3,2.0\n")
        rows = read_csv(csv, platform="meta_ads", source_file="meta.csv")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["campaign"], "Lead WhatsApp")
        self.assertEqual(rows[0]["spend"], 150)
        self.assertEqual(rows[0]["leads"], 3)
        self.assertEqual(rows[0]["cpl"], 50)

    def test_meta_export_with_long_headers_is_mapped_correctly(self):
        csv = StringIO(
            "Nome da campanha,Nome do conjunto de anúncios,Alcance,Impressões,Frequência,Resultados,Valor gasto (BRL),Custo por resultado,Início dos relatórios\n"
            "Engajamento Jacarecanga,Novo conjunto,8397,13273,1.58068358,43,207.9,4.83488372,2026-08-01\n"
        )
        rows = read_csv(csv, platform="meta_ads", source_file="Relatorio-Creative-ADS.csv")
        self.assertEqual(rows[0]["campaign"], "Engajamento Jacarecanga")
        self.assertEqual(rows[0]["ad_group"], "Novo conjunto")
        self.assertEqual(rows[0]["reach"], 8397)
        self.assertEqual(rows[0]["spend"], 207.9)
        self.assertEqual(rows[0]["cpl"], 4.83)
        self.assertEqual(rows[0]["date"], "2026-08-01")

    def test_google_csv_import_calculates_metrics(self):
        csv = StringIO("Campaign,Impressions,Clicks,Cost,Conversions\nSearch Geral,2000,100,300,10\n")
        rows = read_csv(csv, platform="google_ads", source_file="google.csv")
        self.assertEqual(rows[0]["platform"], "google_ads")
        self.assertEqual(rows[0]["ctr"], 5)
        self.assertEqual(rows[0]["cpc"], 3)
        self.assertEqual(rows[0]["cpl"], 30)

    def test_rule_recommends_pause_for_spend_without_lead(self):
        rows = [{"platform": "meta_ads", "campaign": "Teste", "spend": 150, "leads": 0, "ctr": 1.5, "frequency": 2.1}]
        client = {"waste_limit": 100, "target_cpl": 40, "min_ctr": 0.8, "max_frequency": 3}
        alerts = evaluate_rows(rows, client, allow_pause=True)
        self.assertEqual(alerts[0].rule_name, "gasto_sem_lead")
        self.assertTrue(alerts[0].should_pause)

    def test_kpi_summary_and_html_report(self):
        rows = [{"platform": "google_ads", "campaign": "Search", "spend": 200, "leads": 4, "clicks": 50, "impressions": 1000, "cpl": 50, "ctr": 5}]
        kpis = summarize_kpis(rows)
        self.assertEqual(kpis["cpl"], 50)
        client = {"name": "Cliente Teste"}
        path = generate_html_report(client, rows, [], "Analise de teste")
        self.assertTrue(path.exists())
        self.assertIn("Relatorio de campanhas", path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
