import pytest
from flask import Flask

from app import create_app


@pytest.mark.web
def test_create_app_returns_flask_instance():
    # Ensure the factory returns a usable Flask app for testing.
    app = create_app()

    assert isinstance(app, Flask)
    assert app.test_client() is not None


@pytest.mark.web
def test_required_routes_are_registered():
    # Verify the app registers the core routes needed by the UI and API.
    app = create_app()
    routes = {rule.rule for rule in app.url_map.iter_rules()}

    assert "/" in routes
    assert "/analysis" in routes
    assert "/pull-data" in routes
    assert "/pull-status" in routes
    assert "/update-analysis" in routes


@pytest.mark.web
def test_required_route_methods_are_present():
    # Confirm each route exposes the expected HTTP methods.
    app = create_app()
    route_methods = {rule.rule: rule.methods for rule in app.url_map.iter_rules()}

    assert "GET" in route_methods["/"]
    assert "GET" in route_methods["/analysis"]
    assert "POST" in route_methods["/pull-data"]
    assert "GET" in route_methods["/pull-status"]
    assert "POST" in route_methods["/update-analysis"]


@pytest.mark.web
def test_analysis_page_loads(analysis_client):
    # Confirm the analysis page responds successfully.
    client = analysis_client()
    response = client.get("/analysis")

    assert response.status_code == 200


@pytest.mark.web
def test_analysis_page_contains_required_content(analysis_client):
    # Check for key labels/buttons in the rendered analysis page.
    client = analysis_client()
    response = client.get("/analysis")

    html = response.get_data(as_text=True)
    assert "Pull Data" in html
    assert "Update Analysis" in html
    assert "Analysis" in html
    assert "Answer:" in html
