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


# Provide a client that renders /analysis without hitting a real database.
@pytest.fixture
def analysis_client(monkeypatch):
    class DummyCursor:
        def __init__(self):
            self.description = [SimpleNamespace(name="value")]

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def execute(self, query):
            return None

        def fetchall(self):
            return [(1,)]

    class DummyConnection:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def cursor(self):
            return DummyCursor()

    monkeypatch.setattr(app_module, "question_sql_dict", {"Q1": "SELECT 1;"})
    monkeypatch.setattr(app_module.psycopg, "connect", lambda **kwargs: DummyConnection())

    app = app_module.create_app()
    return app.test_client()


# Small helper fixture to post to a route with a fresh test client.
@pytest.fixture
def post_request():
    def _post(path, **kwargs):
        app = create_app()
        client = app.test_client()
        return client.post(path, **kwargs)

    return _post
