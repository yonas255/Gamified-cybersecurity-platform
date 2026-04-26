from datetime import datetime # datetime module for timestamp

# an audit logging function that records event/actions type, user, and extra metadata
def audit(event, user=None, extra=None):
    ts = datetime.utcnow().isoformat() # UTC timestamp
    username = getattr(user, "username", "anonymous") # retrieving username or default
    line = f"{ts} | {event} | user={username} | extra={extra}\n" # format the log entry

    # opens the security log file in append mode and write the log
    with open("instance/security.log", "a", encoding="utf-8") as f:
        f.write(line)
