import os # OS model to interact with the file system
from flask import Flask, make_response, render_template # Flask
from config import Config # configuration
from flask_login import LoginManager # authentication
from flags_local import FLAGS # FLAG
from models import db # Database model
from models.user import User # user model
from models.challenge import Challenge # challenge model for storing challenges
from models.submission import Submission # submission model for tracking users
from routes.auth_routes import auth_bp # authentication routes
from flask_login import login_required # login_required to protect routes
from flask_login import login_required, current_user # current_user to access to logged-in users details
from routes.challenge_routes import challenge_bp # challenge routes for listing and submitting
from routes.leaderboard_routes import leaderboard_bp # leaderboard route for displaying users ranked by point
import bcrypt # bcrypt for securely hashing passwords
from flask import abort # abort to return error pages such as 403 forbidden
from functools import wraps # wraps to create decorators while preserving function metadata
from routes.lab_routes import lab_bp # SQLi, XSS, nad Stored XSS lab route
from routes.idor_routes import idor_bp # IDOR lab route
from routes.csrf_routes import csrf_bp # CSRF lab route
from routes.bac_routes import bac_bp # BAC lab route
from routes.admin_routes import admin_bp # Admin route for managing challenges
from flask import request # request to access incoming HTTP request data
from routes.account_routes import account_bp # account routes for features like 2FA setup (** this is for future security implementation**)
# creating and configuring flask-login so unauthenticated users are redirected to the login page

