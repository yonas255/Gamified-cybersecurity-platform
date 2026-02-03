from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from flags_local import FLAGS

bac_bp = Blueprint("bac", __name__)

@bac_bp.route("/lab/bac")
@login_required
def lab_bac():
    mode = request.args.get("mode", "vuln")
    flag = None

    if mode == "secure":
        # ✅ secure: enforce admin check
        if not current_user.is_admin:
            return render_template(
                "lab_bac.html",
                mode=mode,
                blocked=True,
                flag=None
            )

    # ❌ vulnerable OR admin user
    if mode == "vuln" and not current_user.is_admin:
        flag = FLAGS["bac"]

    return render_template(
        "lab_bac.html",
        mode=mode,
        blocked=False,
        flag=flag
    )
