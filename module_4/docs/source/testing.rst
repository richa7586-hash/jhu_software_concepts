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

Expected UI Selectors and Text
------------------------------
The tests look for these elements and labels on the analysis page:

- ``#pull-data`` button labeled "Pull Data" (``data-testid="pull-data-btn"``)
- ``#update-analysis`` button labeled "Update Analysis" (``data-testid="update-analysis-btn"``)
- ``#status-message`` for status updates (``data-testid="status-message"``)
- "Analysis" title text and "Answer:" labels in the rendered output

Test Doubles and Fixtures
-------------------------
The suite uses fixtures and helpers to avoid real network, subprocess, and DB
calls:

- ``analysis_client`` and ``post_request`` in ``tests/conftest.py``.
- Dependency injection hooks passed to ``create_app`` allow tests to provide
  fake DB connections and pull starters without patching globals.
- DB helpers in ``tests/utils/db_test_utils.py`` for stubbed inserts and queries.
- Scraper tests monkeypatch ``urllib3.request``, ``clean.clean_data``, and
  ``load_data.main`` to keep the run deterministic.

Error-path Coverage
-------------------
There is a negative-path test for pull failures. When the pull starter raises
an exception, ``/pull-data`` returns HTTP 500 with ``{"ok": false}``, and tests
verify that no rows are inserted.
