from flask import * # TODO actually look at imports
from models import User, Game
from app import db
import logging

views = Blueprint("views",__name__)
try:
    logging.basicConfig(filename = "/home/chiud/logic/debug/error.log")
except IOError:
    pass

# use after ALTER'ing the database to fix entries
# or after changing what a database column stores
@views.route("/update")
def update():
    '''
    for game in Game.query.all():
        game = refresh(game)
        # game.chat = [[x[0], "12/1/2016 12:00:00 PM UTC"] for x in game.chat]
        # game.log = [[x[0], "12/1/2016 12:00:00 PM UTC"] for x in game.log]
        # game.notes = {} 
        if '/' not in game.name:
            insert(game)
    '''
    # WHEN UPDATING MAKE SURE TO REINSERT THE GAME/OBJECT SO IT DOESN'T DISAPPEAR PERMANENTLY
    return redirect(url_for("views.homepage"))

@views.route("/")
def homepage():
    # logging.error("this is an error")
    user = None
    if "user" in session:
        user = session["user"]
    return render_template("homepage.html", user = user)

@views.route("/rules")
def rules():
    user = None
    if "user" in session:
        user = session["user"]
    return render_template("rules.html", user=user)

@views.route("/login", methods = ["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        user = User.query.filter_by(username = request.form["username"]).first()
        if user is None:
            error = "No such user \"%s\" exists" % request.form["username"]
        else:
            # TODO check username for length
            session["user"] = user.username # TODO is there a way to make it whole User class
            return redirect(url_for("views.homepage"))
    return render_template("login.html", error = error)

@views.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("views.homepage"))

@views.route("/register", methods = ["GET", "POST"])
def register():
    error = None
    if request.method == "POST":
        user = User.query.filter_by(username = request.form["username"]).first()
        if user is not None:
            error = "The user \"%s\" already exists" % user.username
        else:
            user = User(request.form["username"])
            db.session.add(user)
            db.session.commit()
            return redirect(url_for("views.homepage"))
    return render_template("register.html", error = error)

# removes a game from the database and returns it so it can be modified
# needed because otherwise changes two classes down cannot be tracked
def refresh(game):
    db.session.delete(game)
    db.session.commit()
    return Game(game.name, game.players, game.hands, game.log, game.current, game.state, game.chat, game.notes) # TODO really hacky way to get around the pickletype issue

# inserts a game into the database and adds the game to each user's gamelist
def insert(game):
    db.session.add(game)
    for player in game.players:
        user = User.query.filter_by(username = player).first()
        if user is None:
            pass # TODO will only happen with old games that don't have 4 registered users as players 
        else:
            game.users.append(user)
    db.session.commit()

@views.route("/newgame", methods = ["GET", "POST"])
def newgame():
    error = None
    if request.method == "POST":
        game = Game.query.filter_by(name = request.form["name"]).first()
        if game is not None:
            error = "The game \"%s\" already exists" % game.name
        else:
            players = [request.form["p1"],request.form["p2"],request.form["p3"],request.form["p4"]]
            if len(set(players))!=4:
                error = "The game needs four distinct players"
            for player in players:
                user = User.query.filter_by(username = player).first()
                if user is None:
                    error = "The user \"%s\" doesn't exist" % player
            if not error:
                game = Game(request.form["name"],players)
                insert(game)
                return redirect(url_for("views.game", name = request.form["name"]))
    return render_template("newgame.html", error = error)

@views.route("/games")
def games():
    user = None
    if "user" in session:
        user = session["user"]

    if user is None:
        return redirect(url_for("views.homepage")) # TODO give some error message

    # determines which games are active, current, and completed
    games = User.query.filter_by(username = user).first().games
    completed = [x for x in games if x.state==4]
    games = [x for x in games if not x.state==4]
    myturn = [x for x in games if (x.index(user)==x.current and x.state>=0) or (x.state<0 and ((-x.state)&(1<<x.index(user)))>0)]
    games = [x for x in games if not ((x.index(user)==x.current and x.state>=0) or (x.state<0 and ((-x.state)&(1<<x.index(user)))>0))]
    return render_template("games.html", user = user, myturn = myturn, games = games, completed = completed)

def gameBase(name, game, user, ind):
    return render_template("game-base.html", name = name, user = user, game = game)

def gameOrder(name, game, user, ind):
    if request.method == "POST":
        swapped = request.form["swapped"]
        game = refresh(game)
        for val in swapped:
            for i in range(6):
                if game.hands[ind].cards[i].val == val:
                    game.hands[ind].cards[i], game.hands[ind].cards[i+1] = game.hands[ind].cards[i+1], game.hands[ind].cards[i]
                    break
        game.state+=(1<<ind)
        game.log.append([user+" has finished ordering cards", request.form["time"]]);
        insert(game)
        return redirect(url_for("views.game", name = name))
    done = (ind==-1 or ((-game.state)&(1<<ind))==0)
    return render_template("game-order.html", name = name, user = user, game = game, done = done)

def gamePass(name, game, user, ind):
    if request.method == "POST":
        which = int(request.form["index"])
        game = refresh(game)
        game.state = 1
        game.current = (game.current+2)%4
        game.hands[ind].cards[which-1].secret = True
        game.log.append([user+" passed card "+str(which), request.form["time"]]);
        insert(game)
        return redirect(url_for("views.game", name = name))
    return render_template("game-pass.html", name = name, user = user, game = game)

def gameGuess(name, game, user, ind):
    if request.method == "POST":
        player = int(request.form["player"])
        which = int(request.form["index"])
        value = request.form["value"]
        game = refresh(game)
        success = False
        if game.hands[(ind+player)%4].cards[which-1].val == value:
            success = True
        if success:
            game.state = 0
            game.current = (game.current+3)%4
            game.hands[(ind+player)%4].cards[which-1].flipped = True
            game.log.append([user+" correctly guessed "+game.players[(ind+player)%4]+"'s card "+str(which), request.form["time"]]);
        else:
            game.state = 2
            game.log.append([user+" incorrectly guessed "+game.players[(ind+player)%4]+"'s card "+str(which)+" as "+value, request.form["time"]]);
        insert(game)
        return redirect(url_for("views.game", name = name))
    return render_template("game-guess.html", name = name, user = user, game = game)

def gameReveal(name, game, user, ind):
    if request.method == "POST":
        which = int(request.form["index"])
        game = refresh(game)
        game.state = 0
        game.current = (game.current+3)%4
        game.hands[ind].cards[which-1].flipped = True
        game.log.append([user+" revealed card "+str(which), request.form["time"]]);
        insert(game)
        return redirect(url_for("views.game", name = name))
    return render_template("game-reveal.html", name = name, user = user, game = game)

def maybeAddContinuationGame(name, players):
    number = ""
    while len(name) > 0 and '0' <= name[-1] <= '9':
        number = name[-1] + number
        name = name[:-1]
    if number == "":
        return
    while len(number) > 1 and number[0] == '0':
        name = '0' + name
        number = number[1:]
    number = str(int(number)+1)
    name += number
    game = Game.query.filter_by(name = name).first()
    if game is None:
        insert(Game(name,players))

def gameCall(name, game, user, ind):
    if request.method == "POST":
        player = int(request.form["player"])
        which = int(request.form["index"])
        value = request.form["value"]
        game = refresh(game)
        success = False
        if game.hands[(ind+player)%4].cards[which-1].val == value:
            success = True
        if success:
            game.hands[(ind+player)%4].cards[which-1].flipped = True
            game.log.append([user+" correctly guessed "+game.players[(ind+player)%4]+"'s card "+str(which), request.form["time"]]);
            done = True
            for i in range(4):
                for j in range(6):
                    if not game.hands[i].cards[j].flipped:
                        done = False
            if done:
                game.state = 4
                maybeAddContinuationGame(game.name, game.players)
                game.players+=[game.players[ind],game.players[(ind+2)%4]]
                game.log.append([user+" has successfully named every card!", request.form["time"]]);
                game.log.append([user+" and "+game.players[(ind+2)%4]+" win!", request.form["time"]]);
        else:
            game.state = 4
            maybeAddContinuationGame(game.name, game.players)
            game.players+=[game.players[(ind+1)%4],game.players[(ind+3)%4]]
            game.log.append([user+" incorrectly guessed "+game.players[(ind+player)%4]+"'s card "+str(which)+" as "+value, request.form["time"]]);
            game.log.append([user+" made a mistake while declaring!", request.form["time"]]);
            game.log.append([game.players[(ind+1)%4]+" and "+game.players[(ind+3)%4]+" win!", request.form["time"]]);
        insert(game)
        return redirect(url_for("views.game", name = name))
    return render_template("game-call.html", name = name, user = user, game = game)

def gameOver(name, game, user, ind):
    return render_template("game-over.html", name = name, user = user, game = game)

# view to handle a chat message, not actually visible
def gamechat(name, game, user):
    if user is None:
        return redirect(url_for("views.homepage")) # TODO give some error message

    game = refresh(game)
    game.chat.append([user+": "+request.args.get("message"), request.args.get("time")])
    insert(game)
    return redirect(url_for("views.homepage")) # TODO is there a way to do this without any return value

#view to handle saving notes, not actually visible
def gamenote(name, game, user):
    if user is None:
        return redirect(url_for("views.homepage")) # TODO give some error message

    game = refresh(game)
    game.notes[user] = request.args.get("note")
    insert(game)
    return redirect(url_for("views.homepage"))

# handles viewing a game (in all states), and chatting
@views.route("/game/<name>", methods = ["GET", "POST"])
def game(name):
    game = Game.query.filter_by(name = name).first()
    if game is None:
        return redirect(url_for("views.homepage")) # TODO give some error message
    user = None
    if "user" in session:
        user = session["user"]
    ind = game.index(user)

    if request.method == "POST" and request.args.get("type")=="chat":
        return gamechat(name, game, user)

    if request.method== "POST" and request.args.get("type")=="savenote":
        return gamenote(name, game, user)

    # if someone has performed an action since the user loaded the page
    if request.method == "POST":
        if int(request.form["loglen"]) != len(game.log):
            return redirect(url_for("views.game", name = name))

    if game.state==4:
        return gameOver(name, game, user, ind)
    if game.state<0:
        return gameOrder(name, game, user, ind)

    if request.method == "POST" and request.form["type"]=="declare":
        game = refresh(game)
        game.state = 3
        game.current = ind
        for i in range(6):
            game.hands[ind].cards[i].flipped = True
        game.log.append([user+" declared!", request.form["time"]]);
        insert(game)
        return redirect(url_for("views.game",name = name))

    if ind == game.current:
        if game.state == 0:
            return gamePass(name, game, user, ind)
        if game.state == 1:
            return gameGuess(name, game, user, ind)
        if game.state == 2:
            return gameReveal(name, game, user, ind)
        if game.state == 3:
            return gameCall(name, game, user, ind)

    # if it isn't the user's turn
    if request.method == "POST":
        return redirect(url_for("views.homepage")) # TODO give some error message

    return gameBase(name, game, user, ind)

# currently unaccessible view to look at a game as if logged out
@views.route("/spec/<name>", methods = ["GET", "POST"])
def spec(name):
    game = Game.query.filter_by(name = name).first()
    if game is None:
        return redirect(url_for("views.homepage")) # TODO give some error message
    if game.state==4:
        return gameOver(name, game, None, -1)
    if game.state<0:
        return gameOrder(name, game, None, -1)
    return gameBase(name, game, None, -1)
