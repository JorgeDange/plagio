# IMETRO TFC v3 — Configurações
from flask import render_template, redirect, url_for, flash, request, current_app, send_file
import os
import json
import time
from app.blueprints.configuracoes import config_bp
from app.services.plagio_service import estado_sistema
from app.database import db
from core.auth_helpers import requer_admin


def _dir_size(path):
    total = 0
    try:
        with os.scandir(path) as it:
            for entry in it:
                if entry.is_file():
                    total += entry.stat().st_size
                elif entry.is_dir():
                    total += _dir_size(entry.path)
    except Exception:
        pass
    return total


def _fmt_size(b):
    for u in ('B', 'KB', 'MB', 'GB'):
        if b < 1024:
            return f'{b:.1f} {u}'
        b /= 1024
    return f'{b:.1f} TB'


@config_bp.route('/')
@requer_admin
def index():
    estado = estado_sistema()
    basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    config_path = os.path.join(basedir, 'instance', 'config.json')
    config = {}
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except Exception:
            pass

    db_path = current_app.config.get('DB_PATH', '')
    db_size = _fmt_size(os.path.getsize(db_path)) if os.path.exists(db_path) else '0 B'

    storage = {
        'upload_size': _fmt_size(_dir_size(current_app.config['UPLOAD_FOLDER'])),
        'relatorios_size': _fmt_size(_dir_size(current_app.config['RELATORIOS_FOLDER'])),
        'db_size': db_size
    }

    llm = {
        "enabled":  current_app.config.get("LLM_ENABLED", "false"),
        "provider": current_app.config.get("LLM_PROVIDER", ""),
        "model":    current_app.config.get("LLM_MODEL", ""),
    }
    return render_template('configuracoes/index.html',
                           estado=estado, config=config, storage=storage,
                           limiar=current_app.config.get('LIMIAR_PLAGIO', 0.85),
                           chunk_size=current_app.config.get('CHUNK_SIZE', 200),
                           chunk_overlap=current_app.config.get('CHUNK_OVERLAP', 50),
                           llm=llm)


@config_bp.route('/guardar', methods=['POST'])
@requer_admin
def guardar():
    limiar = request.form.get('limiar', type=float) or 0.85
    chunk_size = request.form.get('chunk_size', type=int) or 200
    chunk_overlap = request.form.get('chunk_overlap', type=int) or 50
    nivel_baixo = request.form.get('nivel_baixo', type=float) or 10
    nivel_moderado = request.form.get('nivel_moderado', type=float) or 30
    nivel_alto = request.form.get('nivel_alto', type=float) or 60

    config = {
        'LIMIAR_PLAGIO': limiar,
        'CHUNK_SIZE': chunk_size,
        'CHUNK_OVERLAP': chunk_overlap,
        'NIVEL_BAIXO': nivel_baixo,
        'NIVEL_MODERADO': nivel_moderado,
        'NIVEL_ALTO': nivel_alto,
        'EMAIL_CORTESIA': request.form.get('email_cortesia', '').strip(),
        'CORE_KEY': request.form.get('core_key', '').strip(),
        'SEMANTIC_SCHOLAR_KEY': request.form.get('semantic_scholar_key', '').strip(),
        'LIMIAR_EXTERNO': request.form.get('limiar_externo', type=float) or 70.0,
        'FONTES_EXTERNAS': request.form.getlist('fontes_externas[]') or ['openalex', 'semantic_scholar', 'core', 'crossref']
    }

    basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    config_path = os.path.join(basedir, 'instance', 'config.json')
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        current_app.config.update(config)
        flash('Configurações guardadas com sucesso!', 'sucesso')
    except Exception as e:
        flash(f'Erro ao guardar: {e}', 'erro')

    return redirect(url_for('configuracoes.index'))


@config_bp.route('/limpar/<tipo>', methods=['POST'])
@requer_admin
def limpar(tipo):
    if tipo == 'uploads':
        pasta = current_app.config['UPLOAD_FOLDER']
    elif tipo == 'relatorios':
        pasta = current_app.config['RELATORIOS_FOLDER']
    else:
        flash('Tipo inválido.', 'erro')
        return redirect(url_for('configuracoes.index'))

    count = 0
    for fn in os.listdir(pasta):
        fp = os.path.join(pasta, fn)
        try:
            if os.path.isfile(fp):
                os.unlink(fp)
                count += 1
        except Exception:
            pass
    flash(f'{count} ficheiro(s) removido(s).', 'sucesso')
    return redirect(url_for('configuracoes.index'))


