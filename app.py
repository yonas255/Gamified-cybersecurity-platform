from flask import Flask, render_template
from config import Config
from flask_login import LoginManager
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
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    with app.app_context():
        db.create_all()
        
        
    
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
    @login_required
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

    
    return app
    

if __name__== "__main__":
    app = create_app()
    app.run(debug=True)
    