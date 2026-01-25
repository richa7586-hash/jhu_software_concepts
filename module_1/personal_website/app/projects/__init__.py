from flask import Blueprint

# Blueprint for projects page routes.
projects_bp = Blueprint("projects", __name__, template_folder="templates")

from app.projects import routes
