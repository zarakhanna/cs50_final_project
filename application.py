import os
import datetime

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
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
db = SQL("sqlite:///celby.db")

# # Make sure API key is set
# if not os.environ.get("API_KEY"):
#     raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    user_id = session.get("user_id")
    return render_template("home.html")

@app.route("/event/<id_event>", methods=["GET",])
@login_required
def learn(id_event):
    """Learn about event"""
    try:
        event = db.execute(
            "SELECT id_event, id_city, name, date, long_description FROM events WHERE id_event=:id_event",
            id_event=id_event
        )[0]
        event['date'] = datetime.datetime.strptime(event['date'],'%Y-%m-%d')
        city = db.execute(
            "SELECT name, country_name FROM cities WHERE id_city=:id_city",
            id_city=event['id_city'])[0]
        return render_template("event.html", event=event, city=city)
    except IndexError:
        return apology("Event does not exist!")


@app.route("/random", methods=["GET", "POST"])
@login_required
def random():
    """Fetch a random event"""
    rows=db.execute("SELECT id_event FROM events ORDER BY RANDOM() LIMIT 1")
    today_date = datetime.datetime.now().strftime("%Y-%m-%d")
    todays=db.execute("SELECT id_event FROM events WHERE date=:date ORDER BY RANDOM() LIMIT 1", date=today_date)
    if not todays:
        return render_template("random.html", id=rows[0]['id_event'])
    return render_template("random.html", id=rows[0]['id_event'], tod_id=todays[0]['id_event'])

@app.route("/wishlist/")
@login_required
def wishlist():
    """Show the user's wishlist of events"""
    wishes = db.execute("SELECT * FROM wishlist, events WHERE wishlist.id_user=:user_id and wishlist.id_event = events.id_event", user_id=session["user_id"])
    return render_template("wishlist.html", wishes=wishes, name=session["user_name"].title())

@app.route("/wishlist/add/<int:id_event>", methods=["GET",])
@login_required
def add_to_wishlist(id_event):
    """Add given id_event to the user's wishlist of events"""
    vals = [session["user_id"], id_event]
    wishes = db.execute("INSERT INTO wishlist (id_user, id_event) VALUES (%s, %s)", vals)
    return redirect(request.referrer or url_for("browse"))

@app.route("/wishlist/remove/<int:id_event>", methods=["GET",])
@login_required
def remove_from_wishlist(id_event):
    """Remove given id_event to the user's wishlist of events"""
    wishes = db.execute("DELETE FROM wishlist WHERE id_user=:id_user AND id_event=:id_event", id_user=session['user_id'], id_event=id_event)
    return redirect(request.referrer or url_for("wishlist"))

def getRows(user_id):
    return db.execute(
        "SELECT events.id_event, name, date, short_description, id_user FROM events LEFT JOIN wishlist ON events.id_event=wishlist.id_event WHERE id_user=:id_user OR id_user IS NULL ORDER BY date",
        id_user=user_id)

@app.route("/browse", methods=["GET", "POST"])
@login_required
def browse():
    """Browse events"""
    if request.method == "POST":
        city = request.form.get("city")
        date = request.form.get("date")
        if not date and not city:
            rows = getRows(session["user_id"])
        elif not date:
            city = db.execute("SELECT id_city FROM cities WHERE name=:name", name=city.title())
            if not city:
                return apology("No such city")
            else:
                city = city[0]["id_city"]
            rows = db.execute("SELECT events.id_event, name, date, short_description, id_user FROM events LEFT JOIN wishlist ON events.id_event=wishlist.id_event WHERE events.id_city=:id_city AND (id_user=:id_user OR id_user IS NULL) ORDER BY date",
            id_user=session["user_id"], id_city=city)
        elif not city:
            rows = db.execute("SELECT events.id_event, name, date, short_description, id_user FROM events LEFT JOIN wishlist ON events.id_event=wishlist.id_event WHERE events.date=:date AND (id_user=:id_user OR id_user IS NULL) ORDER BY date",
            date = date, id_user=session["user_id"])
        else:
            city = db.execute("SELECT id_city FROM cities WHERE name=:name", name=city.title())
            if not city:
                return apology("No such city")
            else:
                city = city[0]["id_city"]
            rows = db.execute("SELECT events.id_event, name, date, short_description, id_user FROM events LEFT JOIN wishlist ON events.id_event=wishlist.id_event WHERE events.id_city=:id_city AND events.date=:date AND (id_user=:id_user OR id_user IS NULL) ORDER BY date",
            id_user=session["user_id"], id_city=city, date = date)
    else:
        rows = getRows(session["user_id"])
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