login_manager=LoginManager()
login_manager.login_view="auth.login"
# defines Flask application factory
def create_app():
    
    app=Flask(__name__, instance_relative_config=True)
    #loads configuration
    app.config.from_object(Config)
    # initializes database/login
    db.init_app(app)
    # registers all route blueprints
    login_manager.init_app(app)
    app.register_blueprint(auth_bp)
    app.register_blueprint(challenge_bp)
    app.register_blueprint(leaderboard_bp)
    app.register_blueprint(lab_bp)
    app.register_blueprint(idor_bp)
    app.register_blueprint(csrf_bp)
    app.register_blueprint(bac_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(account_bp)
    
    # adding security headers after each response
    @app.after_request
    def add_security_headers(response):
        
        response.headers["X-Content-Type-Options"] = "nosniff" # content protection
        response.headers["X-Frame-Options"] = "DENY" # frame protection
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin" # referrer policy
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()" # permissions policy

        # different CSP rules for normal page vs lab pages: strict for platform, relaxed for labs (so XSS demos still work)
        if request.path.startswith("/lab/"):
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "style-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; "
                "script-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; "
                "img-src 'self' data:; "
            )
        # normal page
        else:
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "style-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; "
                "script-src 'self' https://cdn.jsdelivr.net; "
                "img-src 'self' data:; "
            )
        return response
    
    # providing a debug route to test response headers
    @app.route("/debug/headers")
    def debug_headers():
        resp = make_response({"ok": True})
        return resp
    
    # loads users from the database for Flak-login session management
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # creating database table
    with app.app_context():
        db.create_all()
        # creates or updates a bootstrap admin account using environment variables
        admin_email = os.environ.get("BOOTSTRAP_ADMIN_EMAIL")
        admin_password = os.environ.get("BOOTSTRAP_ADMIN_PASSWORD")
        # checks the admins credential are provided via environment variable and normalizes the email format
        if admin_email and admin_password:
            admin_email = admin_email.strip().lower()

            # attempting to find an existsing user in the database using the provided email
            u = User.query.filter_by(email=admin_email).first()

            # no user found it searches for a default admin username
            if not u:
                u = User.query.filter_by(username="admin").first()
            # if user exists
            if u:
                u.email = admin_email # update their email
                u.is_admin = True # grants admin privileges
                pw_hash = bcrypt.hashpw(admin_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8") # securely hashes the password
                u.password_hash = pw_hash
                #saves changes
                db.session.commit()
                print("✔ Bootstrap admin updated/assigned")
            else:
                pw_hash = bcrypt.hashpw(admin_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
                admin_user = User(
                    username="admin",
                    email=admin_email,
                    password_hash=pw_hash,
                    is_admin=True
                )
                db.session.add(admin_user)
                db.session.commit()
                # confirms
                print("✔ Bootstrap admin created")
        
    # defining an admin only decorator that blocks non-admin users from protected routes
    def admin_required(fn):
        @wraps(fn)
        @login_required
        def wrapper(*args, **kwargs):
            if not current_user.is_admin:
                abort(403)
            return fn(*args, **kwargs)
        return wrapper
    
    # defining the dashboard route
    @app.route("/")
    @login_required
    def dashboard():
        total = Challenge.query.count() # calculates total or completed challenges
        completed = Submission.query.filter_by(
            user_id=current_user.id,
            is_correct=True
        ).distinct(Submission.challenge_id).count()
        # progress percentage
        percent = int((completed / total) * 100) if total > 0 else 0
        # renders the dashboard page
        return render_template(
            "dashboard.html",
            total=total,
            completed=completed,
            percent=percent
        )
        
    # adding a debug route showing the current logged-in-user information
    @app.route("/debug/me")
    def debug_me():
        return {
            "authenticated": current_user.is_authenticated,
            "user_id": getattr(current_user, "id", None),
            "username": getattr(current_user, "username", None),
            
        }
        
    # seeds the database within an initial SQL Injection challenge if no challenges already exist
    @app.route("/admin/seed")
    @admin_required
    def seed():
        if Challenge.query.first():
            return {"ok": True, "message": "Already seeded"}
        # hashing the flag
        flag = "FLAG{sql_injection_basics}"
        flag_hash = bcrypt.hashpw(flag.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        # Challenge description
        c = Challenge(
            title="SQLi Basics (Simulation)",
            description="Find the flag using the hint and submit it.",
            difficulty="Beginner",
            points=100,
            flag_hash=flag_hash,
            lab_type="sqli"
        )
        db.session.add(c)
        db.session.commit()
        # confirms
        return {"ok": True, "message": "Seeded 1 challenge"}
    
    # recalculates user points based on distinct correct submissions 
    @app.route("/admin/recalc-points")
    @login_required
    def recalc_points():
    ## recompute points from distinct correct submissions
        for u in User.query.all():
            solved_ids = {
            s.challenge_id
            for s in Submission.query.filter_by(user_id=u.id, is_correct=True).all()
        }
        total = 0
        # updates all user total
        for cid in solved_ids:
            ch = db.session.get(Challenge, cid)
            if ch:
                total += ch.points
        u.points = total
        db.session.commit()
        # confirming
        return {"ok": True, "message": "Recalculated points for all users"}

    # defining an admin only route that seeds the reflected XSS challenge if it does not already seeded
    @app.route("/admin/seed-xss")
    @admin_required
    def seed_xss():
        # Checking if the challenge already exits
        existing = Challenge.query.filter_by(title="XSS Basics (Reflected) - Simulation").first()
        if existing:
            return {"ok": True, "message": "XSS challenge already seeded"}
        # hashes the XSS flag before saving to the database
        flag = "FLAG{xss_reflected_basics}"
        flag_hash = bcrypt.hashpw(flag.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        # Challenge description
        c = Challenge(
            title="XSS Basics (Reflected) - Simulation",
            description="Goal: trigger a reflected XSS in a safe demo and find the flag.",
            difficulty="Beginner",
            points=100,
            flag_hash=flag_hash,
            lab_type="xss"
        )
        db.session.add(c)
        db.session.commit()
        # confirming
        return {"ok": True, "message": "Seeded XSS challenge"}
    
    # Defining the admin-only route for seeding IDOR challenge
    @app.route("/admin/seed-idor")
    @admin_required
    def seed_idor():
        title = "IDOR (Insecure Direct Object Reference)"
        existing = Challenge.query.filter_by(title=title).first()
        if existing:
            return {"ok": True, "message": "IDOR already seeded"}
        # hashes the flag
        flag = FLAGS["idor"]
        flag_hash = bcrypt.hashpw(flag.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        # Challenge description
        c = Challenge(
            title=title,
            description="Access another user's data by changing an ID in the URL (safe simulation).",
            difficulty="Medium",
            points=150,
            flag_hash=flag_hash,
            lab_type="idor"
        )
        db.session.add(c)
        db.session.commit()
        #confirming
        return {"ok": True, "message": "Seeded IDOR challenge"}
    
    # adding a debug for admin-only route to return the current number of challenges in the database
    @app.route("/debug/challenge-count")
    def debug_challenge_count():
        return {"count": Challenge.query.count()}

    # admin-only route for seeding the Stored XSS challenge
    @app.route("/admin/seed-stored-xss")
    @admin_required
    def seed_stored_xss():
        title = "Stored XSS (Comments) - Simulation"
        # checking if the challenge already existing
        existing = Challenge.query.filter_by(title=title).first()
        if existing:
            return {"ok": True, "message": "Stored XSS already seeded"}
        # hashing the flag
        flag = FLAGS["stored_xss"]
        flag_hash = bcrypt.hashpw(flag.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        # description
        c = Challenge(
        title=title,
        description="Post a comment that runs as JavaScript when the page loads (safe demo). Then submit the flag.",
        difficulty="Medium",
        points=150,
        flag_hash=flag_hash,
        lab_type="stored_xss"
        )
        db.session.add(c)
        db.session.commit()
        #confirming
        return {"ok": True, "message": "Seeded Stored XSS challenge"}
    
    # admin-only route for seeding CSRF Challenge
    @app.route("/admin/seed-csrf")
    @admin_required
    def seed_csrf():
        title = "CSRF (Cross-Site Request Forgery)"
        # checks if it already exist
        existing = Challenge.query.filter_by(title=title).first()
        if existing:
            return {"ok": True, "message": "CSRF already seeded"}
        # Hashing the flag
        flag = FLAGS["csrf"]
        flag_hash = bcrypt.hashpw(flag.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        # Description
        c = Challenge(
            title=title,
            description="Trigger an unauthorised state-changing request due to missing CSRF protection.",
            difficulty="Hard",
            points=200,
            flag_hash=flag_hash,
            lab_type="csrf"
        )
        db.session.add(c)
        db.session.commit()
        # confirms
        return {"ok": True, "message": "Seeded CSRF challenge"}
    
    # route to seed BAC
    @app.route("/admin/seed-bac")
    @admin_required
    def seed_bac():
        title = "Broken Access Control (Admin Page)"
        # Check up
        existing = Challenge.query.filter_by(title=title).first()
        if existing:
            return {"ok": True, "message": "BAC already seeded"}
        # hashing the flag
        flag = FLAGS["bac"]
        flag_hash = bcrypt.hashpw(flag.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        # challenge description
        c = Challenge(
            title=title,
            description="Access an admin-only page as a normal user (vulnerable), then see how it’s blocked (secure).",
            difficulty="Hard",
            points=200,
            flag_hash=flag_hash,
            lab_type="bac"
        )
        db.session.add(c)
        db.session.commit()
        # confirming
        return {"ok": True, "message": "Seeded BAC challenge"}
    
    # defining about page route
    @app.route("/about")
    def aboute():
        # renders the project information page
        return render_template("about.html")
    
    # an admin only route for seeding SQL Injection Admin Bypass challenge
    @app.route("/admin/seed-sqli-admin")
    @admin_required
    def seed_sqli_admin():
        title = "SQLi: Admin Bypass (Simulation)"
        # check if the challenge already exist
        existing = Challenge.query.filter_by(title=title).first()
        if existing:
            return {"ok": True, "message": "SQLi Admin already seeded"}
        # hashing the flag
        flag = FLAGS["sqli_admin"]
        flag_hash = bcrypt.hashpw(flag.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        # description
        c = Challenge(
            title=title,
            description="Use SQL Injection to make the query return the admin user and reveal the flag.",
            difficulty="Medium",
            points=150,
            flag_hash=flag_hash,
            lab_type="sqli_admin"
    )

        db.session.add(c)
        db.session.commit()
        # confirming
        return {"ok": True, "message": "Seeded SQLi Admin challenge"}
    # returns the Flask app instance
    return app
    
# run the application in debug mode when the file is executed directly
if __name__== "__main__":
        app = create_app()
        app.run(debug=True)
    