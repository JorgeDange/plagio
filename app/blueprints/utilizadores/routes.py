# IMETRO TFC v3 — Rotas de Gestão de Utilizadores (apenas administrador)
from flask import render_template, redirect, url_for, flash, request
from flask_bcrypt import generate_password_hash
from app.blueprints.utilizadores import utilizadores_bp
from app.database.db import get_db
from core.auth_helpers import requer_admin


@utilizadores_bp.route('/')
@requer_admin
def lista():
    """Lista todos os utilizadores do sistema."""
    db = get_db()
    cur = db.cursor()
    cur.execute('SELECT * FROM utilizadores ORDER BY criado_em DESC')
    cols = [d[0] for d in cur.description]
    utilizadores = [dict(zip(cols, row)) for row in cur.fetchall()]
    cur.close()
    return render_template('utilizadores/lista.html', utilizadores=utilizadores)


@utilizadores_bp.route('/novo', methods=['GET', 'POST'])
@requer_admin
def novo():
    """Criar novo utilizador."""
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        papel = request.form.get('papel', '')

        if not nome or not email or not password or not papel:
            flash('Todos os campos são obrigatórios.', 'erro')
            return redirect(url_for('utilizadores.novo'))

        if len(password) < 8:
            flash('A password deve ter pelo menos 8 caracteres.', 'erro')
            return redirect(url_for('utilizadores.novo'))

        if papel not in ('administrador', 'carregador', 'verificador', 'aprovador'):
            flash('Papel inválido.', 'erro')
            return redirect(url_for('utilizadores.novo'))

        db = get_db()
        cur = db.cursor()

        cur.execute(
            'SELECT id FROM utilizadores WHERE email = %s', (email,)
        )
        existente = cur.fetchone()
        if existente:
            cur.close()
            flash('Já existe um utilizador com este email.', 'erro')
            return redirect(url_for('utilizadores.novo'))

        password_hash = generate_password_hash(password).decode('utf-8')
        cur.execute(
            '''INSERT INTO utilizadores (nome, email, password_hash, papel)
               VALUES (%s, %s, %s, %s)''',
            (nome, email, password_hash, papel)
        )
        db.commit()
        cur.close()

        flash(f'Utilizador "{nome}" criado com sucesso!', 'sucesso')
        return redirect(url_for('utilizadores.lista'))

    return render_template('utilizadores/form.html', utilizador=None)


@utilizadores_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@requer_admin
def editar(id):
    """Editar nome, email e papel de um utilizador."""
    db = get_db()
    cur = db.cursor()
    cur.execute('SELECT * FROM utilizadores WHERE id = %s', (id,))
    cols = [d[0] for d in cur.description]
    row = cur.fetchone()
    utilizador = dict(zip(cols, row)) if row else None

    if not utilizador:
        cur.close()
        flash('Utilizador não encontrado.', 'erro')
        return redirect(url_for('utilizadores.lista'))

    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        email = request.form.get('email', '').strip().lower()
        papel = request.form.get('papel', '')

        if not nome or not email or not papel:
            flash('Nome, email e papel são obrigatórios.', 'erro')
            return redirect(url_for('utilizadores.editar', id=id))

        if papel not in ('administrador', 'carregador', 'verificador', 'aprovador'):
            flash('Papel inválido.', 'erro')
            return redirect(url_for('utilizadores.editar', id=id))

        cur.execute(
            'SELECT id FROM utilizadores WHERE email = %s AND id != %s', (email, id)
        )
        existente = cur.fetchone()
        if existente:
            flash('Já existe outro utilizador com este email.', 'erro')
            return redirect(url_for('utilizadores.editar', id=id))

        cur.execute(
            'UPDATE utilizadores SET nome = %s, email = %s, papel = %s WHERE id = %s',
            (nome, email, papel, id)
        )
        db.commit()
        cur.close()

        flash(f'Utilizador "{nome}" actualizado com sucesso!', 'sucesso')
        return redirect(url_for('utilizadores.lista'))

    cur.close()
    return render_template('utilizadores/form.html', utilizador=utilizador)


@utilizadores_bp.route('/<int:id>/toggle', methods=['POST'])
@requer_admin
def toggle(id):
    """Activar/desactivar conta de utilizador."""
    db = get_db()
    cur = db.cursor()
    cur.execute('SELECT * FROM utilizadores WHERE id = %s', (id,))
    cols = [d[0] for d in cur.description]
    row = cur.fetchone()
    utilizador = dict(zip(cols, row)) if row else None

    if not utilizador:
        cur.close()
        flash('Utilizador não encontrado.', 'erro')
        return redirect(url_for('utilizadores.lista'))

    if utilizador['ativo'] == 1 and utilizador['papel'] == 'administrador':
        cur.execute(
            "SELECT COUNT(*) FROM utilizadores WHERE papel = 'administrador' AND ativo = 1"
        )
        admins_activos = cur.fetchone()[0]
        if admins_activos <= 1:
            cur.close()
            flash('Não é possível desactivar o único administrador activo.', 'erro')
            return redirect(url_for('utilizadores.lista'))

    novo_estado = 0 if utilizador['ativo'] == 1 else 1
    cur.execute(
        'UPDATE utilizadores SET ativo = %s WHERE id = %s', (novo_estado, id)
    )
    db.commit()
    cur.close()

    estado_texto = 'activada' if novo_estado == 1 else 'desactivada'
    flash(f'Conta de "{utilizador["nome"]}" {estado_texto}.', 'sucesso')
    return redirect(url_for('utilizadores.lista'))


@utilizadores_bp.route('/<int:id>/reset', methods=['POST'])
@requer_admin
def reset_password(id):
    """Admin reseta a password de um utilizador."""
    db = get_db()
    cur = db.cursor()
    cur.execute('SELECT * FROM utilizadores WHERE id = %s', (id,))
    cols = [d[0] for d in cur.description]
    row = cur.fetchone()
    utilizador = dict(zip(cols, row)) if row else None

    if not utilizador:
        cur.close()
        flash('Utilizador não encontrado.', 'erro')
        return redirect(url_for('utilizadores.lista'))

    nova_password = request.form.get('nova_password', '')

    if len(nova_password) < 8:
        cur.close()
        flash('A password deve ter pelo menos 8 caracteres.', 'erro')
        return redirect(url_for('utilizadores.lista'))

    password_hash = generate_password_hash(nova_password).decode('utf-8')
    cur.execute(
        'UPDATE utilizadores SET password_hash = %s WHERE id = %s',
        (password_hash, id)
    )
    db.commit()
    cur.close()

    flash(f'Password de "{utilizador["nome"]}" redefinida com sucesso.', 'sucesso')
    return redirect(url_for('utilizadores.lista'))
