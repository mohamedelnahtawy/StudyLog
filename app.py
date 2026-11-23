# AI disclosure: this project was generated with help from Claude (Anthropic),
# then reviewed and adapted by the student, as permitted for the CS50x final project.
import os
from datetime import date, timedelta

from flask import Flask, flash, g, redirect, render_template, request, session
import psycopg
from psycopg.rows import dict_row
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import fmt_minutes, login_required

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-change-me")
app.jinja_env.filters["hm"] = fmt_minutes

DATABASE_URL = os.environ.get("DATABASE_URL")


def get_db():
    if "db" not in g:
        if not DATABASE_URL:
            raise RuntimeError("DATABASE_URL environment variable is not set")
        g.db = psycopg.connect(DATABASE_URL, row_factory=dict_row)
    return g.db


@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def streak_for(user_id):
    """Count consecutive days with a session, ending today (or yesterday)."""
    rows = get_db().execute(
        "SELECT DISTINCT day FROM sessions WHERE user_id = %s", (user_id,)
    ).fetchall()
    days = {r["day"] for r in rows}
    cursor = date.today()
    if cursor.isoformat() not in days:
        cursor -= timedelta(days=1)
    count = 0
    while cursor.isoformat() in days:
        count += 1
        cursor -= timedelta(days=1)
    return count


@app.route("/")
@login_required
def index():
    db, uid = get_db(), session["user_id"]
    today = date.today()
    monday = (today - timedelta(days=today.weekday())).isoformat()

    by_subject = db.execute(
        "SELECT subjects.name, COALESCE(SUM(sessions.minutes), 0) AS total FROM sessions "
        "JOIN subjects ON subjects.id = sessions.subject_id "
        "WHERE sessions.user_id = %s AND sessions.day >= %s "
        "GROUP BY subjects.id, subjects.name ORDER BY total DESC",
        (uid, monday),
    ).fetchall()
    week_total = sum(r["total"] for r in by_subject)
    goal = db.execute("SELECT weekly_goal FROM users WHERE id = %s", (uid,)).fetchone()["weekly_goal"]
    percent = min(100, round(week_total / goal * 100)) if goal else 0
    recent = db.execute(
        "SELECT sessions.day, sessions.minutes, sessions.note, subjects.name FROM sessions "
        "JOIN subjects ON subjects.id = sessions.subject_id WHERE sessions.user_id = %s "
        "ORDER BY sessions.day DESC, sessions.id DESC LIMIT 5",
        (uid,),
    ).fetchall()
    return render_template(
        "index.html", by_subject=by_subject, week_total=week_total, goal=goal,
        percent=percent, streak=streak_for(uid), recent=recent,
    )


@app.route("/log", methods=["GET", "POST"])
@login_required
def log():
    db, uid = get_db(), session["user_id"]
    subjects = db.execute(
        "SELECT id, name FROM subjects WHERE user_id = %s ORDER BY name", (uid,)
    ).fetchall()
    today = date.today().isoformat()

    if request.method == "POST":
        subject_id = request.form.get("subject_id", "")
        minutes = request.form.get("minutes", "")
        day = request.form.get("day", today)
        note = request.form.get("note", "").strip()[:200]

        owned = db.execute(
            "SELECT id FROM subjects WHERE id = %s AND user_id = %s", (subject_id, uid)
        ).fetchone()
        try:
            minutes = int(minutes)
            parsed = date.fromisoformat(day)
        except ValueError:
            flash("Enter whole minutes and a valid date.", "error")
            return render_template("log.html", subjects=subjects, today=today), 400
        if not owned:
            flash("Pick one of your subjects.", "error")
        elif not 1 <= minutes <= 1440:
            flash("Minutes must be between 1 and 1440.", "error")
        elif parsed > date.today():
            flash("Sessions can't be in the future.", "error")
        else:
            db.execute(
                "INSERT INTO sessions (user_id, subject_id, minutes, day, note) VALUES (%s, %s, %s, %s, %s)",
                (uid, owned["id"], minutes, day, note),
            )
            db.commit()
            flash("Session saved.", "ok")
            return redirect("/")
        return render_template("log.html", subjects=subjects, today=today), 400

    return render_template("log.html", subjects=subjects, today=today)


