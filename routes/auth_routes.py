import bcrypt
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user, login_user, logout_user, login_required
from audit import audit
from models import db
from models.user import User

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Username and password are required!")
            return redirect(url_for("auth.register"))

        existing = User.query.filter_by(username=username).first()
        if existing:
            flash("Username already exists")
            return redirect(url_for("auth.register"))

        pw_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        user = User(username=username, password_hash=pw_hash)

        db.session.add(user)
        db.session.commit()

        flash("Account created! Please login.")
        return redirect(url_for("auth.login"))

    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(username=username).first()

        if not user:
            flash("Invalid username or password.")
            return redirect(url_for("auth.login"))

        # IMPORTANT: password_hash (not password_hashed)
        if not bcrypt.checkpw(password.encode("utf-8"), user.password_hash.encode("utf-8")):
            flash("Invalid username or password.")
            audit("LOGIN_FAILED", None, {"username": username})
            return redirect(url_for("auth.login"))

        login_user(user)
        flash("Login successful!")
        audit("LOGIN_SUCCESS", user)
        return redirect(url_for("dashboard"))

    return render_template("login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out")
    audit("LOGOUT", current_user)
    return redirect(url_for("auth.login"))
