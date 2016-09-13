from flask import * # TODO actually look at imports
from game import *

views = Blueprint("views",__name__)

@views.route("/")
def homepage():
    return render_template("homepage.html")

@views.route("/login", methods = ["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        if request.form["username"] != "user": # temp username and password for now
            error = "Invalid username"
        elif request.form["password"] != "pass":
            error = "Invalid password"
        else:
            session["logged_in"] = True
            return redirect("/")
    return render_template("login.html",error = error)

@views.route("/logout")
def logout():
    session.pop("logged_in", None)
    return redirect("/")

@views.route("/register", methods = ["GET", "POST"])
def register():
    if request.method == "POST":
        user = User(request.username)
        db.add(user)
        db.session.commit()
        return redirect("/")
    return render_template("register.html")

@views.route("/game/<int:id>")
def game(id):
    master = Game()
    return render_template("game.html", id = id, grid = master.grid())
