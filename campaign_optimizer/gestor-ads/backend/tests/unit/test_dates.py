from __future__ import annotations

from datetime import date

from app.shared.dates import date_preset_to_start_date

TODAY = date(2026, 8, 29)


def test_today():
    assert date_preset_to_start_date("today", TODAY) == "2026-08-29"


def test_yesterday():
    assert date_preset_to_start_date("yesterday", TODAY) == "2026-08-28"


def test_last_7d():
    assert date_preset_to_start_date("last_7d", TODAY) == "2026-08-22"


def test_last_14d():
    assert date_preset_to_start_date("last_14d", TODAY) == "2026-08-15"


def test_last_30d():
    assert date_preset_to_start_date("last_30d", TODAY) == "2026-07-30"


def test_this_month():
    assert date_preset_to_start_date("this_month", TODAY) == "2026-08-01"


def test_unknown_preset_falls_back_to_last_7d():
    assert date_preset_to_start_date("bogus", TODAY) == "2026-08-22"
