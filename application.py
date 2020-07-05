import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from flask import redirect, render_template, request, session
from helpers import *

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
# app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# # Make sure API key is set
# if not os.environ.get("API_KEY"):
#     raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    user_id = session.get("user_id")
    return render_template("home.html")


@app.route("/random", methods=["GET", "POST"])
@login_required
def random():
    """Fetch a random event"""
    return apology("TODO")


@app.route("/wishlist")
@login_required
def wishlist():
    """Show the user's wishlist of events"""
    return apology("TODO")


@app.route("/browse", methods=["GET", "POST"])
@login_required
def browse():
    """Browse events"""
    rows = db.execute("SELECT id_event, name, date, short_description FROM events")
    return render_template("browse.html", rows=rows)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        rows = db.execute("SELECT * FROM users WHERE (username = :username);",
                          username=request.form.get("username"),
                         )
        if len(rows) == 0 or (rows and check_password_hash(rows[0]["hash"], request.form.get("password")) == False):
            return apology("Invalid username/password")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        session["user_name"] = rows[0]["username"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")



@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    #TODO = DEFINE HASH
# Forget any user_id
    session.clear()
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)
        # Ensure password was confirmed
        elif not request.form.get("confirmation"):
            return apology("must provide confirmation", 403)# Ensure password was confirmed
        elif not request.form.get("confirmation") == request.form.get("password"):
            return apology("must confirm password properly", 403)
       # elif not len(request.form.get("password")) > 5:
           # return apology("you must have a longer password", 403)
                # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # if username exists
        if len(rows) > 0:
            return apology("Username already taken", 403)
        vals = [request.form.get("username"), generate_password_hash(request.form.get("password"))]
        user_id = db.execute("INSERT INTO users (username, hash) VALUES (%s, %s)", vals)
        # return render_template("login.html")
        session["user_id"] = user_id
        session["user_name"] = vals[0]
        return redirect("/") # Redirect user to home page
    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
