import os
import sqlite3
from flask import Blueprint, render_template, request, current_app
from flask_login import login_required
from flags_local import FLAGS

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
    username = ""
    result = None
    flag = None
    query_used = None

    if request.method == "POST":
        username = request.form.get("username", "")
        con = sqlite3.connect(_db_path())
        cur = con.cursor()

        if mode == "vuln":
            # intentionally unsafe (demo)
            query_used = f"SELECT username, role FROM lab_users WHERE username = '{username}'"
            cur.execute(query_used)
        else:
            # safe fix
            query_used = "SELECT username, role FROM lab_users WHERE username = ?"
            cur.execute(query_used, (username,))

        row = cur.fetchone()
        con.close()

        if row:
            result = {"username": row[0], "role": row[1]}
            if row[1] == "admin":
                flag = FLAGS["sqli"]
        else:
            result = None

    return render_template("lab_sqli.html", mode=mode, username=username, result=result, flag=flag, query_used=query_used)

@lab_bp.route("/lab/xss", methods=["GET", "POST"])
@login_required
def lab_xss():
    mode = request.args.get("mode", "vuln")  # vuln or secure
    text = ""
    rendered = None
    flag = None

    if request.method == "POST":
        text = request.form.get("text", "")
        rendered = text  # reflected back (demo)
        # simple “proof” flag when a typical script tag is present (demo only)
        if "<script" in text.lower():
            flag = FLAGS["xss"]

    return render_template("lab_xss.html", mode=mode, text=text, rendered=rendered, flag=flag)
