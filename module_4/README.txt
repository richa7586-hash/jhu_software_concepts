# JHED ID A68B60

# jhu_software_concepts - Module 4 - Testing and Documentation Assignment - Due by Feb 15, 2026


# How It Works
This project is a small Flask app that renders GradCafe analysis results from PostgreSQL.
- /analysis renders the analysis page by running queries in src/query_data.py.
- /pull-data kicks off the scraper (src/scrape.py) in a subprocess; the scraper writes JSON, cleans it, and loads data.
- /update-analysis refreshes the analysis (and returns a JSON status when not busy).

The test suite uses pytest with markers to group tests by behavior:
- web: Flask routes and page load/HTML structure.
- buttons: button endpoints and busy-state behavior.
- analysis: analysis labels and percentage formatting.
- db: database schema/inserts/selects and helpers.
- integration: end-to-end flows.
- scrape: scraper parsing and data flow behavior.

# Requirements
- Python 3.10+
- pip

# Setup
1) Change into the app folder:
   cd module4
2) Create and activate a virtual environment (optional but recommended):
   python -m venv venv
   source venv/bin/activate
3) Install dependencies:
   pip install -r requirements.txt

# How to Run Tests
Run the full suite (coverage is enforced in pytest.ini):
  pytest

Run a specific category:
  pytest -m web
  pytest -m buttons
  pytest -m analysis
  pytest -m db
  pytest -m integration
  pytest -m scrape

Tip: The tests are designed to stub network, subprocess, and database calls, so they can run quickly without external services.


