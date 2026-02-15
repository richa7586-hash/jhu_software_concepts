import os
import psycopg

import app as app_module
import config
import load_data


REQUIRED_FIELDS = [
    "program",
    "comments",
    "date_added",
    "url",
    "status",
    "term",
    "us_or_international",
    "gpa",
    "gre",
    "gre_v",
    "gre_aw",
    "degree",
    "llm_generated_program",
    "llm_generated_university",
]


def _connect_db():
    # Centralized DB connection helper for the insert test.
    return psycopg.connect(
        dbname=config.DB_NAME,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        host=config.DB_HOST,
        port=config.DB_PORT,
    )


def _truncate_table(table_name):
    # Ensure the test table exists and is empty before/after the test.
    with _connect_db() as conn:
        load_data.create_table_if_not_exists(conn)
        with conn.cursor() as cur:
            cur.execute(f"TRUNCATE TABLE {table_name} RESTART IDENTITY;")
        conn.commit()


def _set_test_table(monkeypatch, table_name):
    # Point both app and loader config to the isolated test table.
    monkeypatch.setattr(config, "TABLE_NAME", table_name)
    monkeypatch.setattr(load_data.config, "TABLE_NAME", table_name)


def _get_sample_jsonl_path():
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), "resources", "applicant_data_sample.jsonl")
    )


def _set_sample_jsonl(monkeypatch):
    jsonl_path = _get_sample_jsonl_path()
    if not os.path.exists(jsonl_path):
        raise AssertionError(f"Missing data file: {jsonl_path}")

    monkeypatch.setattr(config, "APPLICANT_DATA_JSON_FILE", jsonl_path)
    monkeypatch.setattr(load_data.config, "APPLICANT_DATA_JSON_FILE", jsonl_path)


def _install_fake_popen(monkeypatch):
    # Run the loader inline when /pull-data starts the scraper.
    def fake_popen(*_args, **_kwargs):
        load_data.main()

        class DoneProcess:
            def poll(self):
                return 0

        return DoneProcess()

    monkeypatch.setattr(app_module, "_pull_process", None)
    monkeypatch.setattr(app_module.subprocess, "Popen", fake_popen)

def _count_rows(table_name):
    with _connect_db() as conn:
        with conn.cursor() as cur:
            cur.execute(f"SELECT COUNT(*) FROM {table_name};")
            return cur.fetchone()[0]


def _count_required_fields(table_name):
    with _connect_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT COUNT(*)
                FROM {table_name}
                WHERE program IS NOT NULL
                  AND url IS NOT NULL
                  AND term IS NOT NULL
                  AND degree IS NOT NULL
                  AND llm_generated_program IS NOT NULL
                  AND llm_generated_university IS NOT NULL
                """
            )
            return cur.fetchone()[0]


def _fetch_one_as_dict(table_name, fields):
    with _connect_db() as conn:
        with conn.cursor() as cur:
            field_list = ", ".join(fields)
            cur.execute(f"SELECT {field_list} FROM {table_name} LIMIT 1;")
            row = cur.fetchone()
            if row is None:
                return None
            return dict(zip(fields, row))


def test_pull_data_inserts_rows(monkeypatch, post_request):
    # Ensure a pull inserts new rows with required fields populated.
    table_name = "applicant_test"
    _set_test_table(monkeypatch, table_name)

    _truncate_table(table_name)
    try:
        assert _count_rows(table_name) == 0
        _set_sample_jsonl(monkeypatch)
        _install_fake_popen(monkeypatch)
        response = post_request("/pull-data")

        assert response.status_code == 200
        assert response.get_json() == {"status": "started"}
        assert _count_rows(table_name) > 0
        assert _count_required_fields(table_name) > 0
    finally:
        _truncate_table(table_name)


def test_pull_data_is_idempotent(monkeypatch, post_request):
    # Ensure duplicate pulls do not create duplicate rows.
    table_name = "applicant_test"
    _set_test_table(monkeypatch, table_name)

    _truncate_table(table_name)
    try:
        _set_sample_jsonl(monkeypatch)
        _install_fake_popen(monkeypatch)

        first_response = post_request("/pull-data")
        assert first_response.status_code == 200
        assert first_response.get_json() == {"status": "started"}

        count_after_first = _count_rows(table_name)
        assert count_after_first > 0

        second_response = post_request("/pull-data")
        assert second_response.status_code == 200
        assert second_response.get_json() == {"status": "started"}

        count_after_second = _count_rows(table_name)
        assert count_after_second == count_after_first
    finally:
        _truncate_table(table_name)


def test_query_returns_required_keys(monkeypatch, post_request):
    # Ensure query results can be returned as a dict with required keys.
    table_name = "applicant_test"
    _set_test_table(monkeypatch, table_name)

    _truncate_table(table_name)
    try:
        _set_sample_jsonl(monkeypatch)
        _install_fake_popen(monkeypatch)

        response = post_request("/pull-data")
        assert response.status_code == 200
        assert response.get_json() == {"status": "started"}

        row = _fetch_one_as_dict(table_name, REQUIRED_FIELDS)
        assert row is not None
        assert set(row.keys()) == set(REQUIRED_FIELDS)
    finally:
        _truncate_table(table_name)
