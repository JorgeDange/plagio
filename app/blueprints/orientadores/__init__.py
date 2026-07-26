# Blueprint de orientadores — CRUD
from flask import Blueprint

orientadores_bp = Blueprint('orientadores', __name__, url_prefix='/orientadores')

from app.blueprints.orientadores import routes
