import pytest

import app
import flask_app


@pytest.mark.web
def test_flask_app_exports_create_app():
    # flask_app should re-export the Flask app factory.
    assert flask_app.create_app is app.create_app
    assert flask_app.__all__ == ["create_app"]
