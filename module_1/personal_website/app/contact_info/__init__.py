from flask import Blueprint

# Blueprint for contact information routes.
contact_info_bp = Blueprint("contact_info", __name__, template_folder="templates")

from app.contact_info import routes
