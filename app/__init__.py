import logging
import os
from logging.handlers import RotatingFileHandler

from flask import Flask
from flask_ckeditor import CKEditor
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy

from config import Config

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = "login"
ckeditor = CKEditor(app)
moment = Moment(app)

# Register Blueprints
from app.errors import bp as errors_bp

app.register_blueprint(errors_bp)

from app.auth import bp as auth_bp

app.register_blueprint(auth_bp, url_prefix="/auth")

from app import models, routes

# Setup log files
if not app.debug:
    if not os.path.exists("logs"):
        os.mkdir("logs")
    file_handler = RotatingFileHandler("logs/flask-blog.log", maxBytes=102400, backupCount=10)
    file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)

    app.logger.setLevel(logging.INFO)
    app.logger.info("Flask-Blog startup")
