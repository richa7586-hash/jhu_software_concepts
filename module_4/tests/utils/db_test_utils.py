import importlib
import os

import psycopg

import app as app_module
import config
import load_data
import query_data

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


def connect_db():
    # Open a database connection using the current config.
    return psycopg.connect(
        dbname=config.DB_NAME,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        host=config.DB_HOST,
        port=config.DB_PORT,
    )


def truncate_table(table_name):
    # Ensure the test table exists and is empty.
    with connect_db() as conn:
        load_data.create_table_if_not_exists(conn)
        with conn.cursor() as cur:
            cur.execute(f"TRUNCATE TABLE {table_name} RESTART IDENTITY;")
        conn.commit()


def set_test_table(monkeypatch, table_name):
    # Point config at the test table for isolated writes.
    monkeypatch.setattr(config, "TABLE_NAME", table_name)
    monkeypatch.setattr(load_data.config, "TABLE_NAME", table_name)


def set_sample_jsonl(monkeypatch):
    # Use a small JSONL fixture for predictable inserts.
    jsonl_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../resources", "applicant_data_sample.jsonl")
    )
    if not os.path.exists(jsonl_path):
        raise AssertionError(f"Missing data file: {jsonl_path}")

    monkeypatch.setattr(config, "APPLICANT_DATA_JSON_FILE", jsonl_path)
    monkeypatch.setattr(load_data.config, "APPLICANT_DATA_JSON_FILE", jsonl_path)


def install_fake_popen(monkeypatch):
    # Replace subprocess.Popen with a loader call for tests.
    def fake_popen(*_args, **_kwargs):
        # Run the loader synchronously for deterministic inserts.
        load_data.main()

        class DoneProcess:
            def poll(self):
                # Signal that the fake process has completed.
                return 0

        return DoneProcess()

    monkeypatch.setattr(app_module, "_pull_process", None)
    monkeypatch.setattr(app_module.subprocess, "Popen", fake_popen)


def install_query_data(monkeypatch):
    # Reload question_sql_dict after table name changes.
    reloaded = importlib.reload(query_data)
    monkeypatch.setattr(app_module, "question_sql_dict", reloaded.question_sql_dict)


def count_rows(table_name):
    # Count total rows in the given table.
    with connect_db() as conn:
        with conn.cursor() as cur:
            cur.execute(f"SELECT COUNT(*) FROM {table_name};")
            return cur.fetchone()[0]


def count_required_fields(table_name):
    # Count rows where required fields are present.
    with connect_db() as conn:
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


def fetch_one_as_dict(table_name, fields):
    # Fetch one row and return it as a dict keyed by fields.
    with connect_db() as conn:
        with conn.cursor() as cur:
            field_list = ", ".join(fields)
            cur.execute(f"SELECT {field_list} FROM {table_name} LIMIT 1;")
            row = cur.fetchone()
            if row is None:
                return None
            return dict(zip(fields, row))
