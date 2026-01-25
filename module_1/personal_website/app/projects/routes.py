from flask import render_template

from app.projects import projects_bp


@projects_bp.route("/projects")
def projects():
    # Projects page listing module work with links.
    return render_template(
        "projects.html",
        page_title="Projects",
    )
