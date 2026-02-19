"""
Flask app entrypoint and route overview.

Routes:
- GET / -> redirect to /analysis
- GET /analysis -> render analysis page
- POST /pull-data -> start the scraper subprocess
- GET /pull-status -> report whether a pull is running
- POST /update-analysis -> refresh analysis results
"""

from app import create_app

__all__ = ["create_app"]
