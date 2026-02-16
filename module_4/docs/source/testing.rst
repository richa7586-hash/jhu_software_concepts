Testing Guide
=============

Run the full suite (coverage is enforced in ``pytest.ini``):

.. code-block:: bash

   pytest

Run a marked subset:

.. code-block:: bash

   pytest -m web
   pytest -m buttons
   pytest -m analysis
   pytest -m db
   pytest -m integration
   pytest -m scrape

Expected UI Selectors and Text
------------------------------
The tests look for these elements and labels on the analysis page:

- ``#pull-data`` button labeled "Pull Data"
- ``#update-analysis`` button labeled "Update Analysis"
- ``#status-message`` for status updates
- "Analysis" and "Answer:" text in the rendered output

Test Doubles and Fixtures
-------------------------
The suite uses fixtures and helpers to avoid real network, subprocess, and DB
calls:

- ``analysis_client`` and ``post_request`` in ``tests/conftest.py``.
- DB helpers in ``tests/utils/db_test_utils.py`` for stubbed inserts and queries.
- Scraper tests monkeypatch ``urllib3.request``, ``clean.clean_data``, and
  ``load_data.main`` to keep the run deterministic.
