# IMETRO TFC v3 — API REST completa
from flask import jsonify, request, current_app
from app.blueprints.api import api_bp
from app.services.plagio_service import estado_sistema
from app.extensions import jobs
from app.database import db
from core.auth_helpers import requer_login


@api_bp.route('/status')
@requer_login
def status():
    try:
        return jsonify(estado_sistema())
    except Exception as e:
        return jsonify({'erro': str(e), 'modelo_ok': False, 'chroma_ok': False}), 200


@api_bp.route('/progresso/<job_id>')
@requer_login
def progresso(job_id):
    job = jobs.get(job_id, {'status': 'nao_encontrado', 'progresso': 0, 'total': 0})
    return jsonify(job)


@api_bp.route('/dashboard/stats')
@requer_login
def dashboard_stats():
    try:
        stats = {
            'tcc_validos': db.contar_tcc_validos(),
            'tcc_suspeitos': db.contar_tcc_suspeitos(),
            'verificacoes': db.contar_verificacoes(),
            'plagio_alto': db.contar_plagio_alto(),
            'cursos_activos': len([c for c in db.listar_cursos_admin() if c['activo']]),
            'pendentes': db.contar_tcc_suspeitos(estado='pendente'),
            'sem_abnt': db.contar_sem_abnt(),
            'por_nivel': db.contar_por_nivel(),
            'verificacoes_por_mes': db.verificacoes_por_mes(),
            'distribuicao_curso': db.distribuicao_por_curso(),
            'evolucao_media': db.evolucao_media_plagio(),
            'distribuicao_abnt': db.distribuicao_abnt(),
            'suspeitos_por_estado': db.suspeitos_por_estado(),
            'media_pct': db.media_percentagem()
        }
        return jsonify(stats)
    except Exception as e:
        return jsonify({'erro': str(e)}), 200


@api_bp.route('/cursos')
@requer_login
def cursos():
    return jsonify([dict(c) for c in db.listar_cursos_admin()])


@api_bp.route('/tcc-validos')
@requer_login
def tcc_validos():
    curso_id = request.args.get('curso_id', type=int)
    rows, total = db.listar_tcc_validos(curso_id=curso_id, pagina=1, por_pagina=100)
    return jsonify({'total': total, 'items': [dict(r) for r in rows]})


@api_bp.route('/tcc-suspeitos')
@requer_login
def tcc_suspeitos():
    estado = request.args.get('estado')
    rows, total = db.listar_tcc_suspeitos(estado=estado, pagina=1, por_pagina=100)
    return jsonify({'total': total, 'items': [dict(r) for r in rows]})


@api_bp.route('/verificacoes/<int:id>')
@requer_login
def verificacao(id):
    v = db.buscar_verificacao(id)
    if not v:
        return jsonify({'erro': 'Não encontrado'}), 404
    matches = db.listar_matches(id)
    return jsonify({'verificacao': dict(v), 'matches': [dict(m) for m in matches]})


@api_bp.route('/relatorio/<int:id>/json')
@requer_login
def relatorio_json(id):
    v = db.buscar_verificacao(id)
    if not v:
        return jsonify({'erro': 'Não encontrado'}), 404
    matches = db.listar_matches(id)
    chunks = db.listar_chunks_suspeitos(id)
    return jsonify({
        'verificacao': dict(v),
        'matches': [dict(m) for m in matches],
        'chunks': [dict(c) for c in chunks]
    })


@api_bp.route('/configuracoes', methods=['POST'])
@requer_login
def configuracoes():
    import json
    import os
    data = request.get_json()
    if not data:
        return jsonify({'erro': 'Dados inválidos'}), 400

    basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    config_path = os.path.join(basedir, 'instance', 'config.json')
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        for k, v in data.items():
            current_app.config[k] = v
        return jsonify({'sucesso': True})
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@api_bp.route('/analise-ia/<int:verificacao_id>', methods=['POST'])
@requer_login
def analise_ia(verificacao_id):
    """Placeholder para futura integração com IA."""
    return jsonify({
        'status': 'not_implemented',
        'message': 'Módulo IA em desenvolvimento. Em breve disponível.'
    }), 501
