import secrets # libraries for secure token generation
from flask import Blueprint, request, render_template, redirect, url_for # flask routing
from flask_login import login_required, current_user # authentication
from flags_local import FLAGS # access to store flags

# creating a blueprint for CSRF lab routes.
csrf_bp = Blueprint("csrf", __name__)

# a helper function to know whether the lab runs in vulnerable or secure mode.
def _mode():
    m = request.args.get("mode", "vuln")
    return m if m in ("vuln", "secure") else "vuln"

# displaying the CSRF attacker page

@csrf_bp.route("/lab/csrf", methods=["GET"])
@login_required
def csrf_attacker_page():
    mode = _mode()
    challenge_id = request.args.get("challenge_id", type=int)

    # optionally generates a CSRF token in secure mode
    # generating a token and send it to the template in secure mode.
    csrf_token = None
    if mode == "secure":
        csrf_token = secrets.token_urlsafe(16)
    
    # passes all required data to the template
    return render_template(
        "lab_csrf.html",
        mode=mode,
        challenge_id=challenge_id,
        message=None,
        flag=None,
        csrf_token=csrf_token
    )

# simulating the victim endpoint

@csrf_bp.route("/lab/csrf/victim", methods=["POST"])
@login_required
# demonstrating CSRF vulnerability by accepting request without validation in vuln mode
def csrf_victim_endpoint():
    mode = _mode()
    challenge_id = request.args.get("challenge_id", type=int)

    flag = None
    message = None

    if mode == "vuln":
        # forged request succeeds if there is no CSRF protection
        flag = FLAGS["csrf"]
        message = "✅ Victim request accepted. Email changed without CSRF protection."
    else:
        # secure: require token
        token = request.form.get("csrf_token", "")
        # enforcing token validation in secure mode before returning the result
        # expecting token == "VALID"
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
