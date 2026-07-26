# Blueprint de TCC Válidos
from flask import Blueprint

tcc_validos_bp = Blueprint('tcc_validos', __name__, url_prefix='/tcc-validos')

from app.blueprints.tcc_validos import routes
