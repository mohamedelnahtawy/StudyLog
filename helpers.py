# AI disclosure: this project was generated with help from Claude (Anthropic),
# then reviewed and adapted by the student, as permitted for the CS50x final project.
from functools import wraps
from flask import redirect, session


def login_required(f):
    """Redirect anonymous visitors to the login page."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return wrapper


def fmt_minutes(total):
    """Turn 150 into '2h 30m'."""
    total = int(total or 0)
    hours, mins = divmod(total, 60)
    if hours and mins:
        return f"{hours}h {mins}m"
    return f"{hours}h" if hours else f"{mins}m"
