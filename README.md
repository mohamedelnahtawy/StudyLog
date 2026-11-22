# StudyLog
#### Video Demo: https://youtu.be/R04hztsDFZs
#### Description:

StudyLog is a Flask web app for tracking study time, built with Python, SQL, and JavaScript. After registering, you add the subjects you study, log sessions by entering a subject, a number of minutes, a date, and an optional note, and then watch a dashboard that shows how much you've studied this week against a weekly goal you set, a breakdown of that time by subject, your most recent sessions, and your current daily study streak.

I chose this project because I wanted something that would let me actually use the three main skills from this course at once: Python for the application logic, SQL for storing and querying real data, and JavaScript for something interactive on the front end. A study tracker was a good fit for that, since it needs user accounts and relational data (users, subjects, and sessions all reference each other), real queries (summing minutes by week and by subject, computing a streak), and a front-end feature that benefits from JavaScript rather than a page reload, which is why I added a stopwatch timer to the logging page instead of only letting people type in a number of minutes. It's also something I can genuinely picture using myself while working through the rest of CS50, which made it easier to decide what features actually mattered and which didn't.

## Files

- `app.py`: the Flask application. It defines all of the routes: `/` (the dashboard), `/log` (log a new session, with a GET form and a POST handler), `/history` (list and delete past sessions), `/subjects` (add and delete subjects), `/goal` (update the weekly goal), `/register`, `/login`, and `/logout`, along with POST-only routes for deleting a session or a subject. It also opens the SQLite database connection per request, creates the tables from `schema.sql` on startup if they don't already exist, and computes the weekly totals and the study streak used on the dashboard.
- `helpers.py`: two small helpers used by `app.py`. `login_required` is a decorator that redirects anyone who isn't logged in to the login page, so I don't have to repeat that check in every route. `fmt_minutes` turns a raw number of minutes, like 150, into a readable string like "2h 30m", and is registered as the Jinja filter `hm` so templates can call it directly.
- `schema.sql`: defines the three tables the app uses. `users` holds the username, password hash, and weekly goal. `subjects` holds each user's list of subjects, with a uniqueness constraint so the same user can't add the same subject name twice. `sessions` holds each logged study session, linked to both a user and a subject. There's also an index on `(user_id, day)` in `sessions`, since nearly every query filters by user and by date range.
- `templates/`: the HTML templates. `layout.html` holds the shared header, navigation, and flashed-message area that every page extends. The rest are one template per page: `index.html` (dashboard), `log.html` (the logging form and timer), `history.html`, `subjects.html`, `login.html`, and `register.html`.
- `static/timer.js`: the JavaScript in the project. It implements a simple stopwatch on the log page with start, pause, and resume buttons. Clicking "Finish and fill minutes" stops the timer, rounds the elapsed time up to the nearest whole minute, and fills that value into the form's minutes field automatically. I built it using timestamps (`Date.now()`) rather than counting ticks in a loop, so the elapsed time stays accurate even if the browser throttles a background tab, which is a real problem with naive setInterval-based timers.
- `static/styles.css`: all of the page styling, including a light and a dark theme controlled automatically by `prefers-color-scheme`. I adjusted the color palette, fonts, and some of the wording on the pages to make the app feel like mine rather than a generic template.
- `requirements.txt`: lists Flask as the project's only dependency.

## Design choices

- **Plain `sqlite3` instead of `cs50.SQL`.** I wanted the app to run on any machine with just Flask installed, not only inside the CS50 Codespace, so I used Python's built-in `sqlite3` module directly instead of the course's SQL wrapper.
- **Signed cookie sessions instead of Flask-Session.** Flask's built-in session is enough for storing a user ID in a signed cookie, so I didn't add Flask-Session as an extra dependency just to store server-side session files.
- **Minutes stored as integers.** Every session is stored as a plain integer number of minutes rather than, say, a formatted string or a start/end time pair. That keeps totals exact when I sum them in SQL, and I only format them for display (using `fmt_minutes`) at the point where they're shown to the user.
- **Every query is scoped by `user_id`.** Every SELECT, UPDATE, and DELETE that touches `subjects` or `sessions` filters by the logged-in user's ID, and the delete routes double-check that the row actually belongs to that user before deleting it. This means one account can never see or modify another account's data, even if someone guessed another user's subject or session ID.
- **Deleting a subject deletes its sessions.** Rather than leaving orphaned session rows pointing at a subject that no longer exists, deleting a subject also deletes every session logged under it. The subjects page states this clearly before the delete happens, so it isn't a surprise.
- **The streak counts consecutive days with at least one session, ending today or yesterday.** This means logging a session today keeps a streak alive even if you haven't logged one yet today when you check the dashboard this morning, but the streak does reset once a full day has been skipped entirely.
- **Passwords are hashed, never stored in plain text.** Registration and login use Werkzeug's `generate_password_hash` and `check_password_hash`, and passwords must be at least 8 characters. Even with direct access to the database, there's no way to recover a user's actual password from what's stored.

If I kept working on this project, the next thing I'd add is reminders or notifications, for example an email or a browser notification nudging a user who hasn't logged a session in a day or two, so the streak feature actually encourages consistent studying instead of just reporting on it after the fact.

## Running it

    pip install -r requirements.txt
    flask run

## AI disclosure

This project was built with help from Claude (Anthropic), as permitted for the CS50x final project, and then reviewed and adapted by me. I changed the color palette, fonts, and wording across the templates and stylesheet to match my own taste rather than leaving the generated defaults, and I read through the Python and SQL to make sure I understand and can explain every route and query before submitting.
