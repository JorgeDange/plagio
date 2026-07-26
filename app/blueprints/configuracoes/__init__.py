from flask import Blueprint

config_bp = Blueprint('configuracoes', __name__, url_prefix='/configuracoes')

from app.blueprints.configuracoes import routes
