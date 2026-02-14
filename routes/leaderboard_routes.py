from flask import Blueprint, render_template
from flask_login import login_required

from models.user import User

leaderboard_bp = Blueprint("leaderboard", __name__)

@leaderboard_bp.route("/leaderboard")
@login_required
def leaderboard():
    users = User.query.filter_by(is_admin=False).order_by(User.points.desc()).all()
    return render_template("leaderboard.html", users=users)

