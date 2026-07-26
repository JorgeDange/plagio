# Blueprint de aprovações — decisão final sobre TCC verificados
from flask import Blueprint

aprovacoes_bp = Blueprint('aprovacoes', __name__, url_prefix='/aprovacoes',
                           template_folder='../../templates/aprovacoes')

from app.blueprints.aprovacoes import routes  # noqa: E402, F401
