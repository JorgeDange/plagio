# Blueprint de TCC Suspeitos
from flask import Blueprint

tcc_suspeitos_bp = Blueprint('tcc_suspeitos', __name__, url_prefix='/tcc-suspeitos')

from app.blueprints.tcc_suspeitos import routes
