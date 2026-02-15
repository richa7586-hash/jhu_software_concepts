import os
import sys
from types import SimpleNamespace

import pytest


# Ensure the app package is importable in tests.
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_ROOT = os.path.join(PROJECT_ROOT, "src")
if SRC_ROOT not in sys.path:
    sys.path.insert(0, SRC_ROOT)


import app as app_module
from app import create_app


# Factory fixture to build a client for /analysis with stubbed DB rows.
@pytest.fixture
def analysis_client(monkeypatch):
    # Build a test client with stubbed DB access for /analysis.
    def _build(rows=None, question="Q1"):
        # Create a client using a fake DB connection that returns provided rows.
        class DummyCursor:
            def __init__(self):
                # Provide column metadata needed by the app.
                self.description = [SimpleNamespace(name="value")]

            def __enter__(self):
                # Support context manager usage in DB cursor.
                return self

            def __exit__(self, exc_type, exc, tb):
                # Do not suppress exceptions from the context manager.
                return False

            def execute(self, query):
                # No-op for stubbed queries.
                return None

            def fetchall(self):
                # Return the configured rows for the test.
                return [(1,)] if rows is None else rows

        class DummyConnection:
            def __enter__(self):
                # Support context manager usage in DB connection.
                return self

            def __exit__(self, exc_type, exc, tb):
                # Do not suppress exceptions from the context manager.
                return False

            def cursor(self):
                # Return a stubbed cursor for query execution.
                return DummyCursor()

        monkeypatch.setattr(app_module, "question_sql_dict", {question: "SELECT 1;"})
        monkeypatch.setattr(app_module.psycopg, "connect", lambda **kwargs: DummyConnection())

        app = app_module.create_app()
        return app.test_client()

    return _build


# Small helper fixture to post to a route with a fresh test client.
@pytest.fixture
def post_request():
    # Helper to post to a route using a fresh test client.
    def _post(path, **kwargs):
        # Create a new client for each POST request.
        app = create_app()
        client = app.test_client()
        return client.post(path, **kwargs)

    return _post
