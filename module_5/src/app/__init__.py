from decimal import Decimal
from flask import Flask, jsonify, redirect, render_template, url_for
import os
import subprocess
import sys
import threading
import psycopg
import config
from query_data import question_sql_dict

_pull_lock = threading.Lock()
_pull_process = None

# Create the Flask application instance.
def create_app(question_map=None, connect_fn=None, db_kwargs_fn=None, start_pull_fn=None):
    app = Flask(__name__)
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src"))
    question_map = question_map or question_sql_dict
    connect_fn = connect_fn or psycopg.connect
    db_kwargs_fn = db_kwargs_fn or config.get_db_connect_kwargs

    def _default_start_pull():
        return subprocess.Popen(
            [sys.executable, os.path.join(base_dir, "scrape.py")],
            cwd=base_dir,
        )

    def _start_pull():
        if start_pull_fn is None:
            return _default_start_pull()
        return start_pull_fn(base_dir)

    def _coerce_numeric(value):
        if isinstance(value, Decimal):
            return float(value)
        return value

    def build_results():
        results = []
        with connect_fn(**db_kwargs_fn()) as conn:
            with conn.cursor() as cur:
                for question, query in question_map.items():
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

    def render_analysis_page():
        return render_template("index.html", results=build_results())

    @app.route("/")
    def index():
        return redirect(url_for("analysis"))

    @app.route("/analysis")
    def analysis():
        return render_analysis_page()

    @app.route("/pull-data", methods=["POST"])
    def pull_data():
        global _pull_process
        with _pull_lock:
            if _pull_process and _pull_process.poll() is None:
                return jsonify({"busy": True}), 409

            try:
                _pull_process = _start_pull()
            except Exception:
                return jsonify({"ok": False}), 500
        return jsonify({"ok": True})

    @app.route("/pull-status", methods=["GET"])
    def pull_status():
        with _pull_lock:
            running = _pull_process is not None and _pull_process.poll() is None
        return jsonify({"running": running})

    @app.route("/update-analysis", methods=["POST"])
    def update_analysis():
        with _pull_lock:
            if _pull_process and _pull_process.poll() is None:
                return jsonify({"busy": True}), 409

        render_analysis_page()
        return jsonify({"ok": True})

    # Register modular page blueprints
    return app
