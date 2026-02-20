"""Run the Flask application entrypoint."""

import sys

from app import create_app
from config import HOST, PORT

# Create the Flask application instance for the entrypoint.
app = create_app()

if __name__ == "__main__":
    # Returns error if Python version is less than 3.10.
    if sys.version_info < (3, 10):
        raise RuntimeError("Python 3.10+ is required.")
    app.run(host=HOST, port=PORT, debug=True)
