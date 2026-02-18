from flask import Blueprint, request, render_template
from flask_login import login_required, current_user
from models.user import User
from flags_local import FLAGS

idor_bp = Blueprint("idor", __name__)

@idor_bp.route("/lab/idor")
@login_required
def lab_idor():
    mode = request.args.get("mode", "vuln")
    if mode not in ("vuln", "secure"):
        mode = "vuln"

    uid = request.args.get("uid", type=int) or current_user.id
    challenge_id = request.args.get("challenge_id", type=int)

    target_user = User.query.get(uid)

    denied = False
    flag = None

    if not target_user:
        denied = True

    #  secure: block before sending data
    if mode == "secure" and uid != current_user.id and not getattr(current_user, "is_admin", False):
        denied = True
        target_user = None  #  IMPORTANT: prevent leaking data to template

    #  vuln: flag only when accessing other user
    if mode == "vuln" and target_user and uid != current_user.id:
        flag = FLAGS["idor"]

    return render_template(
        "lab_idor.html",
        mode=mode,
        challenge_id=challenge_id,
        uid=uid,
        target_user=target_user,
        denied=denied,
        flag=flag
    )
