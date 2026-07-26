# Blueprint de gestão de utilizadores — apenas administrador
from flask import Blueprint

utilizadores_bp = Blueprint('utilizadores', __name__, url_prefix='/utilizadores',
                             template_folder='../../templates/utilizadores')

from app.blueprints.utilizadores import routes  # noqa: E402, F401
