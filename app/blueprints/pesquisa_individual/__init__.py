from flask import Blueprint

pesquisa_individual_bp = Blueprint('pesquisa_individual', __name__, url_prefix='/pesquisa-individual')

from . import routes
