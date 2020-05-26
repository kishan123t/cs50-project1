from functools import wraps
from flask import g, request, redirect, url_for
from flask import render_template, session

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("username") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function
