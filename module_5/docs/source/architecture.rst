Architecture
============

Web Layer
---------
The Flask app lives in ``src/app/__init__.py`` and exposes routes for:

- Rendering analysis results (``/analysis``).
- Starting and monitoring the scraper (``/pull-data``, ``/pull-status``).
- Refreshing analysis output (``/update-analysis``).

The app queries PostgreSQL via ``psycopg`` and renders results with the
template in ``src/app/templates/index.html``.

For testability, ``create_app`` accepts dependency injection hooks for:

- Query map overrides (``question_map``)
- Database connection factory (``connect_fn``)
- DB connection kwargs (``db_kwargs_fn``)
- Pull starter (``start_pull_fn``)

ETL Layer
---------
The ETL flow is triggered by ``/pull-data``:

1) ``src/scrape.py`` scrapes list and detail pages and writes JSON.
2) ``src/clean.py`` cleans data via the LLM helper script.
3) ``src/load_data.py`` inserts cleaned rows into PostgreSQL.

Database Layer
--------------
All analytics are built from SQL in ``src/query_data.py`` against the table
configured in ``src/config.py``. The query results are mapped into the UI as
Answer payloads with labels and numeric formatting.
