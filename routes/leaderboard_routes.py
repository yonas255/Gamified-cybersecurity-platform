from flask import Blueprint, render_template # flask routing tools
from flask_login import login_required # login protection

from models.user import User # the user model for querying data

leaderboard_bp = Blueprint("leaderboard", __name__) # creating the blueprint for the leaderboard feature
# leaderboard route
@leaderboard_bp.route("/leaderboard")
@login_required
def leaderboard():
    # retrieving all non admin users sorted by points in descending order
    users = User.query.filter_by(is_admin=False).order_by(User.points.desc()).all()
    # renders the leaderboard page with the results
    return render_template("leaderboard.html", users=users)

