from types import SimpleNamespace
import json
import runpy

import pytest

import config
import load_data
import psycopg


class FakeError(Exception):
    pass


class FakeCursor:
    def __init__(self, raise_on_executemany=False, raise_on_execute=False, raise_on_execute_if=None):
        # Configure whether to raise on executemany or execute calls.
        self.raise_on_executemany = raise_on_executemany
        self.raise_on_execute = raise_on_execute
        self.raise_on_execute_if = raise_on_execute_if
        self.connection = SimpleNamespace(commit=lambda: None)

    def __enter__(self):
        # Support context manager usage.
        return self

    def __exit__(self, exc_type, exc, tb):
        # Do not suppress exceptions.
        return False

    def execute(self, _query, _params=None):
        # Optionally raise to simulate row-level insert failures.
        if self.raise_on_execute:
            raise FakeError("row error")
        if self.raise_on_execute_if and _params is not None and self.raise_on_execute_if(_params):
            raise FakeError("row error")
        return None

    def executemany(self, _query, _records):
        # Optionally raise to simulate bulk insert failure.
        if self.raise_on_executemany:
            raise FakeError("bulk error")
        return None

    def close(self):
        # Match cursor.close usage in the production code.
        return None


class FakeConnection:
    def __init__(self, cursor):
        # Store the cursor to return for DB operations.
        self._cursor = cursor

    def __enter__(self):
        # Support context manager usage.
        return self

    def __exit__(self, exc_type, exc, tb):
        # Do not suppress exceptions.
        return False

    def cursor(self):
        # Provide the configured fake cursor.
        return self._cursor

    def close(self):
        # Mirror psycopg connection close.
        return None


@pytest.mark.db
def test_parse_date_invalid_returns_none():
    # Invalid date strings should return None.
    assert load_data.parse_date("not-a-date") is None
    assert load_data.parse_date(None) is None


@pytest.mark.db
def test_parse_float_handles_numeric_types():
    # Numeric inputs should round-trip to float.
    assert load_data.parse_float(3) == 3.0
    assert load_data.parse_float(2.5) == 2.5


@pytest.mark.db
def test_bulk_insert_reports_nul_fields(monkeypatch, capsys):
    # NUL bytes should be detected during row-level insert retry.
    records = [
        ("ok", None, None, "url-1", None, None, None, None, None, None, None, None, None, None),
        ("bad\x00value", None, None, "url-2", None, None, None, None, None, None, None, None, None, None),
    ]
    cursor = FakeCursor(
        raise_on_executemany=True,
        raise_on_execute_if=lambda params: any(isinstance(value, str) and "\x00" in value for value in params),
    )
    conn = FakeConnection(cursor)

    monkeypatch.setattr(load_data.psycopg, "Error", FakeError)

    with pytest.raises(FakeError):
        load_data.bulk_insert_with_skip_duplicates(conn, records)
    captured = capsys.readouterr()
    assert "contains NUL bytes" in captured.out


@pytest.mark.db
def test_main_handles_psycopg_error(monkeypatch):
    # Database errors should be handled without raising.
    monkeypatch.setattr(load_data.psycopg, "Error", FakeError)
    monkeypatch.setattr(load_data.psycopg, "connect", lambda **_kwargs: (_ for _ in ()).throw(FakeError()))

    load_data.main()


@pytest.mark.db
def test_main_handles_file_not_found(monkeypatch, capsys):
    # Missing input data should be handled without raising.
    monkeypatch.setattr(load_data.psycopg, "connect", lambda **_kwargs: FakeConnection(FakeCursor()))
    monkeypatch.setattr(load_data, "load_jsonl_data", lambda _path: (_ for _ in ()).throw(FileNotFoundError()))

    load_data.main()
    captured = capsys.readouterr()
    assert "applicant_data.json file not found" in captured.out


@pytest.mark.db
def test_main_handles_json_decode_error(monkeypatch, capsys):
    # JSON decoding errors should be handled without raising.
    monkeypatch.setattr(load_data.psycopg, "connect", lambda **_kwargs: FakeConnection(FakeCursor()))
    monkeypatch.setattr(
        load_data,
        "load_jsonl_data",
        lambda _path: (_ for _ in ()).throw(json.JSONDecodeError("bad", "doc", 0)),
    )

    load_data.main()
    captured = capsys.readouterr()
    assert "Error parsing JSON" in captured.out


@pytest.mark.db
def test_main_handles_unexpected_error(monkeypatch):
    # Unexpected exceptions should be handled without raising.
    monkeypatch.setattr(load_data.psycopg, "connect", lambda **_kwargs: FakeConnection(FakeCursor()))
    monkeypatch.setattr(load_data, "load_jsonl_data", lambda _path: (_ for _ in ()).throw(RuntimeError("boom")))

    load_data.main()


@pytest.mark.db
def test_module_main_executes_with_fake_db(monkeypatch, tmp_path):
    # Execute the __main__ block with a fake database connection.
    data_path = tmp_path / "data.json.jsonl"
    data_path.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(config, "APPLICANT_DATA_JSON_FILE", str(data_path))
    monkeypatch.setattr(psycopg, "connect", lambda **_kwargs: FakeConnection(FakeCursor()))

    runpy.run_module("load_data", run_name="__main__")
