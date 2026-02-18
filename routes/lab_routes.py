import os
import sqlite3
from flask import Blueprint, redirect, render_template, request, current_app
from flask_login import login_required
from flags_local import FLAGS
from models.challenge import Challenge

lab_bp = Blueprint("lab", __name__)

def _db_path():
    # reliable path to your sqlite db file
    return os.path.join(current_app.root_path, "instance", "app.db")


def _ensure_lab_data():
    db_file = _db_path()
    os.makedirs(os.path.dirname(db_file), exist_ok=True)

    con = sqlite3.connect(db_file)
    cur = con.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS lab_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            role TEXT NOT NULL
        )
    """)

    cur.execute("SELECT COUNT(*) FROM lab_users")
    count = cur.fetchone()[0]
    if count == 0:
        cur.execute("INSERT INTO lab_users (username, role) VALUES (?, ?)", ("guest", "user"))
        cur.execute("INSERT INTO lab_users (username, role) VALUES (?, ?)", ("admin", "admin"))

    con.commit()
    con.close()

@lab_bp.route("/lab/sqli", methods=["GET", "POST"])
@login_required
def lab_sqli():
    _ensure_lab_data()

    mode = request.args.get("mode", "vuln")  # vuln or secure
    if mode not in ("vuln", "secure"):
        mode = "vuln"
    challenge_id = request.args.get("challenge_id", type=int)

    challenge = Challenge.query.get(challenge_id) if challenge_id else None
    lab_variant = challenge.lab_type if challenge else "sqli"
    points = challenge.points if challenge else 100
    challenge_title = challenge.title if challenge else "SQL Injection Lab"

    
    username = ""
    result = None
    flag = None
    query_used = None
    error = None  # ✅ define for both GET and POST

    if request.method == "POST":
        username = request.form.get("username", "")

        con = sqlite3.connect(_db_path())
        cur = con.cursor()

        try:
            if mode == "vuln":
                query_used = f"SELECT username, role FROM lab_users WHERE username = '{username}'"
                cur.execute(query_used)
            else:
                query_used = "SELECT username, role FROM lab_users WHERE username = ?"
                cur.execute(query_used, (username,))
        except sqlite3.Error as e:
            error = str(e)
            row = None
        else:
            row = cur.fetchone()
        finally:
            con.close()

        if row:
            result = {"username": row[0], "role": row[1]}

            if mode == "vuln":
                # Beginner SQLi: any successful result reveals flag
                if lab_variant == "sqli":
                    flag = FLAGS["sqli"]

                # Medium SQLi: must get admin specifically
                elif lab_variant == "sqli_admin":
                    if result["role"] == "admin":
                        flag = FLAGS["sqli_admin"]


    return render_template(
        "lab_sqli.html",
        mode=mode,
        challenge_id=challenge_id,
        username=username,
        result=result,
        flag=flag,
        query_used=query_used,
        error=error,
        points=points,
        challenge_title=challenge_title,
        lab_variant=lab_variant

    )


@lab_bp.route("/lab/xss", methods=["GET", "POST"])
@login_required
def lab_xss():
    mode = request.args.get("mode", "vuln")
    if mode not in ("vuln", "secure"):
        mode = "vuln"
    challenge_id = request.args.get("challenge_id", type=int)

    text = ""
    rendered = None
    flag = None

    if request.method == "POST":
        text = request.form.get("text", "")
        rendered = text

        # Only award flag in vulnerable mode when an XSS payload is attempted
        if mode == "vuln" and "<script" in text.lower():
            flag = FLAGS["xss"]

    return render_template(
        "lab_xss.html",
        mode=mode,
        challenge_id=challenge_id,
        text=text,
        rendered=rendered,
        flag=flag
    )
    
from flask import redirect, render_template, request
from flask_login import login_required
from flags_local import FLAGS

@lab_bp.route("/lab/stored-xss", methods=["GET", "POST"])
@login_required
def lab_stored_xss():
    mode = request.args.get("mode", "vuln")
    if mode not in ("vuln", "secure"):
        mode = "vuln"

    challenge_id = request.args.get("challenge_id", type=int)

    # In-memory store (per process)
    if not hasattr(lab_stored_xss, "STORE"):
        lab_stored_xss.STORE = []

    # POST = store comment then redirect (prevents double-submit)
    if request.method == "POST":
        comment = request.form.get("comment", "").strip()
        if comment:
            # prevent accidental double post (same comment twice in a row)
            if not lab_stored_xss.STORE or lab_stored_xss.STORE[-1] != comment:
                lab_stored_xss.STORE.append(comment)

        url = f"/lab/stored-xss?mode={mode}"
        if challenge_id:
            url += f"&challenge_id={challenge_id}"
        return redirect(url)

    comments = list(lab_stored_xss.STORE)

    # ✅ IMPORTANT: attacker page never reveals flag
    flag = None

    return render_template(
        "lab_stored_xss.html",
        mode=mode,
        challenge_id=challenge_id,
        comments=comments,
        flag=flag,
    )


@lab_bp.route("/lab/stored-xss/victim", methods=["GET"])
@login_required
def stored_xss_victim():
    mode = request.args.get("mode", "vuln")
    if mode not in ("vuln", "secure"):
        mode = "vuln"

    challenge_id = request.args.get("challenge_id", type=int)

    if not hasattr(lab_stored_xss, "STORE"):
        lab_stored_xss.STORE = []

    comments = list(lab_stored_xss.STORE)

    # ✅ Flag appears ONLY on victim view, ONLY in vuln mode, ONLY if payload exists
    flag = None
    if mode == "vuln" and any("<script" in c.lower() for c in comments):
        flag = FLAGS["stored_xss"]

    return render_template(
        "lab_stored_xss_victim.html",
        mode=mode,
        challenge_id=challenge_id,
        comments=comments,
        flag=flag,
    )


@lab_bp.route("/lab/stored-xss/clear", methods=["POST"])
@login_required
def clear_stored_xss():
    if hasattr(lab_stored_xss, "STORE"):
        lab_stored_xss.STORE = []

    mode = request.args.get("mode", "vuln")
    if mode not in ("vuln", "secure"):
        mode = "vuln"

    challenge_id = request.args.get("challenge_id", type=int)

    url = f"/lab/stored-xss?mode={mode}"
    if challenge_id:
        url += f"&challenge_id={challenge_id}"

    return redirect(url)
