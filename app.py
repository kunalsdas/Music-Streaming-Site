from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config
from flask_login import LoginManager
from flask_migrate import Migrate

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
#change path
app.config['UPLOAD_FOLDER'] = '/static/songs'

# Initialize Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = 'login' 

from views import *

if __name__ == '__main__':
    app.run(debug=True)
    