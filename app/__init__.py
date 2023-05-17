import logging
import os
from logging.handlers import RotatingFileHandler

from elasticsearch import Elasticsearch
from flask import Flask
from flask_ckeditor import CKEditor
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy

from config import Config

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
ckeditor = CKEditor()
moment = Moment()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    ckeditor.init_app(app)
    moment.init_app(app)

    # Add elasticsearch attribute to app instance to store elasticsearch client if URL exists.
    # Otherwise, set to None to disable elasticsearch
    app.elasticsearch = (
        Elasticsearch(
            hosts=[app.config["ELASTICSEARCH_URL"]],
            ca_certs=app.config["ELASTICSEARCH_CERT"],
            basic_auth=(app.config["ELASTICK_USERNAME"], app.config["ELASTICK_PW"]),
        )
        if app.config["ELASTICSEARCH_URL"]
        else None
    )

    # Register Blueprints
    from app.errors import bp as errors_bp

    app.register_blueprint(errors_bp)

    from app.auth import bp as auth_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")

    from app.main import bp as main_bp

    app.register_blueprint(main_bp)

    # Setup log files
    if not app.debug and not app.testing:
        if not os.path.exists("logs"):
            os.mkdir("logs")
        file_handler = RotatingFileHandler("logs/flask-blog.log", maxBytes=102400, backupCount=10)
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]")
        )
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info("Flask-Blog startup")

    return app


from app import models
