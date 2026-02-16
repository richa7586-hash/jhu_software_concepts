import pytest

import re

import app as app_module
from bs4 import BeautifulSoup

from tests.utils.db_test_utils import (
    count_rows,
    install_fake_popen,
    install_query_data,
    set_sample_jsonl,
    set_test_table,
    truncate_table,
)


@pytest.mark.integration
def test_end_to_end_pull_update_render(monkeypatch, post_request):
    # End-to-end: pull -> update -> render.
    table_name = "applicant_integration_test"
    set_test_table(monkeypatch, table_name)

    truncate_table(table_name)
    try:
        set_sample_jsonl(monkeypatch)
        start_pull_fn = install_fake_popen()
        install_query_data(monkeypatch)

        pull_response = post_request("/pull-data", app_kwargs={"start_pull_fn": start_pull_fn})
        assert pull_response.status_code == 200
        assert pull_response.get_json() == {"ok": True}
        assert count_rows(table_name) > 0

        update_response = post_request("/update-analysis")
        assert update_response.status_code == 200
        assert update_response.get_json() == {"ok": True}

        client = app_module.create_app().test_client()
        analysis_response = client.get("/analysis")
        assert analysis_response.status_code == 200
        soup = BeautifulSoup(analysis_response.get_data(as_text=True), "html.parser")
        text = soup.get_text()
        assert "Answer:" in text
        assert re.search(r"\d+\.\d{2}%", text)
    finally:
        truncate_table(table_name)


@pytest.mark.integration
def test_pull_data_is_idempotent_integration(monkeypatch, post_request):
    # Multiple pulls with overlapping data should not create duplicates.
    table_name = "applicant_integration_test"
    set_test_table(monkeypatch, table_name)

    truncate_table(table_name)
    try:
        set_sample_jsonl(monkeypatch)
        start_pull_fn = install_fake_popen()

        first_response = post_request("/pull-data", app_kwargs={"start_pull_fn": start_pull_fn})
        assert first_response.status_code == 200
        assert first_response.get_json() == {"ok": True}
        count_after_first = count_rows(table_name)
        assert count_after_first > 0

        second_response = post_request("/pull-data", app_kwargs={"start_pull_fn": start_pull_fn})
        assert second_response.status_code == 200
        assert second_response.get_json() == {"ok": True}
        assert count_rows(table_name) == count_after_first
    finally:
        truncate_table(table_name)
