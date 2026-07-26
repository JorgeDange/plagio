# IMETRO TFC v3 — Rotas de Autenticação
from datetime import datetime
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from flask_bcrypt import generate_password_hash
from app.blueprints.auth import auth_bp
from app.database.db import get_db
from core.models.utilizador import Utilizador


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Página e processamento de login."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Email e password são obrigatórios.', 'erro')
            return render_template('auth/login.html')

        utilizador = Utilizador.carregar_por_email(email)

        if not utilizador:
            flash('Email ou password incorrectos.', 'erro')
            return render_template('auth/login.html')

        if not utilizador.is_active:
            flash('Conta desactivada. Contacte o administrador.', 'erro')
            return render_template('auth/login.html')

        if not utilizador.verificar_password(password):
            flash('Email ou password incorrectos.', 'erro')
            return render_template('auth/login.html')

        login_user(utilizador, remember=True)

        db = get_db()
        cur = db.cursor()
        cur.execute(
            'UPDATE utilizadores SET ultimo_login = %s WHERE id = %s',
            (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), utilizador.id)
        )
        db.commit()
        cur.close()

        flash(f'Bem-vindo, {utilizador.nome}!', 'sucesso')

        next_page = request.args.get('next')
        if next_page and next_page.startswith('/'):
            return redirect(next_page)
        return redirect(url_for('main.dashboard'))

    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """Termina sessão."""
    logout_user()
    flash('Sessão terminada com sucesso.', 'sucesso')
    return redirect(url_for('auth.login'))


@auth_bp.route('/perfil', methods=['GET', 'POST'])
@login_required
def perfil():
    """Ver e alterar dados do próprio utilizador."""
    if request.method == 'POST':
        password_actual = request.form.get('password_actual', '')
        password_nova = request.form.get('password_nova', '')
        password_confirmar = request.form.get('password_confirmar', '')

        if not password_actual:
            flash('Introduza a password actual.', 'erro')
            return redirect(url_for('auth.perfil'))

        if not current_user.verificar_password(password_actual):
            flash('Password actual incorrecta.', 'erro')
            return redirect(url_for('auth.perfil'))

        if len(password_nova) < 8:
            flash('A nova password deve ter pelo menos 8 caracteres.', 'erro')
            return redirect(url_for('auth.perfil'))

        if password_nova != password_confirmar:
            flash('As passwords não coincidem.', 'erro')
            return redirect(url_for('auth.perfil'))

        novo_hash = generate_password_hash(password_nova).decode('utf-8')
        db = get_db()
        cur = db.cursor()
        cur.execute(
            'UPDATE utilizadores SET password_hash = %s WHERE id = %s',
            (novo_hash, current_user.id)
        )
        db.commit()
        cur.close()

        flash('Password alterada com sucesso!', 'sucesso')
        return redirect(url_for('auth.perfil'))

    return render_template('auth/perfil.html')
