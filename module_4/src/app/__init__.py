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
def create_app():
    app = Flask(__name__)
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

    def build_results():
        results = []
        with psycopg.connect(
            dbname=config.DB_NAME,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            host=config.DB_HOST,
            port=config.DB_PORT,
        ) as conn:
            with conn.cursor() as cur:
                for question, query in question_sql_dict.items():
                    cur.execute(query)
                    rows = cur.fetchall()
                    columns = [desc.name for desc in cur.description] if cur.description else []

                    if not rows:
                        payload = None
                    elif len(columns) == 1 and len(rows) == 1:
                        payload = rows[0][0]
                    elif len(columns) == 1:
                        payload = [row[0] for row in rows]
                    else:
                        payload = [dict(zip(columns, row)) for row in rows]

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
                return jsonify({"status": "running"}), 409

            _pull_process = subprocess.Popen(
                [sys.executable, os.path.join(base_dir, "scrape.py")],
                cwd=base_dir,
            )
        return jsonify({"status": "started"})

    @app.route("/pull-status", methods=["GET"])
    def pull_status():
        with _pull_lock:
            running = _pull_process is not None and _pull_process.poll() is None
        return jsonify({"running": running})

    @app.route("/update-analysis", methods=["POST"])
    def update_analysis():
        with _pull_lock:
            if _pull_process and _pull_process.poll() is None:
                return jsonify({"status": "running"}), 409

        subprocess.run(
            [sys.executable, os.path.join(base_dir, "load_data.py")],
            cwd=base_dir,
            check=True,
        )
        return jsonify({"status": "updated"})

    # Register modular page blueprints
    return app
