from flask import Flask, render_template
import psycopg
import config
from query_data import question_sql_dict

# Create the Flask application instance.
def create_app():
    app = Flask(__name__)

    @app.route("/")
    def index():
        results = []
        with psycopg.connect(
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

        return render_template("index.html", results=results)

    # Register modular page blueprints
    return app
