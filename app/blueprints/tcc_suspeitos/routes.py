# Rotas de TCC Suspeitos — submissão, listagem, gestão de estados
import os
import uuid
from flask import render_template, redirect, url_for, flash, request, current_app, send_file
from flask_login import current_user
from werkzeug.utils import secure_filename
from app.blueprints.tcc_suspeitos import tcc_suspeitos_bp
from app.database import db
from core.auth_helpers import requer_login, requer_admin, requer_carregador

EXTENSOES = {'pdf', 'docx', 'txt'}


def _ext_ok(nome):
    return '.' in nome and nome.rsplit('.', 1)[1].lower() in EXTENSOES


def _guardar(ficheiro):
    nome_orig = secure_filename(ficheiro.filename)
    ext = nome_orig.rsplit('.', 1)[1].lower() if '.' in nome_orig else 'txt'
    nome_seg = f'{uuid.uuid4().hex[:16]}.{ext}'
    caminho = os.path.join(current_app.config['UPLOAD_FOLDER'], nome_seg)
    ficheiro.save(caminho)
    return caminho, nome_orig


@tcc_suspeitos_bp.route('/')
@requer_login
def lista():
    curso_id = request.args.get('curso_id', type=int)
    estado = request.args.get('estado', '').strip()
    pesquisa = request.args.get('q', '').strip()
    pagina = request.args.get('pagina', 1, type=int)

    tccs, total = db.listar_tcc_suspeitos(
        curso_id=curso_id, estado=estado or None,
        pesquisa=pesquisa or None, pagina=pagina)
    cursos = db.listar_cursos_admin()
    total_paginas = max(1, (total + 19) // 20)

    return render_template('tcc_suspeitos/lista.html', tccs=tccs, cursos=cursos,
                           total=total, pagina=pagina, total_paginas=total_paginas,
                           filtro_curso=curso_id, filtro_estado=estado, filtro_q=pesquisa)


@tcc_suspeitos_bp.route('/submeter', methods=['GET', 'POST'])
@requer_carregador
def submeter():
    if request.method == 'POST':
        titulo = request.form.get('titulo', '').strip()
        autor = request.form.get('autor', '').strip()
        curso_id_str = request.form.get('curso_id', '')
        orientador_id_str = request.form.get('orientador_id', '')
        ano_str = request.form.get('ano', '')

        curso_id = int(curso_id_str) if curso_id_str.isdigit() else None
        orientador_id = int(orientador_id_str) if orientador_id_str.isdigit() else None
        ano = int(ano_str) if ano_str.isdigit() else None

        if not autor or not curso_id:
            flash('Autor e Curso são obrigatórios.', 'erro')
            return redirect(url_for('tcc_suspeitos.submeter'))

        ficheiros = request.files.getlist('ficheiros')
        ficheiros_validos = [f for f in ficheiros if f.filename and _ext_ok(f.filename)]
        if not ficheiros_validos:
            flash('Ficheiro obrigatório (.pdf, .docx, .txt).', 'erro')
            return redirect(url_for('tcc_suspeitos.submeter'))

        curso_obj = db.buscar_curso(curso_id)
        curso_nome = curso_obj['nome'] if curso_obj else ''
        orientador_nome = ''
        if orientador_id:
            ori = db.buscar_orientador(orientador_id)
            orientador_nome = ori['nome'] if ori else ''

        count = 0
        for ficheiro in ficheiros_validos:
            caminho, nome_orig = _guardar(ficheiro)
            tit = titulo if len(ficheiros_validos) == 1 else f'{titulo or nome_orig}'
            db.inserir_tcc_suspeito(
                autor=autor, caminho_ficheiro=caminho, titulo=tit,
                orientador_id=orientador_id, orientador_nome=orientador_nome,
                curso_id=curso_id, curso_nome=curso_nome, ano_submissao=ano,
                submetido_por=current_user.id)
            count += 1

        flash(f'{count} TCC submetido(s) para verificação.', 'sucesso')
        return redirect(url_for('tcc_suspeitos.lista'))

    cursos = db.listar_cursos_admin()
    orientadores = db.listar_orientadores()
    return render_template('tcc_suspeitos/submeter.html', cursos=cursos, orientadores=orientadores)


@tcc_suspeitos_bp.route('/<int:id>')
@requer_login
def detalhe(id):
    tcc = db.buscar_tcc_suspeito(id)
    if not tcc:
        flash('TCC suspeito não encontrado.', 'erro')
        return redirect(url_for('tcc_suspeitos.lista'))

    verificacoes = db.verificacoes_do_suspeito(id)
    return render_template('tcc_suspeitos/detalhe.html', tcc=tcc, verificacoes=verificacoes)


@tcc_suspeitos_bp.route('/<int:id>/estado', methods=['POST'])
@requer_admin
def mudar_estado(id):
    novo_estado = request.form.get('estado', '')
    if novo_estado in ('pendente', 'aprovado', 'reprovado'):
        db.actualizar_estado_suspeito(id, novo_estado)
        flash(f'Estado actualizado para: {novo_estado}.', 'sucesso')
    else:
        flash('Estado inválido.', 'erro')
    return redirect(url_for('tcc_suspeitos.detalhe', id=id))


@tcc_suspeitos_bp.route('/<int:id>/remover', methods=['POST'])
@requer_admin
def remover(id):
    db.remover_tcc_suspeito(id)
    flash('TCC suspeito removido.', 'sucesso')
    return redirect(url_for('tcc_suspeitos.lista'))


@tcc_suspeitos_bp.route('/<int:id>/download')
@requer_login
def download(id):
    tcc = db.buscar_tcc_suspeito(id)
    if tcc and tcc['caminho_ficheiro'] and os.path.exists(tcc['caminho_ficheiro']):
        return send_file(tcc['caminho_ficheiro'], as_attachment=True)
    flash('Ficheiro não encontrado.', 'erro')
    return redirect(url_for('tcc_suspeitos.detalhe', id=id))
