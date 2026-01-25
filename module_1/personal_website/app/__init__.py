from flask import Flask

from app.contact_info import contact_info_bp
from app.main import main_bp
from app.projects import projects_bp

# Create the Flask application instance.
def create_app():
    app = Flask(__name__)

    # Register modular page blueprints.
    app.register_blueprint(main_bp)
    app.register_blueprint(contact_info_bp)
    app.register_blueprint(projects_bp)
    return app
