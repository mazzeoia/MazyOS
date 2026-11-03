from __future__ import annotations

import re

from app.core.naming import ad_name, adset_name, campaign_name


def test_campaign_name_format():
    name = campaign_name("FORTEC", "leads-whatsapp", "sp-25-45-imoveis")
    assert name.startswith("[FORTEC]")
    assert "leads-whatsapp" in name
    assert "sp-25-45-imoveis" in name
    assert re.search(r"\d{8}-\d{4}$", name)


def test_adset_name_format():
    name = adset_name("FORTEC", "homens-30-45-sp")
    assert name.startswith("[FORTEC]")
    assert "homens-30-45-sp" in name
    assert re.search(r"\d{8}-\d{4}$", name)


def test_ad_name_format():
    name = ad_name("FORTEC", "video-prova-social")
    assert name.startswith("[FORTEC]")
    assert "video-prova-social" in name
    assert re.search(r"\d{8}-\d{4}$", name)


def test_campaign_name_pipe_separator():
    name = campaign_name("X", "obj", "pub")
    parts = name.split(" | ")
    assert len(parts) == 4
    assert parts[0] == "[X]"
