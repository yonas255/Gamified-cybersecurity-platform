import os # models for file handling
import sqlite3 # database operations
from flask import Blueprint, redirect, render_template, request, current_app # flask routing
from flask_login import login_required # authentication
from flags_local import FLAGS
from models.challenge import Challenge # challenge model

lab_bp = Blueprint("lab", __name__) # creates a blue print to group all lab related routes

def _db_path(): # helper function to generate a reliable file path for SQLite database
    # reliable path to sqlite db file
    return os.path.join(current_app.root_path, "instance", "app.db")


def _ensure_lab_data(): # making sure the lab database
    
    db_file = _db_path()
    os.makedirs(os.path.dirname(db_file), exist_ok=True)

    con = sqlite3.connect(db_file)
    cur = con.cursor()
    
    # sample data exist by creating a table and inserting default users if empty
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
# SQL injection lab, captures errors,
@lab_bp.route("/lab/sqli", methods=["GET", "POST"])
@login_required
def lab_sqli():
    _ensure_lab_data()
    # supports vulnerable and secure models
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
    error = None  # define for both GET and POST

    if request.method == "POST":
        username = request.form.get("username", "")

        con = sqlite3.connect(_db_path())
        cur = con.cursor()
    # executes queries differently depends on mode,
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
        # reveals flags depending on successful exploitation and lab difficulty
            if mode == "vuln":
                # Beginner SQLi
                if lab_variant == "sqli":
                    flag = FLAGS["sqli"]

                # Medium SQLi
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

# Reflected XSS lab
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
    # takes user input
    if request.method == "POST":
        text = request.form.get("text", "")
        rendered = text

        # revealing a flag in vulnerable mode when a script payload is detected
        if mode == "vuln" and "<script" in text.lower():
            flag = FLAGS["xss"]
    # renders it directly
    return render_template(
        "lab_xss.html",
        mode=mode,
        challenge_id=challenge_id,
        text=text,
        rendered=rendered,
        flag=flag
    )
    

# Stored XSS lab
@lab_bp.route("/lab/stored-xss", methods=["GET", "POST"])
@login_required
def lab_stored_xss():
    mode = request.args.get("mode", "vuln")
    if mode not in ("vuln", "secure"):
        mode = "vuln"

    challenge_id = request.args.get("challenge_id", type=int)

    # stores user comments in memory
    if not hasattr(lab_stored_xss, "STORE"):
        lab_stored_xss.STORE = []

    # store comment then redirect (prevents double-submit)
    if request.method == "POST":
        comment = request.form.get("comment", "").strip()
        if comment:
            # preventing duplicate submissions
            if not lab_stored_xss.STORE or lab_stored_xss.STORE[-1] != comment:
                lab_stored_xss.STORE.append(comment)

        url = f"/lab/stored-xss?mode={mode}"
        if challenge_id:
            url += f"&challenge_id={challenge_id}"
        return redirect(url)

    comments = list(lab_stored_xss.STORE)
    # displays stored comments without revealing the flag on the attacker page
    # attacker page never reveals flag
    flag = None

    return render_template(
        "lab_stored_xss.html",
        mode=mode,
        challenge_id=challenge_id,
        comments=comments,
        flag=flag,
    )

# simulating the victim view for stored XSS
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
    # flag is only revealed in vulnerable mode if a malicious script exists in stored comments
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

# route to clear stored XSS comments
@lab_bp.route("/lab/stored-xss/clear", methods=["POST"])
@login_required
def clear_stored_xss():
    if hasattr(lab_stored_xss, "STORE"):
        lab_stored_xss.STORE = []

    mode = request.args.get("mode", "vuln")
    if mode not in ("vuln", "secure"):
        mode = "vuln"

    challenge_id = request.args.get("challenge_id", type=int)
    # resets the lab state before redirecting back to the page
    url = f"/lab/stored-xss?mode={mode}"
    if challenge_id:
        url += f"&challenge_id={challenge_id}"

    return redirect(url)
