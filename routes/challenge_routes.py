import bcrypt
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from models import db
from models.challenge import Challenge
from models.submission import Submission
from models.user import User


challenge_bp = Blueprint("challenges", __name__)

def completed_ids_for_user(user_id: int) -> set[int]:
    subs = Submission.query.filter_by(user_id=user_id, is_correct=True).all()
    return {s.challenge_id for s in subs}


def is_unlocked(challenge: Challenge, done_ids: set[int]) -> bool:
    if challenge.difficulty == "Beginner":
        return True

    beginner_ids = {c.id for c in Challenge.query.filter_by(difficulty="Beginner").all()}
    medium_ids   = {c.id for c in Challenge.query.filter_by(difficulty="Medium").all()}

    beginner_done = beginner_ids.issubset(done_ids)
    medium_done   = medium_ids.issubset(done_ids)

    if challenge.difficulty == "Medium":
        return beginner_done
    if challenge.difficulty == "Hard":
        return beginner_done and medium_done
    return True


@challenge_bp.route("/challenges")
@login_required
def list_challenges():
    challenges = Challenge.query.all()
    done_ids = completed_ids_for_user(current_user.id)

    rows = []
    for c in challenges:
        rows.append({
            "c": c,
            "done": c.id in done_ids,
            "unlocked": is_unlocked(c, done_ids)
        })

    return render_template("challenges.html", rows=rows)


@challenge_bp.route("/challenges/<int:challenge_id>", methods=["GET", "POST"])
@login_required
def challenge_detail(challenge_id):
    challenge = Challenge.query.get_or_404(challenge_id)
    
    done_ids = completed_ids_for_user(current_user.id)
    if not is_unlocked(challenge, done_ids):
        flash("This level is locked. Complete previous level challenges first.")
        return redirect(url_for("challenges.list_challenges"))
    
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
