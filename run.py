from app import app, db
from app.views import views
#from app import app

db.create_all()

app.register_blueprint(views) # TODO forgot what this does

app.run(debug=True)
