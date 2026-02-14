import bcrypt
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user, login_user, logout_user, login_required
from audit import audit
from models import db
from models.user import User
import time
import re
import pyotp
from flask import session

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        email = request.form.get("email", "").strip().lower()

        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
            flash("Enter a valid email address.")
            return redirect(url_for("auth.register"))

        if len(email) > 254:
            flash("Email is too long.")
            return redirect(url_for("auth.register"))

        
        # ✅ Password policy
        if len(password) < 10:
            flash("Password must be at least 10 characters.")
            return redirect(url_for("auth.register"))

        if len(password) > 72:
            flash("Password is too long (max 72 characters).")
            return redirect(url_for("auth.register"))

        if not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
            flash("Password must contain at least one letter and one number.")
            return redirect(url_for("auth.register"))

        
        if not username or not password or not email:
            flash("Username, email and password are required!")
            return redirect(url_for("auth.register"))

        existing = User.query.filter_by(username=username).first()
        if existing:
            flash("Username already exists")
            return redirect(url_for("auth.register"))
        
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            flash("Email already registered.")
            return redirect(url_for("auth.register"))


        pw_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        user = User(username=username, email=email, password_hash=pw_hash)

        db.session.add(user)
        db.session.commit()

        flash("Account created! Please login.")
        return redirect(url_for("auth.login"))

    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        ip = request.headers.get("X-Forwarded-For", request.remote_addr) or "unknown"

        email = request.form.get("email", "").strip().lower()
        user = User.query.filter_by(email=email).first()

        password = request.form.get("password", "")
        
        now = int(time.time())

        # If user exists and is locked
        if user and user.locked_until and now < user.locked_until:
            seconds_left = user.locked_until - now
            flash(f"Account locked. Try again in {seconds_left}s.")
            return redirect(url_for("auth.login"))

        
        # Wrong user or wrong password
        if (not user) or (not bcrypt.checkpw(password.encode("utf-8"), user.password_hash.encode("utf-8"))):
            # Only track lockout for real users (avoid username enumeration)
            if user:
                user.failed_login_count = (user.failed_login_count or 0) + 1
                audit("LOGIN_FAILED", user, {"email": email, "ip": ip})
                
                attempts_left = max(0, 5 - user.failed_login_count)

                if user.failed_login_count >= 5:
                    user.locked_until = now + 60  # lock 60s
                    user.failed_login_count = 0   # reset after lock triggers
                    db.session.commit()
                    flash("Too many failed attempts. Account locked for 60s.")
                    return redirect(url_for("auth.login"))

                db.session.commit()
                flash(f"Invalid email or password. Attempts left: {attempts_left}")
            else:
                flash("Invalid username or password.")
                audit("LOGIN_FAILED", None, {"email": email, "ip": ip})


            return redirect(url_for("auth.login"))
        
        # Enforce 2FA
        if user.totp_enabled:
            session["2fa_user_id"] = user.id
            return redirect(url_for("auth.twofa_login"))

        login_user(user)
        user.failed_login_count = 0
        user.locked_until = None
        db.session.commit()
        audit("LOGIN_SUCCESS", user, {"ip": ip})
        flash("Login successful!")
        if user.is_admin:
            return redirect(url_for("admin.dashboard"))
        else:
            return redirect(url_for("dashboard"))

    return render_template("login.html")

@auth_bp.route("/login/2fa", methods=["GET", "POST"])
def twofa_login():
    user_id = session.get("2fa_user_id")
    if not user_id:
        return redirect(url_for("auth.login"))

    user = db.session.get(User, user_id)
    if request.method == "POST":
        code = request.form.get("code", "")
        totp = pyotp.TOTP(user.totp_secret)

        if totp.verify(code):
            session.pop("2fa_user_id", None)
            login_user(user)
            audit("LOGIN_2FA_SUCCESS", user)
            flash("Login successful.")
            if user.is_admin:
                return redirect(url_for("admin.dashboard"))
            return redirect(url_for("dashboard"))

        flash("Invalid 2FA code.")
        audit("LOGIN_2FA_FAILED", user)

    return render_template("login_2fa.html")

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out")
    audit("LOGOUT", current_user)
    return redirect(url_for("auth.login"))
