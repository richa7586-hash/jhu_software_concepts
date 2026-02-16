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
There are no required environment variables by default. Database settings are
defined in ``src/config.py``:

- ``DB_HOST``
- ``DB_PORT``
- ``DB_NAME``
- ``DB_USER``
- ``DB_PASSWORD``

If you prefer environment variables (for example, a single ``DATABASE_URL``),
update ``src/config.py`` to read from ``os.environ`` and map those values.
One simple pattern is to read ``DATABASE_URL`` (or ``DB_HOST``, ``DB_PORT``,
``DB_NAME``, ``DB_USER``, ``DB_PASSWORD``) in ``src/config.py`` and fall back
to the current defaults.
