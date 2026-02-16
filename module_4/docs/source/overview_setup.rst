Overview and Setup
==================

Overview
--------
This project is a small Flask app that renders GradCafe analysis results from
PostgreSQL. The UI is served from ``/analysis`` and shows a list of questions
and answers from ``src/query_data.py``. Two buttons control data flow:

- Pull Data: starts the scraper in ``src/scrape.py`` (which then cleans and loads data).
- Update Analysis: refreshes the analysis results (blocked while a pull is running).

Setup
-----
1) Create and activate a virtual environment:

   .. code-block:: bash

      python -m venv venv
      source venv/bin/activate

2) Install dependencies:

   .. code-block:: bash

      pip install -r requirements.txt

3) Run the app:

   .. code-block:: bash

      python src/run.py

The server listens on ``HOST`` and ``PORT`` defined in ``src/config.py``.

Configuration and Environment
-----------------------------
Database settings are defined in ``src/config.py`` and can be provided either
via a single ``DATABASE_URL`` or via the individual settings below.

- ``DB_HOST``
- ``DB_PORT``
- ``DB_NAME``
- ``DB_USER``
- ``DB_PASSWORD``

When ``DATABASE_URL`` is set, the app will connect using that value. Otherwise,
it falls back to ``DB_HOST``, ``DB_PORT``, ``DB_NAME``, ``DB_USER``, and
``DB_PASSWORD``.
