import os
basedir=os.path.abspath(os.path.dirname(__file__))
class Config:
    SECRET_KEY =os.environ.get("SECRET_KEY", "dev-secret-chang-me")
    SQLALCHEMY_DATABASE_URI= "sqlite:///" + os.path.join(basedir, "instance", "app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS=False
    
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = False  # set True only when deployed on HTTPS
