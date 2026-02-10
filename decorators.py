from functools import wraps
from flask import abort
from flask_login import current_user
from audit import audit

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not getattr(current_user, "is_admin", False):
            audit("ACCESS_DENIED", current_user)
            abort(403)
        return f(*args, **kwargs)
    return decorated_function
