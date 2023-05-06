from flask import Blueprint

bp = Blueprint(name="errors", import_name=__name__)

from app.errors import handlers