@app.route("/history")
@login_required
def history():
    rows = get_db().execute(
        "SELECT sessions.id, sessions.day, sessions.minutes, sessions.note, subjects.name FROM sessions "
        "JOIN subjects ON subjects.id = sessions.subject_id WHERE sessions.user_id = %s "
        "ORDER BY sessions.day DESC, sessions.id DESC",
        (session["user_id"],),
    ).fetchall()
    return render_template("history.html", rows=rows)


@app.post("/history/<int:session_id>/delete")
@login_required
def delete_session(session_id):
    db = get_db()
    db.execute("DELETE FROM sessions WHERE id = %s AND user_id = %s", (session_id, session["user_id"]))
    db.commit()
    flash("Session deleted.", "ok")
    return redirect("/history")


@app.route("/subjects", methods=["GET", "POST"])
@login_required
def subjects():
    db, uid = get_db(), session["user_id"]
    if request.method == "POST":
        name = request.form.get("name", "").strip()[:40]
        if not name:
            flash("Give the subject a name.", "error")
        else:
            try:
                db.execute("INSERT INTO subjects (user_id, name) VALUES (%s, %s)", (uid, name))
                db.commit()
                flash(f"Added {name}.", "ok")
            except psycopg.errors.UniqueViolation:
                db.rollback()
                flash("You already have a subject with that name.", "error")
        return redirect("/subjects")
    rows = db.execute(
        "SELECT subjects.id, subjects.name, COALESCE(SUM(sessions.minutes), 0) AS total "
        "FROM subjects LEFT JOIN sessions ON sessions.subject_id = subjects.id "
        "WHERE subjects.user_id = %s GROUP BY subjects.id, subjects.name ORDER BY subjects.name",
        (uid,),
    ).fetchall()
    return render_template("subjects.html", rows=rows)


@app.post("/subjects/<int:subject_id>/delete")
@login_required
def delete_subject(subject_id):
    db, uid = get_db(), session["user_id"]
    db.execute("DELETE FROM sessions WHERE subject_id = %s AND user_id = %s", (subject_id, uid))
    db.execute("DELETE FROM subjects WHERE id = %s AND user_id = %s", (subject_id, uid))
    db.commit()
    flash("Subject and its sessions deleted.", "ok")
    return redirect("/subjects")


@app.post("/goal")
@login_required
def goal():
    try:
        hours = float(request.form.get("hours", ""))
        assert 0.5 <= hours <= 100
    except (ValueError, AssertionError):
        flash("Weekly goal must be between 0.5 and 100 hours.", "error")
        return redirect("/")
    db = get_db()
    db.execute("UPDATE users SET weekly_goal = %s WHERE id = %s", (round(hours * 60), session["user_id"]))
    db.commit()
    flash("Weekly goal updated.", "ok")
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if not username or len(password) < 8:
            flash("Choose a username and a password of at least 8 characters.", "error")
        elif password != request.form.get("confirmation"):
            flash("Passwords don't match.", "error")
        else:
            db = get_db()
            try:
                row = db.execute(
                    "INSERT INTO users (username, hash) VALUES (%s, %s) RETURNING id",
                    (username, generate_password_hash(password)),
                ).fetchone()
                db.commit()
            except psycopg.errors.UniqueViolation:
                db.rollback()
                flash("That username is taken.", "error")
                return render_template("register.html"), 400
            session["user_id"] = row["id"]
            return redirect("/subjects")
        return render_template("register.html"), 400
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()
    if request.method == "POST":
        user = get_db().execute(
            "SELECT * FROM users WHERE username = %s", (request.form.get("username", "").strip(),)
        ).fetchone()
        if user and check_password_hash(user["hash"], request.form.get("password", "")):
            session["user_id"] = user["id"]
            return redirect("/")
        flash("Wrong username or password.", "error")
        return render_template("login.html"), 403
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


if __name__ == "__main__":
    app.run(debug=True)