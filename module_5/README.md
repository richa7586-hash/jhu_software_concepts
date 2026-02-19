# JHED ID A68B60

# jhu_software_concepts - Module 5 - Software Assurance + Secure SQL (SQLi Defense) Assignment - Due by Feb 23, 2026


# How It Works

# Requirements
- Python 3.10+
- pip

# Setup
1) Change into the app folder:
   cd module_4
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

# Build Documentation
Generate the Sphinx HTML docs:
  make -C docs html

Output goes to:
  docs/build/html

If make is unavailable, run:
  sphinx-build -M html docs/source docs/build

# Read the Docs
This repo includes a ``.readthedocs.yml`` file for Read the Docs builds.
After pushing to GitHub:
1) Sign in to Read the Docs and import the repository.
2) Ensure the default branch is selected.
3) Trigger a build; docs will be built from ``docs/source``.

Docs URL:
https://jhu-software-concepts-module-4-richa.readthedocs.io/en/latest/
