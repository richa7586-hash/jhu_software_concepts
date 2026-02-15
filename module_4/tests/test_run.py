import runpy
import sys
from types import SimpleNamespace

import pytest

import config


class DummyApp:
    def __init__(self, started):
        # Capture run() arguments in the provided dict.
        self._started = started

    def run(self, host=None, port=None, debug=None):
        # Store invocation details for assertions.
        self._started["host"] = host
        self._started["port"] = port
        self._started["debug"] = debug


def _install_fake_app(monkeypatch, started):
    # Replace the app module so run.py uses a controllable create_app.
    fake_app = SimpleNamespace(create_app=lambda: DummyApp(started))
    monkeypatch.setitem(sys.modules, "app", fake_app)


@pytest.mark.web
def test_run_main_rejects_old_python(monkeypatch):
    # __main__ should raise on Python versions below 3.10.
    started = {}
    _install_fake_app(monkeypatch, started)
    monkeypatch.setattr(sys, "version_info", (3, 9))

    with pytest.raises(RuntimeError):
        runpy.run_module("run", run_name="__main__")
    assert started == {}


@pytest.mark.web
def test_run_main_calls_app_run(monkeypatch):
    # __main__ should run the app with configured host/port when supported.
    started = {}
    _install_fake_app(monkeypatch, started)
    monkeypatch.setattr(sys, "version_info", (3, 10))

    runpy.run_module("run", run_name="__main__")

    assert started["host"] == config.HOST
    assert started["port"] == config.PORT
    assert started["debug"] is True
