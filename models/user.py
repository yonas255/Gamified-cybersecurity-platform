from models import db # importing the database instance 
from flask_login import UserMixin # importing userMixin to support authentication features like login sessions.


# defines the user model with fields for
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)# identification
    username = db.Column(db.String(80), unique=True, nullable=False) # username
    email = db.Column(db.String(254), unique=True, nullable=True) # email
    password_hash = db.Column(db.String(250), nullable=False) # passwords
    points = db.Column(db.Integer, default=0) # scoring system
    is_admin = db.Column(db.Boolean, default=False) # account security for admin
    failed_login_count = db.Column(db.Integer, default=0) # account security for failed login tracking
    locked_until = db.Column(db.Integer, nullable=True)  # unix timestamp (lockout)
    
    # 2FA settings
    totp_secret = db.Column(db.String(32), nullable=True)
    totp_enabled = db.Column(db.Boolean, default=False) 
    twofa_verified = db.Column(db.Boolean, default=False)

