from flask import Blueprint, render_template, request # flask tools
from flask_login import login_required, current_user # login protection, current users
from flags_local import FLAGS # locally storing flags for the lab

# creating the blueprint for the broken access control(BAC) lab routes
bac_bp = Blueprint("bac", __name__)

# defining the bac lab route
@bac_bp.route("/lab/bac")
@login_required
# determine weather the app runs in vulnerable or secure mode
# checks user permission
def lab_bac():
    mode = request.args.get("mode", "vuln")
    if mode not in ("vuln", "secure"):
        mode = "vuln"

    # simulate improper access control in vuln mode by exposing the flag
    challenge_id = request.args.get("challenge_id", type=int)

    blocked = False
    flag = None

    #  blocking unauthorized access in secure mode before rendering the lab page
    if mode == "secure" and not getattr(current_user, "is_admin", False):
        blocked = True

    # normal users can access (broken), so reveal flag (vuln)
    if mode == "vuln" and not getattr(current_user, "is_admin", False):
        flag = FLAGS["bac"]

    return render_template(
        "lab_bac.html",
        mode=mode,
        challenge_id=challenge_id,
        blocked=blocked,
        flag=flag
    )
