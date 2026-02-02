from flask import Blueprint, request, render_template
from flask_login import login_required, current_user
from flags_local import FLAGS

csrf_bp = Blueprint("csrf", __name__)

@csrf_bp.route("/lab/csrf", methods=["GET", "POST"])
@login_required
def lab_csrf():
    mode = request.args.get("mode", "vuln")
    flag = None
    message = None

    if request.method == "POST":
        if mode == "vuln":
            # ❌ no CSRF protection
            flag = FLAGS["csrf"]
            message = "Email updated without CSRF protection."
        else:
            # ✅ secure version would require CSRF token
            message = "Request blocked due to missing CSRF token."

    return render_template("lab_csrf.html", mode=mode, message=message, flag=flag)
