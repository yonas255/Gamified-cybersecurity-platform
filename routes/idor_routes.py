from flask import Blueprint, request, render_template
from flask_login import login_required, current_user
from models.user import User
from flags_local import FLAGS

idor_bp = Blueprint("idor", __name__)

@idor_bp.route("/lab/idor")
@login_required
def lab_idor():
    mode = request.args.get("mode", "vuln")
    uid = request.args.get("uid", type=int)

    user = None
    flag = None

    if mode == "vuln":
        # ❌ vulnerable: no ownership check
        user = User.query.get(uid)
        if user and user.id != current_user.id:
            flag = FLAGS["idor"]

    else:
        # ✅ secure: enforce ownership
        if uid == current_user.id:
            user = current_user

    return render_template("lab_idor.html", mode=mode, user=user, flag=flag)