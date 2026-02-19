import pytest

import config


@pytest.mark.db
def test_get_db_connect_kwargs_prefers_database_url(monkeypatch):
    # DATABASE_URL should be used when set.
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@host:5432/dbname")

    assert config.get_db_connect_kwargs() == {"conninfo": "postgresql://user:pass@host:5432/dbname"}
