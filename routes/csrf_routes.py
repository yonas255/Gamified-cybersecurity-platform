import secrets
from flask import Blueprint, request, render_template, redirect, url_for
from flask_login import login_required, current_user
from flags_local import FLAGS

csrf_bp = Blueprint("csrf", __name__)

def _mode():
    m = request.args.get("mode", "vuln")
    return m if m in ("vuln", "secure") else "vuln"

@csrf_bp.route("/lab/csrf", methods=["GET"])
@login_required
def csrf_attacker_page():
    mode = _mode()
    challenge_id = request.args.get("challenge_id", type=int)

    # simple per-session token (for demo). If you use flask session, store there.
    # For now, we generate a token and send it to the template in secure mode.
    csrf_token = None
    if mode == "secure":
        csrf_token = secrets.token_urlsafe(16)

    return render_template(
        "lab_csrf.html",
        mode=mode,
        challenge_id=challenge_id,
        message=None,
        flag=None,
        csrf_token=csrf_token
    )

@csrf_bp.route("/lab/csrf/victim", methods=["POST"])
@login_required
def csrf_victim_endpoint():
    mode = _mode()
    challenge_id = request.args.get("challenge_id", type=int)

    flag = None
    message = None

    if mode == "vuln":
        # ❌ no CSRF protection: forged request succeeds
        flag = FLAGS["csrf"]
        message = "✅ Victim request accepted. Email changed without CSRF protection."
    else:
        # ✅ secure: require token
        token = request.form.get("csrf_token", "")
        # In a real app you'd compare with session-stored token.
        # For this demo we expect token == "VALID"
        if token == "VALID":
            message = "✅ Request accepted (valid CSRF token)."
        else:
            message = "❌ Request blocked: missing/invalid CSRF token."

    return render_template(
        "lab_csrf_result.html",
        mode=mode,
        challenge_id=challenge_id,
        message=message,
        flag=flag
    )
