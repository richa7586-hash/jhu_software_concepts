"""Flask application factory and routes."""

from dataclasses import dataclass
from decimal import Decimal
import os
import subprocess
import sys
import threading

from flask import Flask, jsonify, redirect, render_template, url_for
import psycopg
import config
from query_data import question_sql_dict

PULL_LOCK = threading.Lock()
_pull_state = {"process": None}


@dataclass(frozen=True)
class AppDeps:
    """Container for app dependency wiring."""
    base_dir: str
    question_map: dict
    connect_fn: object
    db_kwargs_fn: object
    start_pull_fn: object


def _coerce_numeric(value):
    if isinstance(value, Decimal):
        return float(value)
    return value


def _build_results(deps):
    results = []
    with deps.connect_fn(**deps.db_kwargs_fn()) as conn:
        with conn.cursor() as cur:
            for question, query in deps.question_map.items():
                cur.execute(query)
                rows = cur.fetchall()
                columns = [desc.name for desc in cur.description] if cur.description else []

                if not rows:
                    payload = None
                elif len(columns) == 1 and len(rows) == 1:
                    payload = _coerce_numeric(rows[0][0])
                elif len(columns) == 1:
                    payload = [_coerce_numeric(row[0]) for row in rows]
                else:
                    payload = [
                        {col: _coerce_numeric(value) for col, value in zip(columns, row)}
                        for row in rows
                    ]

                results.append({
                    "question": question,
                    "columns": columns,
                    "answer": payload,
                })
    return results


def _render_analysis_page(deps):
    return render_template("index.html", results=_build_results(deps))


def _default_start_pull(base_dir):
    return subprocess.Popen(
        [sys.executable, os.path.join(base_dir, "scrape.py")],
        cwd=base_dir,
    )


def _register_routes(app, deps):
    def _start_pull():
        if deps.start_pull_fn is None:
            return _default_start_pull(deps.base_dir)
        return deps.start_pull_fn(deps.base_dir)

    @app.route("/")
    def index():
        return redirect(url_for("analysis"))

    @app.route("/analysis")
    def analysis():
        return _render_analysis_page(deps)

    @app.route("/pull-data", methods=["POST"])
    def pull_data():
        with PULL_LOCK:
            if _pull_state["process"] and _pull_state["process"].poll() is None:
                return jsonify({"busy": True}), 409

            try:
                _pull_state["process"] = _start_pull()
            except (OSError, subprocess.SubprocessError):
                return jsonify({"ok": False}), 500
        return jsonify({"ok": True})

    @app.route("/pull-status", methods=["GET"])
    def pull_status():
        with PULL_LOCK:
            running = _pull_state["process"] is not None and _pull_state["process"].poll() is None
        return jsonify({"running": running})

    @app.route("/update-analysis", methods=["POST"])
    def update_analysis():
        with PULL_LOCK:
            if _pull_state["process"] and _pull_state["process"].poll() is None:
                return jsonify({"busy": True}), 409

        _render_analysis_page(deps)
        return jsonify({"ok": True})


# Create the Flask application instance.
def create_app(question_map=None, connect_fn=None, db_kwargs_fn=None, start_pull_fn=None):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src"))
    question_map = question_map or question_sql_dict
    connect_fn = connect_fn or psycopg.connect
    db_kwargs_fn = db_kwargs_fn or config.get_db_connect_kwargs

    deps = AppDeps(
        base_dir=base_dir,
        question_map=question_map,
        connect_fn=connect_fn,
        db_kwargs_fn=db_kwargs_fn,
        start_pull_fn=start_pull_fn,
    )
    _register_routes(app, deps)
    return app
