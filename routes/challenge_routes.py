import bcrypt
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from models import db
from models.challenge import Challenge
from models.submission import Submission
from models.user import User

challenge_bp = Blueprint("challenges", __name__)

@challenge_bp.route("/challenges")
@login_required
def list_challenges():
    challenges = Challenge.query.all()
    return render_template("challenges.html", challenges=challenges)

@challenge_bp.route("/challenges/<int:challenge_id>", methods=["GET", "POST"])
@login_required
def challenge_detail(challenge_id):
    challenge = Challenge.query.get_or_404(challenge_id)

    if request.method == "POST":
        submitted_flag = request.form.get("flag", "")

        # check flag against stored hash
        is_correct = bcrypt.checkpw(
            submitted_flag.encode("utf-8"),
            challenge.flag_hash.encode("utf-8")
        )

        # ✅ Check BEFORE inserting a new submission (avoids autoflush bug)
        already_correct = Submission.query.filter_by(
            user_id=current_user.id,
            challenge_id=challenge.id,
            is_correct=True
        ).first()

        # log submission (for audit trail)
        sub = Submission(
            user_id=current_user.id,
            challenge_id=challenge.id,
            is_correct=is_correct
        )
        db.session.add(sub)

        if is_correct and not already_correct:
            user = db.session.get(User, current_user.id)
            user.points += challenge.points
            flash(f"✅ Correct! +{challenge.points} points")
        elif is_correct and already_correct:
            flash("✅ Correct, but you already earned points for this challenge.")
        else:
            flash("❌ Incorrect flag. Try again.")

        db.session.commit()
        return redirect(url_for("challenges.challenge_detail", challenge_id=challenge.id))

    return render_template("challenge_detail.html", challenge=challenge)
