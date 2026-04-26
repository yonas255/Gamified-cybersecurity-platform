import os # OS module and define base directory
basedir=os.path.abspath(os.path.dirname(__file__))
class Config:
    SECRET_KEY =os.environ.get("SECRET_KEY", "dev-secret-chang-me") # sets a secret key for session security
    SQLALCHEMY_DATABASE_URI= "sqlite:///" + os.path.join(basedir, "instance", "app.db") # DataBase URL to use a local SQLite database
    SQLALCHEMY_TRACK_MODIFICATIONS=False # Disable SQLAlchemy modification tracking to improve performance
    
    # configures secure session cookie setting, including HTTP-only access, SameSite protection, HTTPS requirement
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = False  ## set True only when deployed on HTTPS
