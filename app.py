from flask import Flask, render_template
from config import Config
from flask_login import LoginManager
from flags_local import FLAGS
from models import db
from models.user import User
from models.challenge import Challenge
from models.submission import Submission
from routes.auth_routes import auth_bp
from flask_login import login_required
from flask_login import login_required, current_user
from routes.challenge_routes import challenge_bp
from routes.leaderboard_routes import leaderboard_bp
import bcrypt
from models.challenge import Challenge
from flask import abort
from functools import wraps
from routes.lab_routes import lab_bp
from routes.idor_routes import idor_bp
from routes.csrf_routes import csrf_bp
from routes.bac_routes import bac_bp

login_manager=LoginManager()
login_manager.login_view="auth.login"

def create_app():
    
    app=Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)
    
    db.init_app(app)
    login_manager.init_app(app)
    app.register_blueprint(auth_bp)
    app.register_blueprint(challenge_bp)
    app.register_blueprint(leaderboard_bp)
    app.register_blueprint(lab_bp)
    app.register_blueprint(idor_bp)
    app.register_blueprint(csrf_bp)
    app.register_blueprint(bac_bp)
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    with app.app_context():
        db.create_all()
        
    def admin_required(fn):
        @wraps(fn)
        @login_required
        def wrapper(*args, **kwargs):
            if not current_user.is_admin:
                abort(403)
            return fn(*args, **kwargs)
        return wrapper
    
    
    @app.route("/")
    @login_required
    def dashboard():
        return render_template("dashboard.html")
    @app.route("/debug/me")
    def debug_me():
        return {
            "authenticated": current_user.is_authenticated,
            "user_id": getattr(current_user, "id", None),
            "username": getattr(current_user, "username", None),
            
        }
    @app.route("/admin/seed")
    @admin_required
    def seed():
        if Challenge.query.first():
            return {"ok": True, "message": "Already seeded"}

        flag = "FLAG{sql_injection_basics}"
        flag_hash = bcrypt.hashpw(flag.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        c = Challenge(
            title="SQLi Basics (Simulation)",
            description="Find the flag using the hint and submit it.",
            difficulty="Beginner",
            points=100,
            flag_hash=flag_hash
        )
        db.session.add(c)
        db.session.commit()

        return {"ok": True, "message": "Seeded 1 challenge"}
        
    @app.route("/admin/recalc-points")
    @login_required
    def recalc_points():
    # recompute points from distinct correct submissions
        for u in User.query.all():
            solved_ids = {
            s.challenge_id
            for s in Submission.query.filter_by(user_id=u.id, is_correct=True).all()
        }
        total = 0
        for cid in solved_ids:
            ch = db.session.get(Challenge, cid)
            if ch:
                total += ch.points
        u.points = total

        db.session.commit()
        return {"ok": True, "message": "Recalculated points for all users"}

    
    @app.route("/admin/seed-xss")
    @admin_required
    def seed_xss():
    
        existing = Challenge.query.filter_by(title="XSS Basics (Reflected) - Simulation").first()
        if existing:
            return {"ok": True, "message": "XSS challenge already seeded"}

        flag = "FLAG{xss_reflected_basics}"
        flag_hash = bcrypt.hashpw(flag.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        c = Challenge(
            title="XSS Basics (Reflected) - Simulation",
            description="Goal: trigger a reflected XSS in a safe demo and find the flag.",
            difficulty="Beginner",
            points=100,
            flag_hash=flag_hash
        )
        db.session.add(c)
        db.session.commit()
        return {"ok": True, "message": "Seeded XSS challenge"}
    
    
    @app.route("/admin/seed-idor")
    @admin_required
    def seed_idor():
        title = "IDOR (Insecure Direct Object Reference)"
        existing = Challenge.query.filter_by(title=title).first()
        if existing:
            return {"ok": True, "message": "IDOR already seeded"}

        flag = FLAGS["idor"]
        flag_hash = bcrypt.hashpw(flag.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        c = Challenge(
            title=title,
            description="Access another user's data by changing an ID in the URL (safe simulation).",
            difficulty="Medium",
            points=150,
            flag_hash=flag_hash
        )
        db.session.add(c)
        db.session.commit()
        return {"ok": True, "message": "Seeded IDOR challenge"}

    
    @app.route("/admin/seed-stored-xss")
    @admin_required
    def seed_stored_xss():
        title = "Stored XSS (Comments) - Simulation"
        existing = Challenge.query.filter_by(title=title).first()
        if existing:
            return {"ok": True, "message": "Stored XSS already seeded"}

        flag = FLAGS["stored_xss"]
        flag_hash = bcrypt.hashpw(flag.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        c = Challenge(
        title=title,
        description="Post a comment that runs as JavaScript when the page loads (safe demo). Then submit the flag.",
        difficulty="Medium",
        points=150,
        flag_hash=flag_hash
        )
        db.session.add(c)
        db.session.commit()
        return {"ok": True, "message": "Seeded Stored XSS challenge"}

    @app.route("/admin/seed-csrf")
    @admin_required
    def seed_csrf():
        title = "CSRF (Cross-Site Request Forgery)"
        existing = Challenge.query.filter_by(title=title).first()
        if existing:
            return {"ok": True, "message": "CSRF already seeded"}

        flag = FLAGS["csrf"]
        flag_hash = bcrypt.hashpw(flag.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        c = Challenge(
            title=title,
            description="Trigger an unauthorised state-changing request due to missing CSRF protection.",
            difficulty="Hard",
            points=200,
            flag_hash=flag_hash
        )
        db.session.add(c)
        db.session.commit()
        return {"ok": True, "message": "Seeded CSRF challenge"}

    @app.route("/admin/seed-bac")
    @admin_required
    def seed_bac():
        title = "Broken Access Control (Admin Page)"
        existing = Challenge.query.filter_by(title=title).first()
        if existing:
            return {"ok": True, "message": "BAC already seeded"}

        flag = FLAGS["bac"]
        flag_hash = bcrypt.hashpw(flag.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        c = Challenge(
            title=title,
            description="Access an admin-only page as a normal user (vulnerable), then see how it’s blocked (secure).",
            difficulty="Hard",
            points=200,
            flag_hash=flag_hash
        )
        db.session.add(c)
        db.session.commit()
        return {"ok": True, "message": "Seeded BAC challenge"}

    
    return app
    

if __name__== "__main__":
        app = create_app()
        app.run(debug=True)
    