from flask import Blueprint, request, render_template # flask tools
from flask_login import login_required, current_user # authentication utilities
from models.user import User # user model
from flags_local import FLAGS # stored flags for the lab

# creating the blueprint for the Inscure Dircet Object Reference lab
idor_bp = Blueprint("idor", __name__)

# the lab route, determining the mode (vulnerable/ secure), retrieving user ID and challenge ID request parameters.
@idor_bp.route("/lab/idor")
@login_required
def lab_idor():
    mode = request.args.get("mode", "vuln")
    if mode not in ("vuln", "secure"):
        mode = "vuln"

    # fetching the target user from the database and intitialize variables to control access and flag display
    uid = request.args.get("uid", type=int) or current_user.id
    challenge_id = request.args.get("challenge_id", type=int)

    target_user = User.query.get(uid)

    denied = False
    flag = None

    if not target_user:
        denied = True

    #  in secure: block before sending data/ users from accessing others users data unless they are admin
    if mode == "secure" and uid != current_user.id and not getattr(current_user, "is_admin", False):
        denied = True
        target_user = None  #  IMPORTANT: prevent leaking data to template

    #  in vuln: allows unautorized access and reveals the flag when a user tries to access another users data
    if mode == "vuln" and target_user and uid != current_user.id:
        flag = FLAGS["idor"]
    
    # renders the lab template with all relevant data with access status, selected user, and flag if exposed
    return render_template(
        "lab_idor.html",
        mode=mode,
        challenge_id=challenge_id,
        uid=uid,
        target_user=target_user,
        denied=denied,
        flag=flag
    )
