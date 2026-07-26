# Rotas de TCC Válidos — listagem, indexação, detalhe, remoção
import os
import uuid
import threading
from flask import render_template, redirect, url_for, flash, request, current_app, send_file
from werkzeug.utils import secure_filename
from app.blueprints.tcc_validos import tcc_validos_bp
from app.database import db
from app.extensions import jobs
from app.services import plagio_service
from core.auth_helpers import requer_admin

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


@tcc_validos_bp.route('/')
@requer_admin
def lista():
    curso_id = request.args.get('curso_id', type=int)
    ano = request.args.get('ano', type=int)
    pesquisa = request.args.get('q', '').strip()
    pagina = request.args.get('pagina', 1, type=int)

    tccs, total = db.listar_tcc_validos(curso_id=curso_id, ano=ano,
                                         pesquisa=pesquisa or None, pagina=pagina)
    cursos = db.listar_cursos_admin()
    conexao = db.get_db()
    cur = conexao.cursor()
    cur.execute(
        'SELECT DISTINCT ano_defesa FROM tcc_validos WHERE ano_defesa IS NOT NULL ORDER BY ano_defesa DESC'
    )
    anos = [row[0] for row in cur.fetchall()]
    cur.close()
    total_paginas = max(1, (total + 19) // 20)

    return render_template('tcc_validos/lista.html', tccs=tccs, cursos=cursos,
                           anos=anos,
                           total=total, pagina=pagina, total_paginas=total_paginas,
                           filtro_curso=curso_id, filtro_ano=ano, filtro_q=pesquisa)


@tcc_validos_bp.route('/adicionar', methods=['GET', 'POST'])
@requer_admin
def adicionar():
    if request.method == 'POST':
        titulo = request.form.get('titulo', '').strip()
        autor = request.form.get('autor', '').strip()
        curso_id_str = request.form.get('curso_id', '')
        orientador_id_str = request.form.get('orientador_id', '')
        ano_str = request.form.get('ano_defesa', '')
        semestre = request.form.get('semestre', '')
        palavras_chave = request.form.get('palavras_chave', '').strip()
        resumo = request.form.get('resumo', '').strip()
        nota_str = request.form.get('nota_final', '')

        curso_id = int(curso_id_str) if curso_id_str.isdigit() else None
        orientador_id = int(orientador_id_str) if orientador_id_str.isdigit() else None
        ano = int(ano_str) if ano_str.isdigit() else None
        nota = float(nota_str) if nota_str.replace('.', '', 1).isdigit() else None

        ficheiros = request.files.getlist('ficheiros')

        if not titulo or not autor or not curso_id:
            flash('Título, Autor e Curso são obrigatórios.', 'erro')
            return redirect(url_for('tcc_validos.adicionar'))

        ficheiros_validos = [f for f in ficheiros if f.filename and _ext_ok(f.filename)]
        if not ficheiros_validos:
            flash('Ficheiro obrigatório (.pdf, .docx, .txt).', 'erro')
            return redirect(url_for('tcc_validos.adicionar'))

        curso_obj = db.buscar_curso(curso_id)
        curso_nome = curso_obj['nome'] if curso_obj else ''
        orientador_nome = ''
        if orientador_id:
            ori = db.buscar_orientador(orientador_id)
            orientador_nome = ori['nome'] if ori else ''

        ficheiro = ficheiros_validos[0]
        caminho, _ = _guardar(ficheiro)
        chroma_id = uuid.uuid4().hex[:12]

        job_id = uuid.uuid4().hex[:12]
        jobs[job_id] = {'status': 'em_progresso', 'progresso': 0, 'total': 1, 'resultados': []}

        app_ref = current_app._get_current_object()

        def processar(app_r, job_id_r, cam, chroma_r, tit, aut, c_nome, c_id, o_id, o_nome,
                      ano_r, sem, pkw, res, nota_r):
            with app_r.app_context():
                try:
                    resultado = plagio_service.indexar_monografia(
                        caminho=cam, titulo=tit, autor=aut, curso=c_nome,
                        monografia_id=chroma_r, curso_id=str(c_id) if c_id else '',
                        ano=str(ano_r) if ano_r else '')
                    if resultado['sucesso']:
                        db.inserir_tcc_valido(
                            titulo=tit, autor=aut, curso_id=c_id, curso_nome=c_nome,
                            orientador_id=o_id, orientador_nome=o_nome,
                            ano_defesa=ano_r, semestre=sem, palavras_chave=pkw,
                            resumo=res, nota_final=nota_r,
                            num_chunks=resultado['num_chunks'], caminho=cam,
                            chroma_id=resultado['chroma_id'])
                        jobs[job_id_r]['resultados'].append({'sucesso': True})
                    else:
                        jobs[job_id_r]['resultados'].append({'sucesso': False, 'erro': resultado['erro']})
                except Exception as e:
                    jobs[job_id_r]['resultados'].append({'sucesso': False, 'erro': str(e)})
                jobs[job_id_r]['progresso'] = 1
                jobs[job_id_r]['status'] = 'concluido'

        thread = threading.Thread(target=processar, daemon=True,
            args=(app_ref, job_id, caminho, chroma_id, titulo, autor, curso_nome, curso_id,
                  orientador_id, orientador_nome, ano, semestre, palavras_chave, resumo, nota))
        thread.start()

        return render_template('tcc_validos/progresso.html', job_id=job_id)

    cursos = db.listar_cursos_admin()
    orientadores = db.listar_orientadores()
    return render_template('tcc_validos/adicionar.html', cursos=cursos, orientadores=orientadores)


@tcc_validos_bp.route('/<int:id>')
@requer_admin
def detalhe(id):
    tcc = db.buscar_tcc_valido(id)
    if not tcc:
        flash('TCC não encontrado.', 'erro')
        return redirect(url_for('tcc_validos.lista'))

    conexao = db.get_db()
    cur = conexao.cursor()
    cur.execute('''
        SELECT m.*, v.data, v.percentagem_plagio, v.nivel,
               s.titulo as susp_titulo, s.autor as susp_autor
        FROM matches m
        JOIN verificacoes v ON m.verificacao_id = v.id
        LEFT JOIN tcc_suspeitos s ON v.tcc_suspeito_id = s.id
        WHERE m.tcc_valido_id = %s ORDER BY v.data DESC
    ''', (id,))
    cols = [d[0] for d in cur.description]
    matches_como_origem = [dict(zip(cols, row)) for row in cur.fetchall()]
    cur.close()

    return render_template('tcc_validos/detalhe.html', tcc=tcc, matches_origem=matches_como_origem)


@tcc_validos_bp.route('/<int:id>/remover', methods=['POST'])
@requer_admin
def remover(id):
    tcc = db.buscar_tcc_valido(id)
    if tcc and tcc['chroma_id']:
        try:
            from app.extensions import modelo_lock
            coleccao = current_app.config.get('COLECCAO')
            if coleccao:
                with modelo_lock:
                    res = coleccao.get(where={'monografia_id': tcc['chroma_id']})
                    if res and res['ids']:
                        coleccao.delete(ids=res['ids'])
        except Exception as e:
            print(f'[Aviso] Erro ao remover chunks ChromaDB: {e}')

    db.remover_tcc_valido(id)
    flash('TCC válido removido com sucesso.', 'sucesso')
    return redirect(url_for('tcc_validos.lista'))


@tcc_validos_bp.route('/<int:id>/download')
@requer_admin
def download(id):
    tcc = db.buscar_tcc_valido(id)
    if tcc and tcc['caminho_ficheiro'] and os.path.exists(tcc['caminho_ficheiro']):
        return send_file(tcc['caminho_ficheiro'], as_attachment=True)
    flash('Ficheiro não encontrado.', 'erro')
    return redirect(url_for('tcc_validos.detalhe', id=id))
