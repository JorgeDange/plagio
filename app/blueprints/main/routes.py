# IMETRO TFC v3 — Dashboard Routes
from flask import render_template, current_app
from app.blueprints.main import main_bp
from app.database import db
from app.services.plagio_service import estado_sistema
from core.auth_helpers import requer_login


@main_bp.route('/')
@requer_login
def dashboard():
    try:
        from flask_login import current_user

        if current_user.is_carregador:
            meus_envios = db.listar_tcc_suspeitos_por_utilizador(current_user.id)
            stats = {
                'total_enviados': len(meus_envios),
                'pendentes': len([t for t in meus_envios if t.get('estado') == 'pendente']),
                'em_verificacao': len([t for t in meus_envios if t.get('estado') == 'em_verificacao']),
                'verificados': len([t for t in meus_envios if t.get('estado') == 'verificado']),
            }
            return render_template('main/dashboard.html', stats=stats, meus_envios=meus_envios, is_carregador=True)

        def _safe(fn, default=None):
            try:
                return fn()
            except Exception as e:
                current_app.logger.error(f'Dashboard [{fn.__name__}]: {e}')
                return default if default is not None else (0 if default is None else default)

        stats = {
            'tcc_validos': _safe(db.contar_tcc_validos, 0),
            'tcc_suspeitos': _safe(db.contar_tcc_suspeitos, 0),
            'total_verificacoes': _safe(db.contar_verificacoes, 0),
            'plagio_alto': _safe(db.contar_plagio_alto, 0),
            'cursos_activos': len([c for c in _safe(db.listar_cursos_admin, []) if c.get('activo')]),
            'pendentes': _safe(lambda: db.contar_tcc_suspeitos(estado='pendente'), 0),
            'pendentes_normas': _safe(db.contar_pendentes_normas, 0),
            'sem_abnt': _safe(db.contar_sem_abnt, 0),
            'media_pct': _safe(db.media_percentagem, 0),
            'por_nivel': _safe(db.contar_por_nivel, {'Baixo': 0, 'Moderado': 0, 'Alto': 0, 'Critico': 0}),
            'sistema': _safe(estado_sistema, {'modelo_ok': False, 'chroma_ok': False, 'ram_gb': 0, 'chunks': 0}),
            'verificacoes_por_mes': _safe(db.verificacoes_por_mes, {}),
            'verificacoes_mensais': _safe(db.verificacoes_por_mes_aprov_reprov, []),
            'distribuicao_curso': _safe(db.distribuicao_por_curso, {}),
            'evolucao_media': _safe(db.evolucao_media_plagio, {}),
            'distribuicao_abnt': _safe(db.distribuicao_abnt, {}),
            'suspeitos_por_estado': _safe(db.suspeitos_por_estado, {})
        }
        verificacoes = _safe(lambda: db.listar_verificacoes(limite=10), [])
        return render_template('main/dashboard.html', stats=stats, verificacoes=verificacoes, is_carregador=False)
    except Exception as e:
        return render_template('main/dashboard.html',
            stats={'tcc_validos': 0, 'tcc_suspeitos': 0, 'total_verificacoes': 0,
                   'plagio_alto': 0, 'cursos_activos': 0, 'pendentes': 0, 'pendentes_normas': 0,
                   'sem_abnt': 0, 'media_pct': 0, 'por_nivel': {'Baixo': 0, 'Moderado': 0, 'Alto': 0, 'Critico': 0},
                   'sistema': {'modelo_ok': False, 'chroma_ok': False, 'ram_gb': 0, 'chunks': 0},
                   'verificacoes_por_mes': {}, 'verificacoes_mensais': [], 'distribuicao_curso': {},
                   'evolucao_media': {}, 'distribuicao_abnt': {}, 'suspeitos_por_estado': {}},
            verificacoes=[], is_carregador=False, erro=str(e))
