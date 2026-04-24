import bcrypt # library for hashing
from flask import Blueprint, render_template, request, redirect, url_for, flash # flask routing
from flask_login import login_required, current_user # authentication

from models import db # databese models
from models.challenge import Challenge
from models.submission import Submission
from models.user import User
from rate_limiter import check # rate limiting

# creating a blueprint for challenge based routes 
challenge_bp = Blueprint("challenges", __name__)

# retrieving all correctly completed challenges IDs for a exact user to track progress
def completed_ids_for_user(user_id: int) -> set[int]:
    subs = Submission.query.filter_by(user_id=user_id, is_correct=True).all()
    return {s.challenge_id for s in subs}

# unlocking logic for challenges depends on difficulty levels
# ensuring users completed beginner and medium levels befor approaching the harder level while allowing admin full access
def is_unlocked(challenge: Challenge, done_ids: set[int]) -> bool:
    # allowing Admin to access everything
    if current_user.is_authenticated and getattr(current_user, "is_admin", False):
        return True

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

# displaying all challenges, marking each as completed or locked or unlocked depends on the user progress
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

# managing viewing and submitting a specific challenge
# enforcing access control, applies rate limiting on submissions,
# verifying the flag using hashing, logs the attempts
# updates user points if correct
# providing feedback messages before saving to the database
@challenge_bp.route("/challenges/<int:challenge_id>", methods=["GET", "POST"])
@login_required
def challenge_detail(challenge_id):
    challenge = Challenge.query.get_or_404(challenge_id)
    
    done_ids = completed_ids_for_user(current_user.id)
    if not is_unlocked(challenge, done_ids):
        flash("This level is locked. Complete previous level challenges first.")
        return redirect(url_for("challenges.list_challenges"))
    
    if request.method == "POST":
        key = f"flag:{current_user.id}:{challenge.id}"
        allowed, remaining, retry_after = check(key, limit=10, window_seconds=60)
        if not allowed:
            flash(f"Too many flag attempts. Try again in {retry_after}s.")
            return redirect(url_for("challenges.challenge_detail", challenge_id=challenge.id))

        
        submitted_flag = request.form.get("flag", "")

        # check flag against stored hash
        is_correct = bcrypt.checkpw(
            submitted_flag.encode("utf-8"),
            challenge.flag_hash.encode("utf-8")
        )

        #  Checking before inserting a new submission (avoids auto flush bug)
        already_correct = Submission.query.filter_by(
            user_id=current_user.id,
            challenge_id=challenge.id,
            is_correct=True
        ).first()

        # logging submission for audit
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
