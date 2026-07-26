from flask import render_template, redirect, url_for, flash, request
from app.blueprints.cursos import cursos_bp
from app.services import curso_service
from app.database import db
from core.auth_helpers import requer_admin

@cursos_bp.route('/')
@requer_admin
def lista():
    cursos = curso_service.listar_cursos_admin()

    conexao = db.get_db()
    cur = conexao.cursor()
    for c in cursos:
        cur.execute(
            'SELECT COUNT(*) FROM tcc_validos WHERE curso_id = %s', (c['id'],))
        c['num_monografias'] = cur.fetchone()[0]
        cur.execute(
            'SELECT COUNT(*) FROM tcc_suspeitos WHERE curso_id = %s', (c['id'],))
        c['num_suspeitos'] = cur.fetchone()[0]
        cur.execute(
            'SELECT COUNT(*) FROM verificacoes WHERE curso_id_filtro = %s', (c['id'],))
        c['num_verificacoes'] = cur.fetchone()[0]
        cur.execute(
            'SELECT AVG(percentagem_plagio) FROM verificacoes WHERE curso_id_filtro = %s', (c['id'],))
        media = cur.fetchone()[0]
        c['media_plagio'] = round(media, 1) if media else 0.0
    cur.close()

    return render_template('cursos/lista.html', cursos=cursos)


@cursos_bp.route('/novo', methods=['GET', 'POST'])
@requer_admin
def novo():
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        codigo = request.form.get('codigo', '').strip()
        departamento = request.form.get('departamento', '').strip()
        descricao = request.form.get('descricao', '').strip()
        activo = int(request.form.get('activo', 1))

        if not nome:
            flash('O nome do curso é obrigatório.', 'erro')
            return redirect(url_for('cursos.novo'))

        resultado = curso_service.criar_curso(nome, codigo, departamento, descricao, activo)
        if resultado['sucesso']:
            flash('Curso criado com sucesso!', 'sucesso')
            return redirect(url_for('cursos.lista'))
        else:
            flash(resultado['erro'], 'erro')
            return redirect(url_for('cursos.novo'))

    return render_template('cursos/formulario.html', curso=None)


@cursos_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@requer_admin
def editar(id: int):
    curso = curso_service.buscar_curso(id)
    if not curso:
        flash('Curso não encontrado.', 'erro')
        return redirect(url_for('cursos.lista'))

    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        codigo = request.form.get('codigo', '').strip()
        departamento = request.form.get('departamento', '').strip()
        descricao = request.form.get('descricao', '').strip()
        activo = int(request.form.get('activo', 1))

        if not nome:
            flash('O nome do curso é obrigatório.', 'erro')
            return redirect(url_for('cursos.editar', id=id))

        resultado = curso_service.editar_curso(id, nome, codigo, departamento, descricao, activo)
        if resultado['sucesso']:
            flash('Curso editado com sucesso!', 'sucesso')
            return redirect(url_for('cursos.lista'))
        else:
            flash(resultado['erro'], 'erro')
            return redirect(url_for('cursos.editar', id=id))

    return render_template('cursos/formulario.html', curso=curso)


@cursos_bp.route('/<int:id>', methods=['GET'])
@requer_admin
def detalhe(id: int):
    curso = curso_service.buscar_curso(id)
    if not curso:
        flash('Curso não encontrado.', 'erro')
        return redirect(url_for('cursos.lista'))

    conexao = db.get_db()
    cur = conexao.cursor()

    cur.execute(
        'SELECT * FROM tcc_validos WHERE curso_id = %s ORDER BY data_indexacao DESC', (id,))
    tcc_validos_cols = [d[0] for d in cur.description]
    tcc_validos = [dict(zip(tcc_validos_cols, row)) for row in cur.fetchall()]

    cur.execute(
        'SELECT * FROM tcc_suspeitos WHERE curso_id = %s ORDER BY data_submissao DESC', (id,))
    tcc_suspeitos_cols = [d[0] for d in cur.description]
    tcc_suspeitos = [dict(zip(tcc_suspeitos_cols, row)) for row in cur.fetchall()]

    cur.execute(
        'SELECT * FROM orientadores WHERE curso_id = %s', (id,))
    orientadores_cols = [d[0] for d in cur.description]
    orientadores = [dict(zip(orientadores_cols, row)) for row in cur.fetchall()]

    num_validos = len(tcc_validos)
    total_chunks = sum([m['num_chunks'] for m in tcc_validos]) if tcc_validos else 0

    cur.execute(
        'SELECT * FROM verificacoes WHERE curso_id_filtro = %s', (id,))
    verifs_cols = [d[0] for d in cur.description]
    verifs = [dict(zip(verifs_cols, row)) for row in cur.fetchall()]
    media_plagio = sum([v['percentagem_plagio'] for v in verifs]) / len(verifs) if verifs else 0.0
    plagio_alto = sum(1 for v in verifs if v['nivel'] in ('Alto', 'Critico'))
    cur.close()

    return render_template('cursos/detalhe.html',
                           curso=curso,
                           tcc_validos=tcc_validos,
                           tcc_suspeitos=tcc_suspeitos,
                           orientadores=orientadores,
                           estatisticas={
                               'num_validos': num_validos,
                               'num_suspeitos': len(tcc_suspeitos),
                               'total_chunks': total_chunks,
                               'media_plagio': round(media_plagio, 1),
                               'plagio_alto': plagio_alto,
                               'num_orientadores': len(orientadores)
                           })


@cursos_bp.route('/<int:id>/remover', methods=['POST'])
@requer_admin
def remover(id: int):
    resultado = curso_service.remover_curso(id)
    if resultado['sucesso']:
        flash('Curso removido com sucesso.', 'sucesso')
    else:
        flash(resultado['erro'], 'erro')
    return redirect(url_for('cursos.lista'))
