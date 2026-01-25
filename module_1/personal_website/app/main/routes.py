from flask import render_template

from app.main import main_bp


@main_bp.route("/")
def home():
    # Homepage with bio content and profile image.
    return render_template(
        "index.html",
        page_title="Bio",
    )
