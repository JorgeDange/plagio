# Blueprint de Normas ABNT
from flask import Blueprint

normas_bp = Blueprint('normas', __name__, url_prefix='/normas')

from app.blueprints.normas import routes
