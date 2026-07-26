# Blueprint de verificações — submissão e resultados
from flask import Blueprint

verificacoes_bp = Blueprint('verificacoes', __name__)

from app.blueprints.verificacoes import routes  # noqa: E402, F401