@config_bp.route('/exportar-db')
@requer_admin
def exportar_db():
    db_path = current_app.config.get('DB_PATH', '')
    if os.path.exists(db_path):
        return send_file(db_path, as_attachment=True, download_name='plagio.db')
    flash('Base de dados não encontrada.', 'erro')
    return redirect(url_for('configuracoes.index'))


@config_bp.route('/pesquisa-externa')
@requer_admin
def pesquisa_externa():
    conn = db.get_db()
    cur = conn.cursor()
    cur.execute("SELECT chave, valor FROM config_pesquisa_externa")
    cols = [d[0] for d in cur.description]
    rows = [dict(zip(cols, row)) for row in cur.fetchall()]
    cur.close()
    config = {row['chave']: row['valor'] for row in rows}
    
    if 'fase0_ativa' not in config: config['fase0_ativa'] = 'false'
    if 'core_api_key' not in config: config['core_api_key'] = ''
    if 'max_chunks_externos' not in config: config['max_chunks_externos'] = '10'
    if 'score_minimo_externo' not in config: config['score_minimo_externo'] = '0.70'
    if 'apis_activas' not in config: config['apis_activas'] = 'core,openalex,semanticscholar'
    if 'timeout_api' not in config: config['timeout_api'] = '8'
    
    config['apis_activas_list'] = config['apis_activas'].split(',')
    
    return render_template('configuracoes/pesquisa_externa.html', config=config)


@config_bp.route('/pesquisa-externa', methods=['POST'])
@requer_admin
def guardar_pesquisa_externa():
    fase0_ativa = 'true' if request.form.get('fase0_ativa') else 'false'
    core_api_key = request.form.get('core_api_key', '').strip()
    max_chunks_externos = request.form.get('max_chunks_externos', '10')
    score_minimo_externo = request.form.get('score_minimo_externo', '0.70')
    timeout_api = request.form.get('timeout_api', '8')
    
    apis_activas = request.form.getlist('apis_activas')
    apis_activas_str = ','.join(apis_activas)
    
    conn = db.get_db()
    cur = conn.cursor()
    for chave, valor in [
        ('fase0_ativa', fase0_ativa),
        ('core_api_key', core_api_key),
        ('max_chunks_externos', max_chunks_externos),
        ('score_minimo_externo', score_minimo_externo),
        ('timeout_api', timeout_api),
        ('apis_activas', apis_activas_str)
    ]:
        cur.execute("REPLACE INTO config_pesquisa_externa (chave, valor) VALUES (%s, %s)", (chave, valor))
    conn.commit()
    cur.close()
    
    flash('Configurações de pesquisa externa guardadas com sucesso!', 'sucesso')
    return redirect(url_for('configuracoes.pesquisa_externa'))


@config_bp.route('/pesquisa-externa/testar', methods=['POST'])
@requer_admin
def testar_pesquisa_externa():
    from core.pesquisa_externa import CoreAPI, OpenAlexAPI, SemanticScholarAPI, RCAAPApi, ArxivAPI
    
    apis_activas = request.form.get('apis_activas', '').split(',')
    core_api_key = request.form.get('core_api_key', '')
    timeout = int(request.form.get('timeout_api', '8'))
    
    resultados = []
    query = "inteligência artificial aprendizagem automática"
    
    motores = []
    if 'core' in apis_activas: motores.append(("CORE", CoreAPI(core_api_key, timeout)))
    if 'openalex' in apis_activas: motores.append(("OpenAlex", OpenAlexAPI(timeout)))
    if 'semanticscholar' in apis_activas: motores.append(("Semantic Scholar", SemanticScholarAPI(timeout)))
    if 'rcaap' in apis_activas: motores.append(("RCAAP", RCAAPApi(timeout)))
    if 'arxiv' in apis_activas: motores.append(("arXiv", ArxivAPI(timeout)))
    
    for nome, motor in motores:
        start_time = time.time()
        try:
            res = motor.pesquisar(query, limite=1)
            elapsed = int((time.time() - start_time) * 1000)
            status = "OK" if res else "Aviso (0 resultados)"
            resultados.append({"nome": nome, "status": status, "tempo_ms": elapsed})
        except Exception as e:
            elapsed = int((time.time() - start_time) * 1000)
            resultados.append({"nome": nome, "status": f"ERRO: {str(e)}", "tempo_ms": elapsed})
            
    return {"sucesso": True, "resultados": resultados}
