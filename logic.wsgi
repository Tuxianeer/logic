#!/usr/bin/python
# setup for web server
import sys

# directory path
sys.path.insert(0, "/home/chiud/logic")

from app import app as application
from app import db
from app.views import views

db.create_all()

application.register_blueprint(views) 

