import runpy

import pytest
import psycopg

import query_data


class FakeCursor:
    def __init__(self):
        # Track executed queries and close state.
        self.executed = []
        self.closed = False

    def execute(self, query):
        # Record each query for assertions.
        self.executed.append(query)

    def fetchall(self):
        # Return a simple one-row result for printing.
        return [(42,)]

    def close(self):
        # Mirror cursor.close in production.
        self.closed = True


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


@pytest.mark.db
def test_query_data_main_executes_queries(monkeypatch, capsys):
    # main should execute each query and print results.
    cursor = FakeCursor()
    monkeypatch.setattr(query_data, "question_sql_dict", {"Q1": "SELECT 1;", "Q2": "SELECT 2;"})
    monkeypatch.setattr(query_data.psycopg, "connect", lambda **_kwargs: FakeConnection(cursor))

    query_data.main()

    captured = capsys.readouterr()
    assert "Question 1: Q1" in captured.out
    assert "Question 2: Q2" in captured.out
    assert "42" in captured.out
    assert cursor.executed == ["SELECT 1;", "SELECT 2;"]
    assert cursor.closed is True


@pytest.mark.db
def test_query_data_module_main_executes(monkeypatch):
    # Running the module should execute main with the fake DB connection.
    cursor = FakeCursor()
    monkeypatch.setattr(psycopg, "connect", lambda **_kwargs: FakeConnection(cursor))

    runpy.run_module("query_data", run_name="__main__")
