# Rotas de Orientadores — CRUD completo
from flask import render_template, redirect, url_for, flash, request
from app.blueprints.orientadores import orientadores_bp
from app.database import db
from core.auth_helpers import requer_admin


@orientadores_bp.route('/')
@requer_admin
def lista():
    orientadores = db.listar_orientadores()
    conexao = db.get_db()
    cur = conexao.cursor()
    stats = []
    for o in orientadores:
        oid = o['id']
        cur.execute('SELECT COUNT(*) FROM tcc_validos WHERE orientador_id=%s', (oid,))
        n_validos = cur.fetchone()[0]
        cur.execute('SELECT COUNT(*) FROM tcc_suspeitos WHERE orientador_id=%s', (oid,))
        n_suspeitos = cur.fetchone()[0]
        stats.append({'orientador': o, 'n_validos': n_validos, 'n_suspeitos': n_suspeitos,
                       'total': n_validos + n_suspeitos})
    cur.close()
    cursos = db.listar_cursos_admin()
    return render_template('orientadores/lista.html', stats=stats, cursos=cursos)


@orientadores_bp.route('/novo', methods=['GET', 'POST'])
@requer_admin
def novo():
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        email = request.form.get('email', '').strip()
        titulacao = request.form.get('titulacao', '').strip()
        curso_id_str = request.form.get('curso_id', '')
        curso_id = int(curso_id_str) if curso_id_str.isdigit() else None

        if not nome:
            flash('O nome é obrigatório.', 'erro')
            return redirect(url_for('orientadores.novo'))

        db.inserir_orientador(nome, email, titulacao, curso_id)
        flash('Orientador adicionado com sucesso!', 'sucesso')
        return redirect(url_for('orientadores.lista'))

    cursos = db.listar_cursos_admin()
    return render_template('orientadores/formulario.html', orientador=None, cursos=cursos)


@orientadores_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@requer_admin
def editar(id):
    orientador = db.buscar_orientador(id)
    if not orientador:
        flash('Orientador não encontrado.', 'erro')
        return redirect(url_for('orientadores.lista'))

    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        email = request.form.get('email', '').strip()
        titulacao = request.form.get('titulacao', '').strip()
        curso_id_str = request.form.get('curso_id', '')
        curso_id = int(curso_id_str) if curso_id_str.isdigit() else None

        if not nome:
            flash('O nome é obrigatório.', 'erro')
            return redirect(url_for('orientadores.editar', id=id))

        db.editar_orientador(id, nome, email, titulacao, curso_id)
        flash('Orientador actualizado com sucesso!', 'sucesso')
        return redirect(url_for('orientadores.lista'))

    cursos = db.listar_cursos_admin()
    return render_template('orientadores/formulario.html', orientador=orientador, cursos=cursos)


@orientadores_bp.route('/<int:id>/remover', methods=['POST'])
@requer_admin
def remover(id):
    db.remover_orientador(id)
    flash('Orientador removido.', 'sucesso')
    return redirect(url_for('orientadores.lista'))
