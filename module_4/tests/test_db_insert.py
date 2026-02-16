import pytest

from tests.utils.db_test_utils import (
    REQUIRED_FIELDS,
    count_required_fields,
    count_rows,
    fetch_one_as_dict,
    install_fake_popen,
    set_sample_jsonl,
    set_test_table,
    truncate_table,
)


@pytest.mark.db
def test_pull_data_inserts_rows(monkeypatch, post_request):
    # Ensure a pull inserts new rows with required fields populated.
    table_name = "applicant_test"
    set_test_table(monkeypatch, table_name)

    truncate_table(table_name)
    try:
        assert count_rows(table_name) == 0
        set_sample_jsonl(monkeypatch)
        install_fake_popen(monkeypatch)

        response = post_request("/pull-data")

        assert response.status_code == 200
        assert response.get_json() == {"ok": True}
        assert count_rows(table_name) > 0
        assert count_required_fields(table_name) > 0
    finally:
        truncate_table(table_name)


@pytest.mark.db
def test_pull_data_is_idempotent(monkeypatch, post_request):
    # Ensure duplicate pulls do not create duplicate rows.
    table_name = "applicant_test"
    set_test_table(monkeypatch, table_name)

    truncate_table(table_name)
    try:
        set_sample_jsonl(monkeypatch)
        install_fake_popen(monkeypatch)

        first_response = post_request("/pull-data")
        assert first_response.status_code == 200
        assert first_response.get_json() == {"ok": True}

        count_after_first = count_rows(table_name)
        assert count_after_first > 0

        second_response = post_request("/pull-data")
        assert second_response.status_code == 200
        assert second_response.get_json() == {"ok": True}

        count_after_second = count_rows(table_name)
        assert count_after_second == count_after_first
    finally:
        truncate_table(table_name)


@pytest.mark.db
def test_query_returns_required_keys(monkeypatch, post_request):
    # Ensure query results can be returned as a dict with required keys.
    table_name = "applicant_test"
    set_test_table(monkeypatch, table_name)

    truncate_table(table_name)
    try:
        set_sample_jsonl(monkeypatch)
        install_fake_popen(monkeypatch)

        response = post_request("/pull-data")
        assert response.status_code == 200
        assert response.get_json() == {"ok": True}

        row = fetch_one_as_dict(table_name, REQUIRED_FIELDS)
        assert row is not None
        assert set(row.keys()) == set(REQUIRED_FIELDS)
    finally:
        truncate_table(table_name)
