from datetime import datetime

def audit(event, user=None, extra=None):
    ts = datetime.utcnow().isoformat()
    username = getattr(user, "username", "anonymous")
    line = f"{ts} | {event} | user={username} | extra={extra}\n"

    with open("instance/security.log", "a", encoding="utf-8") as f:
        f.write(line)
