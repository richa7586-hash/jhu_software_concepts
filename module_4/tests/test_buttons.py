import os
import sys

import pytest

import app as app_module


class BusyProcess:
    def poll(self):
        # Indicate the fake process is still running.
        return None


def _setup_pull_data(monkeypatch):
    # Stub subprocess.Popen to capture pull-data start parameters.
    started = {}

    def fake_popen(args, cwd):
        # Track the arguments used to start the scraper.
        started["args"] = args
        started["cwd"] = cwd
        return BusyProcess()

    monkeypatch.setattr(app_module, "_pull_process", None)
    monkeypatch.setattr(app_module.subprocess, "Popen", fake_popen)

    return started


@pytest.mark.buttons
def test_pull_data_returns_200(monkeypatch, post_request):
    # Confirm the pull-data endpoint responds successfully.
    _setup_pull_data(monkeypatch)
    response = post_request("/pull-data")

    assert response.status_code == 200


@pytest.mark.buttons
def test_pull_data_starts_scrape_process(monkeypatch, post_request):
    # Ensure pull-data starts the scraper process without running the real script.
    started = _setup_pull_data(monkeypatch)
    response = post_request("/pull-data")

    assert response.get_json() == {"status": "started"}
    assert started["args"][0] == sys.executable
    assert os.path.basename(started["args"][1]) == "scrape.py"
    assert started["cwd"] == os.path.abspath(os.path.join(os.path.dirname(app_module.__file__), "../../src"))
    assert app_module._pull_process is not None


@pytest.mark.buttons
def test_update_analysis_returns_200_when_not_busy(monkeypatch, post_request):
    # Confirm update-analysis returns success when no pull is running.
    monkeypatch.setattr(app_module, "_pull_process", None)

    response = post_request("/update-analysis")

    assert response.status_code == 200
    assert response.get_json() == {"status": "updated"}


@pytest.mark.buttons
def test_update_analysis_returns_409_when_busy(monkeypatch, post_request):
    # Ensure update-analysis is blocked when a pull is already running.
    monkeypatch.setattr(app_module, "_pull_process", BusyProcess())

    response = post_request("/update-analysis")

    assert response.status_code == 409
    assert response.get_json() == {"status": "running"}


@pytest.mark.buttons
def test_pull_data_returns_409_when_busy(monkeypatch, post_request):
    # Ensure pull-data is blocked when a pull is already running.
    def fail_popen(*_args, **_kwargs):
        # Fail fast if the endpoint tries to start a process.
        raise AssertionError("pull-data should not start when busy")

    monkeypatch.setattr(app_module, "_pull_process", BusyProcess())
    monkeypatch.setattr(app_module.subprocess, "Popen", fail_popen)

    response = post_request("/pull-data")

    assert response.status_code == 409
    assert response.get_json() == {"status": "running"}


@pytest.mark.buttons
def test_pull_status_reflects_running_process(monkeypatch):
    # Confirm pull-status reports a running pull.
    monkeypatch.setattr(app_module, "_pull_process", BusyProcess())

    app = app_module.create_app()
    client = app.test_client()
    response = client.get("/pull-status")

    assert response.status_code == 200
    assert response.get_json() == {"running": True}
