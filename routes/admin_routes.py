from flask import Blueprint, render_template
from flask_login import current_user, login_required
from decorators import admin_required
import bcrypt
from flask import request, redirect, url_for, flash
from models import db
from models.challenge import Challenge
from audit import audit
admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

@admin_bp.route("/")
@login_required
@admin_required
def dashboard():
    return render_template("admin/admin_dashboard.html")

@admin_bp.route("/challenges/new", methods=["GET", "POST"])
@login_required
@admin_required
def create_challenge():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        difficulty = request.form.get("difficulty", "Beginner").strip()
        lab_type = request.form.get("lab_type", "none").strip()
        points = int(request.form.get("points", "100"))

        flag_plain = request.form.get("flag", "").strip()

        # ✅ Validate first
        if not title or not description or not flag_plain:
            flash("Title, description, and flag are required.")
            return redirect(url_for("admin.create_challenge"))

        # ✅ Hash the flag before saving
        flag_hash = bcrypt.hashpw(
            flag_plain.encode("utf-8"),
            bcrypt.gensalt()
        ).decode("utf-8")

        c = Challenge(
            title=title,
            difficulty=difficulty,
            points=points,
            lab_type=lab_type,
            description=description,
            flag_hash=flag_hash
        )

        db.session.add(c)
        db.session.commit()

        flash("Challenge created successfully.")
        audit("ADMIN_CREATE_CHALLENGE", current_user, {"title": title})
        return redirect(url_for("admin.dashboard"))

    return render_template("admin/challenge_create.html")


@admin_bp.route("/challenges")
@login_required
@admin_required
def manage_challenges():
    challenges = Challenge.query.order_by(Challenge.id.desc()).all()
    return render_template("admin/challenge_manage.html", challenges=challenges)

@admin_bp.route("/challenges/<int:challenge_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def edit_challenge(challenge_id):
    c = Challenge.query.get_or_404(challenge_id)

    if request.method == "POST":
        c.title = request.form.get("title", "").strip()
        c.description = request.form.get("description", "").strip()
        c.difficulty = request.form.get("difficulty", "Beginner").strip()
        c.points = int(request.form.get("points", "100"))
        c.lab_type = request.form.get("lab_type", "none").strip()

        new_flag = request.form.get("flag", "").strip()
        if new_flag:
            c.flag_hash = bcrypt.hashpw(new_flag.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        db.session.commit()
        flash("Challenge updated.")
        audit("ADMIN_DELETE_CHALLENGE", current_user, {"challenge_id": c.id})
        return redirect(url_for("admin.manage_challenges"))

    return render_template("admin/challenge_edit.html", c=c)

@admin_bp.route("/challenges/<int:challenge_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_challenge(challenge_id):
    c = Challenge.query.get_or_404(challenge_id)
    db.session.delete(c)
    db.session.commit()
    flash("Challenge deleted.")
    audit("ADMIN_DELETE_CHALLENGE", current_user, {"challenge_id": c.id})
    return redirect(url_for("admin.manage_challenges"))
