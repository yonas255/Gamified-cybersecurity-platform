from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from flags_local import FLAGS

bac_bp = Blueprint("bac", __name__)

@bac_bp.route("/lab/bac")
@login_required
def lab_bac():
    mode = request.args.get("mode", "vuln")
    if mode not in ("vuln", "secure"):
        mode = "vuln"

    challenge_id = request.args.get("challenge_id", type=int)

    blocked = False
    flag = None

    # ✅ secure: enforce admin check
    if mode == "secure" and not getattr(current_user, "is_admin", False):
        blocked = True

    # ✅ vuln: normal users can access (broken), so reveal flag
    if mode == "vuln" and not getattr(current_user, "is_admin", False):
        flag = FLAGS["bac"]

    return render_template(
        "lab_bac.html",
        mode=mode,
        challenge_id=challenge_id,
        blocked=blocked,
        flag=flag
    )
