from flask import render_template

from app.contact_info import contact_info_bp


@contact_info_bp.route("/contact_info")
def contact_info():
    # Contact info page with email and LinkedIn details.
    return render_template(
        "contact_info.html",
        page_title="Contact Info",
    )
