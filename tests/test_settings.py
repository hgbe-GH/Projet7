from __future__ import annotations

from datetime import date, timedelta

from openagenda_rag.settings import load_fetch_settings


def test_load_fetch_settings_defaults_to_recent_bounded_window(monkeypatch):
    for name in [
        "OPENDATASOFT_BASE_URL",
        "OPENDATASOFT_DATASET",
        "OPENAGENDA_AGENDA_UID",
        "OPENAGENDA_SEARCH",
        "OPENAGENDA_CITY",
        "OPENAGENDA_START_DATE",
        "OPENAGENDA_END_DATE",
        "OPENAGENDA_CATEGORY_FIELD",
        "OPENAGENDA_CATEGORY_IDS",
        "MISTRAL_API_KEY",
        "MISTRALAI_API_KEY",
    ]:
        monkeypatch.delenv(name, raising=False)

    settings = load_fetch_settings()

    assert settings.start_date == (date.today() - timedelta(days=365)).isoformat()
    assert settings.end_date == date.today().isoformat()
