from functools import wraps # wraps to preserve original function metadata
from flask import abort # abort to return HTTP error responses
from flask_login import current_user # current_user to access the logged-in-user
from audit import audit # audit function to log security activities

# a decorator to restrict access to admin-only routes
def admin_required(f):
    # wraps the target function to enforce authentication and admin role checks before execution
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not getattr(current_user, "is_admin", False):
            audit("ACCESS_DENIED", current_user)
            abort(403) # if the user is not authorized or not admin, logs the access denial and back to a 403 error
        
        return f(*args, **kwargs) # if checks pass, executes the original function
    return decorated_function # return to the decorated function
