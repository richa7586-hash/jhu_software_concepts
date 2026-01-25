from flask import Blueprint

# Blueprint for main page routes.
main_bp = Blueprint("main", __name__, template_folder="templates")

from app.main import routes
