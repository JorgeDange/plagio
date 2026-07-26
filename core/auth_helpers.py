# IMETRO TFC v3 — Decoradores de Permissão (RBAC)
# Controlo de acesso baseado em papéis para proteger rotas.

import logging
from functools import wraps
from flask import abort, flash, redirect, url_for, request
from flask_login import login_required, current_user

logger = logging.getLogger(__name__)


def requer_login(f):
    """Exige utilizador autenticado (wrapper de @login_required)."""
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        return f(*args, **kwargs)
    return decorated


def requer_admin(f):
    """Apenas administradores podem aceder."""
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if not current_user.is_admin:
            logger.warning(
                'Acesso negado (requer_admin): %s tentou aceder a %s',
                current_user.email, request.path
            )
            flash('Sem permissão para aceder a esta área.', 'erro')
            abort(403)
        return f(*args, **kwargs)
    return decorated


def requer_carregador(f):
    """Carregador OU administrador podem aceder."""
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if not (current_user.is_carregador or current_user.is_admin):
            logger.warning(
                'Acesso negado (requer_carregador): %s tentou aceder a %s',
                current_user.email, request.path
            )
            flash('Sem permissão para aceder a esta área.', 'erro')
            abort(403)
        return f(*args, **kwargs)
    return decorated


def requer_verificador(f):
    """Verificador OU administrador podem aceder."""
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if not (current_user.is_verificador or current_user.is_admin):
            logger.warning(
                'Acesso negado (requer_verificador): %s tentou aceder a %s',
                current_user.email, request.path
            )
            flash('Sem permissão para aceder a esta área.', 'erro')
            abort(403)
        return f(*args, **kwargs)
    return decorated


def requer_aprovador(f):
    """Aprovador OU administrador podem aceder."""
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if not (current_user.is_aprovador or current_user.is_admin):
            logger.warning(
                'Acesso negado (requer_aprovador): %s tentou aceder a %s',
                current_user.email, request.path
            )
            flash('Sem permissão para aceder a esta área.', 'erro')
            abort(403)
        return f(*args, **kwargs)
    return decorated
