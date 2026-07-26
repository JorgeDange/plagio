# IMETRO TFC v3 — Rotas de Aprovação de TCC
from datetime import datetime
from flask import render_template, redirect, url_for, flash, request
from flask_login import current_user
from app.blueprints.aprovacoes import aprovacoes_bp
from app.database.db import get_db
from core.auth_helpers import requer_aprovador


@aprovacoes_bp.route('/historico')
@requer_aprovador
def historico():
    """Lista todos os TCC com estado != 'pendente'."""
    db = get_db()
    estado_filtro = request.args.get('estado', '').strip()
    pagina = request.args.get('pagina', 1, type=int)
    por_pagina = 20

    where = ["s.estado != 'pendente'"]
    params = []

    if estado_filtro and estado_filtro in ('verificado', 'aprovado', 'rejeitado'):
        where.append('s.estado = %s')
        params.append(estado_filtro)

    clause = 'WHERE ' + ' AND '.join(where)
    cur = db.cursor()
    cur.execute(
        f'SELECT COUNT(*) FROM tcc_suspeitos s {clause}', params
    )
    total = cur.fetchone()[0]

    offset = (pagina - 1) * por_pagina
    cur.execute(
        f'''SELECT s.*, u.nome as aprovador_nome,
                   vn.classificacao_final as normas_classificacao,
                   vn.requer_correcao as normas_requer_correcao,
                   vf.classificacao as veredicto_classificacao,
                   vf.score_global as veredicto_score,
                   v.id as veredicto_verificacao_id
            FROM tcc_suspeitos s
            LEFT JOIN utilizadores u ON s.aprovado_por = u.id
            LEFT JOIN verificacoes v ON v.id = s.ultima_verificacao_id
            LEFT JOIN verificacoes_normas vn ON vn.verificacao_id = v.id
            LEFT JOIN veredictos_finais vf ON vf.verificacao_id = v.id
            {clause}
            ORDER BY s.data_submissao DESC
            LIMIT %s OFFSET %s''',
        params + [por_pagina, offset]
    )
    cols = [d[0] for d in cur.description]
    tccs = [dict(zip(cols, row)) for row in cur.fetchall()]
    cur.close()

    total_paginas = max(1, (total + por_pagina - 1) // por_pagina)

    return render_template('aprovacoes/historico.html',
                           tccs=tccs, total=total, pagina=pagina,
                           total_paginas=total_paginas,
                           filtro_estado=estado_filtro)


@aprovacoes_bp.route('/<int:id>/aprovar', methods=['POST'])
@requer_aprovador
def aprovar(id):
    """Muda estado para 'aprovado' e guarda nota."""
    db = get_db()
    cur = db.cursor()
    cur.execute('SELECT * FROM tcc_suspeitos WHERE id = %s', (id,))
    cols = [d[0] for d in cur.description]
    row = cur.fetchone()
    tcc = dict(zip(cols, row)) if row else None

    if not tcc:
        cur.close()
        flash('TCC não encontrado.', 'erro')
        return redirect(url_for('aprovacoes.historico'))

    if tcc['estado'] not in ('verificado',):
        cur.close()
        flash('Apenas TCC já verificados podem ser aprovados.', 'erro')
        return redirect(url_for('aprovacoes.historico'))

    nota = request.form.get('nota_aprovacao', '').strip()

    cur.execute(
        '''UPDATE tcc_suspeitos
           SET estado = 'aprovado', aprovado_por = %s, aprovado_em = %s, nota_aprovacao = %s
           WHERE id = %s''',
        (current_user.id, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), nota, id)
    )
    db.commit()
    cur.close()

    flash('TCC aprovado com sucesso.', 'sucesso')
    return redirect(url_for('aprovacoes.historico'))


@aprovacoes_bp.route('/<int:id>/rejeitar', methods=['POST'])
@requer_aprovador
def rejeitar(id):
    """Muda estado para 'rejeitado' e guarda nota."""
    db = get_db()
    cur = db.cursor()
    cur.execute('SELECT * FROM tcc_suspeitos WHERE id = %s', (id,))
    cols = [d[0] for d in cur.description]
    row = cur.fetchone()
    tcc = dict(zip(cols, row)) if row else None

    if not tcc:
        cur.close()
        flash('TCC não encontrado.', 'erro')
        return redirect(url_for('aprovacoes.historico'))

    if tcc['estado'] not in ('verificado',):
        cur.close()
        flash('Apenas TCC já verificados podem ser rejeitados.', 'erro')
        return redirect(url_for('aprovacoes.historico'))

    nota = request.form.get('nota_aprovacao', '').strip()

    if not nota:
        flash('A justificativa é obrigatória para rejeição.', 'erro')
        return redirect(url_for('aprovacoes.historico'))

    cur.execute(
        '''UPDATE tcc_suspeitos
           SET estado = 'rejeitado', aprovado_por = %s, aprovado_em = %s, nota_aprovacao = %s
           WHERE id = %s''',
        (current_user.id, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), nota, id)
    )
    db.commit()
    cur.close()

    flash('TCC rejeitado.', 'sucesso')
    return redirect(url_for('aprovacoes.historico'))
