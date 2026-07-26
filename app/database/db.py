# IMETRO TFC v3 — Camada de Base de Dados (PostgreSQL)

import os
import json
import psycopg2
import psycopg2.extras
from datetime import datetime
from flask import g


def get_db_config():
    """Obtém configuração da BD de variáveis de ambiente ou DATABASE_URL."""
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        return database_url
    return {
        'host': os.getenv('PGHOST', 'localhost'),
        'user': os.getenv('PGUSER', 'postgres'),
        'password': os.getenv('PGPASSWORD', ''),
        'dbname': os.getenv('PGDATABASE', 'plagio'),
        'port': os.getenv('PGPORT', '5432'),
    }


def init_db(db_path=None) -> None:
    """PostgreSQL: aplicar migrações pendentes."""
    try:
        config = get_db_config()
        if isinstance(config, str):
            conn = psycopg2.connect(config)
        else:
            conn = psycopg2.connect(**config)
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute("ALTER TABLE fontes_externas_resultados ADD COLUMN IF NOT EXISTS frase_origem TEXT")
        cur.close()
        conn.close()
    except Exception:
        pass


def get_db():
    """Abre/reutiliza conexão PostgreSQL no contexto do pedido."""
    if 'db' not in g:
        config = get_db_config()
        if isinstance(config, str):
            g.db = psycopg2.connect(config)
        else:
            g.db = psycopg2.connect(**config)
        g.db.autocommit = False
    return g.db


def close_db(e=None):
    """Fecha a conexão PostgreSQL no contexto do pedido."""
    db = g.pop('db', None)
    if db is not None:
        db.close()


def _dict_row(cursor, row):
    """Converte tuple para dict usando nomes das colunas."""
    if row is None:
        return None
    cols = [d[0] for d in cursor.description]
    return dict(zip(cols, row))


def _dict_rows(rows, cursor):
    """Converte lista de tuples para lista de dicts."""
    cols = [d[0] for d in cursor.description] if cursor.description else []
    return [dict(zip(cols, r)) for r in rows]


# ════════════════════════════════════════════════
# CURSOS
# ════════════════════════════════════════════════

def inserir_curso(nome, codigo=None, departamento=None, descricao=None, activo=1):
    db = get_db()
    cur = db.cursor()
    cur.execute(
        'INSERT INTO cursos (nome, codigo, departamento, descricao, data_criacao, activo) VALUES (%s,%s,%s,%s,%s,%s) RETURNING id',
        (nome, codigo, departamento, descricao, datetime.now().strftime('%Y-%m-%d %H:%M'), activo))
    result = cur.fetchone()
    db.commit()
    return result[0] if result else None


def editar_curso(id, nome, codigo=None, departamento=None, descricao=None, activo=1):
    db = get_db()
    cur = db.cursor()
    cur.execute('UPDATE cursos SET nome=%s, codigo=%s, departamento=%s, descricao=%s, activo=%s WHERE id=%s',
               (nome, codigo, departamento, descricao, activo, id))
    db.commit()


def listar_cursos_admin():
    db = get_db()
    cur = db.cursor()
    cur.execute('SELECT * FROM cursos ORDER BY nome ASC')
    return _dict_rows(cur.fetchall(), cur)


def buscar_curso(id):
    db = get_db()
    cur = db.cursor()
    cur.execute('SELECT * FROM cursos WHERE id = %s', (id,))
    return _dict_row(cur, cur.fetchone())


def buscar_curso_por_nome(nome):
    db = get_db()
    cur = db.cursor()
    cur.execute('SELECT * FROM cursos WHERE nome = %s', (nome,))
    return _dict_row(cur, cur.fetchone())


def remover_curso(id):
    db = get_db()
    cur = db.cursor()
    cur.execute('SELECT COUNT(*) FROM tcc_validos WHERE curso_id = %s', (id,))
    c1 = cur.fetchone()[0]
    cur.execute('SELECT COUNT(*) FROM tcc_suspeitos WHERE curso_id = %s', (id,))
    c2 = cur.fetchone()[0]
    if c1 > 0 or c2 > 0:
        return False
    cur.execute('DELETE FROM cursos WHERE id = %s', (id,))
    db.commit()
    return True


# ════════════════════════════════════════════════
# ORIENTADORES
# ════════════════════════════════════════════════

def inserir_orientador(nome, email=None, titulacao=None, curso_id=None):
    db = get_db()
    cur = db.cursor()
    cur.execute('INSERT INTO orientadores (nome, email, titulacao, curso_id) VALUES (%s,%s,%s,%s) RETURNING id',
                (nome, email, titulacao, curso_id))
    result = cur.fetchone()
    db.commit()
    return result[0] if result else None


def editar_orientador(id, nome, email=None, titulacao=None, curso_id=None):
    db = get_db()
    cur = db.cursor()
    cur.execute('UPDATE orientadores SET nome=%s, email=%s, titulacao=%s, curso_id=%s WHERE id=%s',
               (nome, email, titulacao, curso_id, id))
    db.commit()


def listar_orientadores():
    db = get_db()
    cur = db.cursor()
    cur.execute('''SELECT o.*, c.nome as curso_nome
        FROM orientadores o LEFT JOIN cursos c ON o.curso_id = c.id
        ORDER BY o.nome ASC''')
    return _dict_rows(cur.fetchall(), cur)


def buscar_orientador(id):
    db = get_db()
    cur = db.cursor()
    cur.execute('''SELECT o.*, c.nome as curso_nome
        FROM orientadores o LEFT JOIN cursos c ON o.curso_id = c.id
        WHERE o.id = %s''', (id,))
    return _dict_row(cur, cur.fetchone())


def remover_orientador(id):
    db = get_db()
    cur = db.cursor()
    cur.execute('DELETE FROM orientadores WHERE id = %s', (id,))
    db.commit()


# ════════════════════════════════════════════════
# TCC VALIDOS
# ════════════════════════════════════════════════

def inserir_tcc_valido(titulo, autor, curso_id, curso_nome='', orientador_id=None,
                       orientador_nome='', ano_defesa=None, semestre='',
                       palavras_chave='', resumo='', nota_final=None,
                       num_chunks=0, caminho='', chroma_id='',
                       score_abnt=0, abnt_flags=None):
    db = get_db()
    cur = db.cursor()
    flags = abnt_flags or {}
    cur.execute('''INSERT INTO tcc_validos
        (titulo, autor, orientador_id, orientador_nome, curso_id, curso_nome,
         ano_defesa, semestre, palavras_chave, resumo, nota_final,
         data_indexacao, num_chunks, caminho_ficheiro, chroma_id,
         tem_capa, tem_folha_rosto, tem_resumo, tem_abstract, tem_sumario, tem_referencias, score_abnt)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id''',
        (titulo, autor, orientador_id, orientador_nome, curso_id, curso_nome,
         ano_defesa, semestre, palavras_chave, resumo, nota_final,
         datetime.now().strftime('%Y-%m-%d %H:%M'), num_chunks, caminho, chroma_id,
         flags.get('capa', 0), flags.get('folha_rosto', 0), flags.get('resumo', 0),
         flags.get('abstract', 0), flags.get('sumario', 0), flags.get('referencias', 0), score_abnt))
    result = cur.fetchone()
    db.commit()
    return result[0] if result else None


def listar_tcc_validos(curso_id=None, ano=None, pesquisa=None, pagina=1, por_pagina=20):
    db = get_db()
    cur = db.cursor()
    where, params = [], []
    if curso_id:
        where.append('t.curso_id = %s'); params.append(curso_id)
    if ano:
        where.append('t.ano_defesa = %s'); params.append(ano)
    if pesquisa:
        where.append("(t.titulo ILIKE %s OR t.autor ILIKE %s)"); params.extend([f'%{pesquisa}%'] * 2)
    clause = ('WHERE ' + ' AND '.join(where)) if where else ''
    cur.execute(f'SELECT COUNT(*) as cnt FROM tcc_validos t {clause}', params)
    total = cur.fetchone()[0]
    offset = (pagina - 1) * por_pagina
    cur.execute(f'''SELECT t.* FROM tcc_validos t {clause}
        ORDER BY t.data_indexacao DESC LIMIT %s OFFSET %s''', params + [por_pagina, offset])
    rows = _dict_rows(cur.fetchall(), cur)
    return rows, total


def buscar_tcc_valido(id):
    db = get_db()
    cur = db.cursor()
    cur.execute('SELECT * FROM tcc_validos WHERE id = %s', (id,))
    return _dict_row(cur, cur.fetchone())


def buscar_tcc_valido_por_chroma(chroma_id):
    db = get_db()
    cur = db.cursor()
    cur.execute('SELECT * FROM tcc_validos WHERE chroma_id = %s', (chroma_id,))
    return _dict_row(cur, cur.fetchone())


def remover_tcc_valido(id):
    db = get_db()
    cur = db.cursor()
    cur.execute('UPDATE matches SET tcc_valido_id = NULL WHERE tcc_valido_id = %s', (id,))
    cur.execute('DELETE FROM tcc_validos WHERE id = %s', (id,))
    db.commit()


def contar_tcc_validos():
    db = get_db()
    cur = db.cursor()
    cur.execute('SELECT COUNT(*) FROM tcc_validos')
    return cur.fetchone()[0]


def editar_tcc_valido(id, **kwargs):
    db = get_db()
    cur = db.cursor()
    sets = ', '.join(f'{k}=%s' for k in kwargs)
    cur.execute(f'UPDATE tcc_validos SET {sets} WHERE id=%s', list(kwargs.values()) + [id])
    db.commit()


# ════════════════════════════════════════════════
# TCC SUSPEITOS
# ════════════════════════════════════════════════

def inserir_tcc_suspeito(autor, caminho_ficheiro, titulo='', orientador_id=None,
                         orientador_nome='', curso_id=None, curso_nome='', ano_submissao=None,
                         submetido_por=None):
    db = get_db()
    cur = db.cursor()
    cur.execute('''INSERT INTO tcc_suspeitos
        (titulo, autor, orientador_id, orientador_nome, curso_id, curso_nome,
         ano_submissao, data_submissao, caminho_ficheiro, submetido_por)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id''',
        (titulo, autor, orientador_id, orientador_nome, curso_id, curso_nome,
         ano_submissao, datetime.now().strftime('%Y-%m-%d %H:%M'), caminho_ficheiro, submetido_por))
    result = cur.fetchone()
    db.commit()
    return result[0] if result else None


def listar_tcc_suspeitos(curso_id=None, estado=None, pesquisa=None, pagina=1, por_pagina=20):
    db = get_db()
    cur = db.cursor()
    where, params = [], []
    if curso_id:
        where.append('curso_id = %s'); params.append(curso_id)
    if estado:
        where.append('estado = %s'); params.append(estado)
    if pesquisa:
        where.append("(titulo ILIKE %s OR autor ILIKE %s)"); params.extend([f'%{pesquisa}%'] * 2)
    clause = ('WHERE ' + ' AND '.join(where)) if where else ''
    cur.execute(f'SELECT COUNT(*) as cnt FROM tcc_suspeitos {clause}', params)
    total = cur.fetchone()[0]
    offset = (pagina - 1) * por_pagina
    cur.execute(f'''SELECT * FROM tcc_suspeitos {clause}
        ORDER BY data_submissao DESC LIMIT %s OFFSET %s''', params + [por_pagina, offset])
    rows = _dict_rows(cur.fetchall(), cur)
    return rows, total


def listar_tcc_suspeitos_por_utilizador(utilizador_id):
    db = get_db()
    cur = db.cursor()
    cur.execute('''SELECT * FROM tcc_suspeitos WHERE submetido_por = %s
        ORDER BY data_submissao DESC''', (utilizador_id,))
    rows = _dict_rows(cur.fetchall(), cur)
    cur.close()
    return rows


def buscar_tcc_suspeito(id):
    db = get_db()
    cur = db.cursor()
    cur.execute('SELECT * FROM tcc_suspeitos WHERE id = %s', (id,))
    return _dict_row(cur, cur.fetchone())


def actualizar_estado_suspeito(id, estado):
    db = get_db()
    cur = db.cursor()
    cur.execute('UPDATE tcc_suspeitos SET estado = %s WHERE id = %s', (estado, id))
    db.commit()


def actualizar_resultado_suspeito(id, verificacao_id, pct, nivel):
    db = get_db()
    cur = db.cursor()
    cur.execute('''UPDATE tcc_suspeitos SET ultima_verificacao_id=%s, ultima_pct_plagio=%s,
        ultimo_nivel=%s, estado='verificado' WHERE id=%s''', (verificacao_id, pct, nivel, id))
    db.commit()


def remover_tcc_suspeito(id):
    db = get_db()
    cur = db.cursor()

    cur.execute('SELECT id FROM verificacoes WHERE tcc_suspeito_id = %s', (id,))
    verif_ids = [r[0] for r in cur.fetchall()]

    if verif_ids:
        placeholders = ','.join(['%s'] * len(verif_ids))
        cur.execute(f'DELETE FROM analises_ia WHERE verificacao_id IN ({placeholders})', verif_ids)
        cur.execute(f'DELETE FROM chunks_suspeitos WHERE verificacao_id IN ({placeholders})', verif_ids)
        cur.execute(f'DELETE FROM fontes_externas_resultados WHERE verificacao_id IN ({placeholders})', verif_ids)
        cur.execute(f'DELETE FROM fontes_externas WHERE verificacao_id IN ({placeholders})', verif_ids)
        cur.execute(f'DELETE FROM matches WHERE verificacao_id IN ({placeholders})', verif_ids)
        cur.execute(f'DELETE FROM verificacoes_normas_infracoes WHERE normas_id IN (SELECT id FROM verificacoes_normas WHERE verificacao_id IN ({placeholders}))', verif_ids)
        cur.execute(f'DELETE FROM verificacoes_normas WHERE verificacao_id IN ({placeholders})', verif_ids)
        cur.execute(f'DELETE FROM veredictos_finais WHERE verificacao_id IN ({placeholders})', verif_ids)
        cur.execute(f'DELETE FROM verificacoes WHERE tcc_suspeito_id = %s', (id,))

    cur.execute('DELETE FROM tcc_suspeitos WHERE id = %s', (id,))
    db.commit()


def contar_tcc_suspeitos(estado=None):
    db = get_db()
    cur = db.cursor()
    if estado:
        cur.execute('SELECT COUNT(*) FROM tcc_suspeitos WHERE estado=%s', (estado,))
    else:
        cur.execute('SELECT COUNT(*) FROM tcc_suspeitos')
    return cur.fetchone()[0]


def contar_pendentes_normas():
    try:
        db = get_db()
        cur = db.cursor()
        cur.execute('''
            SELECT COUNT(*) FROM tcc_suspeitos s
            JOIN verificacoes_normas vn ON vn.verificacao_id = s.ultima_verificacao_id
            WHERE s.estado = 'verificado' AND vn.requer_correcao = 1
        ''')
        return cur.fetchone()[0]
    except:
        return 0


def editar_tcc_suspeito(id, **kwargs):
    db = get_db()
    cur = db.cursor()
    sets = ', '.join(f'{k}=%s' for k in kwargs)
    cur.execute(f'UPDATE tcc_suspeitos SET {sets} WHERE id=%s', list(kwargs.values()) + [id])
    db.commit()


# ════════════════════════════════════════════════
# VERIFICACOES
# ════════════════════════════════════════════════

def inserir_verificacao(tcc_suspeito_id, curso_id_filtro=None, curso_nome_filtro='',
                       limiar_usado=0.85, pct=0.0, nivel='Baixo',
                       num_total=0, num_suspeitos=0, duracao=0.0,
                       caminho_rel='', score_abnt=0, score_apa=0, observacoes=''):
    db = get_db()
    cur = db.cursor()
    cur.execute('''INSERT INTO verificacoes
        (tcc_suspeito_id, curso_id_filtro, curso_nome_filtro, limiar_usado,
         percentagem_plagio, nivel, num_chunks_total, num_chunks_suspeitos,
         data, duracao_segundos, caminho_relatorio, score_abnt, score_apa, observacoes)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id''',
        (tcc_suspeito_id, curso_id_filtro, curso_nome_filtro, limiar_usado,
         pct, nivel, num_total, num_suspeitos,
         datetime.now().strftime('%Y-%m-%d %H:%M'), duracao, caminho_rel, score_abnt, score_apa, observacoes))
    result = cur.fetchone()
    db.commit()
    return result[0] if result else None


def listar_verificacoes(limite=10):
    db = get_db()
    cur = db.cursor()
    cur.execute('''SELECT v.*, s.titulo as tcc_titulo, s.autor as tcc_autor,
        s.curso_nome as tcc_curso, s.estado as suspeito_estado, vn.classificacao_final as normas_classificacao
        FROM verificacoes v
        LEFT JOIN tcc_suspeitos s ON v.tcc_suspeito_id = s.id
        LEFT JOIN verificacoes_normas vn ON vn.verificacao_id = v.id
        ORDER BY v.data DESC LIMIT %s''', (limite,))
    return _dict_rows(cur.fetchall(), cur)


def listar_verificacoes_filtro(curso_id=None, nivel=None, data_de=None, data_ate=None,
                               pagina=1, por_pagina=20):
    db = get_db()
    cur = db.cursor()
    where, params = [], []
    if curso_id:
        where.append('v.curso_id_filtro = %s'); params.append(curso_id)
    if nivel:
        where.append('v.nivel = %s'); params.append(nivel)
    if data_de:
        where.append('v.data >= %s'); params.append(data_de)
    if data_ate:
        where.append('v.data <= %s'); params.append(data_ate)
    clause = ('WHERE ' + ' AND '.join(where)) if where else ''
    cur.execute(f'SELECT COUNT(*) as cnt FROM verificacoes v {clause}', params)
    total = cur.fetchone()[0]
    offset = (pagina - 1) * por_pagina
    cur.execute(f'''SELECT v.*, s.titulo as tcc_titulo, s.autor as tcc_autor,
        s.curso_nome as tcc_curso, s.estado as suspeito_estado, vn.classificacao_final as normas_classificacao
        FROM verificacoes v
        LEFT JOIN tcc_suspeitos s ON v.tcc_suspeito_id = s.id
        LEFT JOIN verificacoes_normas vn ON vn.verificacao_id = v.id
        {clause} ORDER BY v.data DESC LIMIT %s OFFSET %s''',
        params + [por_pagina, offset])
    rows = _dict_rows(cur.fetchall(), cur)
    return rows, total


def buscar_verificacao(id):
    db = get_db()
    cur = db.cursor()
    cur.execute('''SELECT v.*, s.titulo as tcc_titulo, s.autor as tcc_autor,
        s.curso_nome as tcc_curso, s.caminho_ficheiro as tcc_caminho
        FROM verificacoes v LEFT JOIN tcc_suspeitos s ON v.tcc_suspeito_id = s.id
        WHERE v.id = %s''', (id,))
    return _dict_row(cur, cur.fetchone())


def contar_verificacoes():
    db = get_db()
    cur = db.cursor()
    cur.execute('SELECT COUNT(*) FROM verificacoes')
    return cur.fetchone()[0]


def media_percentagem():
    db = get_db()
    cur = db.cursor()
    cur.execute('SELECT AVG(percentagem_plagio) FROM verificacoes')
    r = cur.fetchone()
    return round(r[0], 1) if r and r[0] else 0.0


def contar_por_nivel():
    db = get_db()
    cur = db.cursor()
    cur.execute('SELECT nivel, COUNT(*) as total FROM verificacoes GROUP BY nivel')
    rows = cur.fetchall()
    res = {"Baixo": 0, "Moderado": 0, "Alto": 0, "Critico": 0}
    for r in rows:
        if r[0] in res:
            res[r[0]] = r[1]
    return res


def verificacoes_por_mes():
    db = get_db()
    cur = db.cursor()
    cur.execute('''SELECT TO_CHAR(data::date, 'YYYY-MM') as mes, COUNT(*) as total
        FROM verificacoes GROUP BY mes ORDER BY mes DESC LIMIT 6''')
    rows = cur.fetchall()
    return {r[0]: r[1] for r in reversed(rows)}


def verificacoes_por_mes_aprov_reprov():
    db = get_db()
    cur = db.cursor()
    cur.execute('''
        SELECT TO_CHAR(data::date, 'YYYY-MM') as mes,
                SUM(CASE WHEN nivel = 'Baixo' THEN 1 ELSE 0 END) as aprovados,
                SUM(CASE WHEN nivel IN ('Moderado','Alto','Critico') THEN 1 ELSE 0 END) as reprovados
        FROM verificacoes GROUP BY mes ORDER BY mes
    ''')
    return _dict_rows(cur.fetchall(), cur)


def verificacoes_do_suspeito(tcc_suspeito_id):
    db = get_db()
    cur = db.cursor()
    cur.execute('''SELECT * FROM verificacoes
        WHERE tcc_suspeito_id = %s ORDER BY data DESC''', (tcc_suspeito_id,))
    return _dict_rows(cur.fetchall(), cur)


def remover_verificacao(id):
    db = get_db()
    cur = db.cursor()
    cur.execute('DELETE FROM verificacoes WHERE id = %s', (id,))
    db.commit()


# ════════════════════════════════════════════════
# MATCHES
# ════════════════════════════════════════════════

def inserir_match(verificacao_id, tcc_valido_id=None, tcc_valido_titulo='',
                 tcc_valido_autor='', num_chunks_comuns=0,
                 similaridade_max=0.0, similaridade_media=0.0, contribuicao_pct=0.0,
                 fonte_tipo='interno', fonte_externa_id=None,
                 fonte_origem='desconhecida', titulo_fonte=None, url_fonte=None,
                 trecho_similar=None, trecho_original=None):
    db = get_db()
    cur = db.cursor()
    cur.execute('''INSERT INTO matches
        (verificacao_id, tcc_valido_id, tcc_valido_titulo, tcc_valido_autor,
         num_chunks_comuns, similaridade_max, similaridade_media, contribuicao_pct,
         fonte_tipo, fonte_externa_id, fonte_origem, titulo_fonte, url_fonte,
         trecho_similar, trecho_original)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id''',
        (verificacao_id, tcc_valido_id, tcc_valido_titulo, tcc_valido_autor,
         num_chunks_comuns, similaridade_max, similaridade_media, contribuicao_pct,
         fonte_tipo, fonte_externa_id, fonte_origem, titulo_fonte, url_fonte,
         trecho_similar, trecho_original))
    result = cur.fetchone()
    db.commit()
    return result[0] if result else None


def listar_matches(verificacao_id):
    db = get_db()
    cur = db.cursor()
    cur.execute('''SELECT * FROM matches
        WHERE verificacao_id = %s ORDER BY contribuicao_pct DESC''', (verificacao_id,))
    return _dict_rows(cur.fetchall(), cur)


# ════════════════════════════════════════════════
# CHUNKS SUSPEITOS
# ════════════════════════════════════════════════

def inserir_chunk_suspeito(verificacao_id, match_id=None, posicao=0,
                          texto_suspeito='', texto_origem='',
                          similaridade=0.0, secao=''):
    db = get_db()
    cur = db.cursor()
    cur.execute('''INSERT INTO chunks_suspeitos
        (verificacao_id, match_id, posicao_chunk, texto_suspeito, texto_origem,
         similaridade, secao_estimada) VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING id''',
        (verificacao_id, match_id, posicao, texto_suspeito, texto_origem, similaridade, secao))
    result = cur.fetchone()
    db.commit()
    return result[0] if result else None


def listar_chunks_suspeitos(verificacao_id):
    db = get_db()
    cur = db.cursor()
    cur.execute('''SELECT cs.*, m.tcc_valido_titulo, m.tcc_valido_autor,
        ia.plagio as ia_plagio, ia.nivel as ia_nivel, ia.tipo as ia_tipo,
        ia.similaridade_llm as ia_sim_llm, ia.justificativa as ia_justificativa,
        ia.modelo_usado as ia_modelo
        FROM chunks_suspeitos cs
        LEFT JOIN matches m ON cs.match_id = m.id
        LEFT JOIN analises_ia ia ON ia.chunk_id = cs.id
        WHERE cs.verificacao_id = %s ORDER BY cs.similaridade DESC''',
        (verificacao_id,))
    return _dict_rows(cur.fetchall(), cur)


# ════════════════════════════════════════════════
# DASHBOARD STATS
# ════════════════════════════════════════════════

def distribuicao_por_curso():
    db = get_db()
    cur = db.cursor()
    cur.execute('''SELECT c.nome, COUNT(t.id) as total
        FROM cursos c LEFT JOIN tcc_validos t ON c.id = t.curso_id
        WHERE c.activo = 1 GROUP BY c.id ORDER BY total DESC LIMIT 8''')
    return {r[0]: r[1] for r in cur.fetchall()}


def distribuicao_abnt():
    db = get_db()
    cur = db.cursor()
    ranges = {}
    for label, lo, hi in [('0-20',0,20),('20-40',20,40),('40-60',40,60),('60-80',60,80),('80-100',80,101)]:
        cur.execute('SELECT COUNT(*) FROM tcc_validos WHERE score_abnt >= %s AND score_abnt < %s', (lo, hi))
        ranges[label] = cur.fetchone()[0]
    return ranges


def suspeitos_por_estado():
    db = get_db()
    cur = db.cursor()
    cur.execute('SELECT estado, COUNT(*) as total FROM tcc_suspeitos GROUP BY estado')
    return {r[0]: r[1] for r in cur.fetchall()}


def evolucao_media_plagio():
    db = get_db()
    cur = db.cursor()
    cur.execute('''SELECT TO_CHAR(data::date, 'YYYY-MM') as mes,
        AVG(percentagem_plagio) as media FROM verificacoes
        GROUP BY mes ORDER BY mes DESC LIMIT 6''')
    rows = cur.fetchall()
    return {r[0]: round(r[1], 1) for r in reversed(rows)}


def contar_plagio_alto():
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT COUNT(*) FROM verificacoes WHERE nivel IN ('Alto','Critico')")
    return cur.fetchone()[0]


def contar_sem_abnt():
    db = get_db()
    cur = db.cursor()
    cur.execute('SELECT COUNT(*) FROM tcc_validos WHERE score_abnt < 50')
    return cur.fetchone()[0]


# ─────────────────────────────────────────────
# VEREDICTOS FINAIS
# ─────────────────────────────────────────────

def guardar_veredicto_final(verificacao_id, dados):
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        INSERT INTO veredictos_finais
            (verificacao_id, score_global, classificacao,
             tipo_predominante, gravidade, conclusao_ia,
             modelo_ia_usado, chunks_analisados, gerado_por_ia, data_geracao)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
        ON CONFLICT (verificacao_id) DO UPDATE SET
            score_global = EXCLUDED.score_global,
            classificacao = EXCLUDED.classificacao,
            tipo_predominante = EXCLUDED.tipo_predominante,
            gravidade = EXCLUDED.gravidade,
            conclusao_ia = EXCLUDED.conclusao_ia,
            modelo_ia_usado = EXCLUDED.modelo_ia_usado,
            chunks_analisados = EXCLUDED.chunks_analisados,
            gerado_por_ia = EXCLUDED.gerado_por_ia,
            data_geracao = NOW()
    """, (
        verificacao_id,
        dados.get('score_global', 0),
        dados.get('classificacao', 'Sem plagio'),
        dados.get('tipo_predominante'),
        dados.get('gravidade'),
        dados.get('conclusao_ia'),
        dados.get('modelo_ia_usado'),
        dados.get('chunks_analisados', 0),
        dados.get('gerado_por_ia', 0),
    ))
    db.commit()
    return verificacao_id


def obter_veredicto_final(verificacao_id):
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM veredictos_finais WHERE verificacao_id = %s", (verificacao_id,))
    return _dict_row(cur, cur.fetchone())


def obter_dados_relatorio_completo(verificacao_id):
    db = get_db()
    cur = db.cursor()

    cur.execute("""
        SELECT v.*, ts.titulo, ts.autor, ts.ano_submissao as ano,
               ts.caminho_ficheiro, ts.estado,
               c.nome AS curso_nome, c.departamento,
               o.nome AS orientador_nome,
               u.nome AS aprovado_por_nome
        FROM verificacoes v
        JOIN tcc_suspeitos ts ON ts.id = v.tcc_suspeito_id
        LEFT JOIN cursos c ON c.id = ts.curso_id
        LEFT JOIN orientadores o ON o.id = ts.orientador_id
        LEFT JOIN utilizadores u ON u.id = ts.aprovado_por
        WHERE v.id = %s
    """, (verificacao_id,))
    verificacao = _dict_row(cur, cur.fetchone())

    if not verificacao:
        return None

    cur.execute("""
        SELECT m.*, tv.titulo AS titulo_fonte, tv.autor AS autor_fonte,
               tv.ano_defesa AS ano_fonte
        FROM matches m
        LEFT JOIN tcc_validos tv ON tv.id = m.tcc_valido_id
        WHERE m.verificacao_id = %s
        ORDER BY m.similaridade_max DESC LIMIT 10
    """, (verificacao_id,))
    matches = _dict_rows(cur.fetchall(), cur)

    cur.execute("""
        SELECT cs.id, cs.texto_suspeito, cs.texto_origem as texto_original,
               cs.similaridade as score,
               ai.plagio as ia_veredicto,
               ai.tipo as ia_tipo,
               ai.nivel as ia_gravidade,
               ai.justificativa as ia_justificativa,
               tv.titulo AS fonte_titulo,
               tv.autor AS fonte_autor
        FROM chunks_suspeitos cs
        LEFT JOIN analises_ia ai ON ai.chunk_id = cs.id
        LEFT JOIN matches m ON m.id = cs.match_id
        LEFT JOIN tcc_validos tv ON tv.id = m.tcc_valido_id
        WHERE cs.verificacao_id = %s
        ORDER BY cs.similaridade DESC LIMIT 50
    """, (verificacao_id,))
    chunks = _dict_rows(cur.fetchall(), cur)

    cur.execute("SELECT * FROM veredictos_finais WHERE verificacao_id = %s", (verificacao_id,))
    veredicto = _dict_row(cur, cur.fetchone())

    return {
        'verificacao':  verificacao,
        'matches':      matches,
        'chunks':       chunks,
        'veredicto':    veredicto,
        'referencia':   f"VRF-{verificacao_id:04d}-{verificacao.get('ano', '2024')}",
    }


# ════════════════════════════════════════════════
# EMBEDDINGS CHUNKS
# ════════════════════════════════════════════════

def guardar_embedding_chunk(tcc_id, tipo, chunk_texto, vector):
    try:
        db = get_db()
    except RuntimeError:
        config = get_db_config()
        if isinstance(config, str):
            db = psycopg2.connect(config)
        else:
            db = psycopg2.connect(**config)
    cur = db.cursor()
    vector_json = json.dumps(vector)
    cur.execute(
        'INSERT INTO embeddings_chunks (tcc_id, tipo, chunk_texto, vector) VALUES (%s, %s, %s, %s)',
        (tcc_id, tipo, chunk_texto, vector_json))
    db.commit()
    cur.close()


def listar_embeddings_por_tipo(tipo):
    try:
        db = get_db()
    except RuntimeError:
        config = get_db_config()
        if isinstance(config, str):
            db = psycopg2.connect(config)
        else:
            db = psycopg2.connect(**config)
    cur = db.cursor()
    cur.execute('SELECT tcc_id, chunk_texto, vector FROM embeddings_chunks WHERE tipo = %s', (tipo,))
    results = []
    for row in cur.fetchall():
        vec = row[2]
        if isinstance(vec, str):
            vec = json.loads(vec)
        results.append({
            'tcc_id': row[0],
            'chunk_texto': row[1],
            'vector': vec
        })
    cur.close()
    return results


# ════════════════════════════════════════════════
# UTILIZADORES (já existia via Flask-Login)
# ════════════════════════════════════════════════

def listar_utilizadores():
    db = get_db()
    cur = db.cursor()
    cur.execute('SELECT * FROM utilizadores ORDER BY nome')
    return _dict_rows(cur.fetchall(), cur)


def contar_utilizadores():
    db = get_db()
    cur = db.cursor()
    cur.execute('SELECT COUNT(*) FROM utilizadores')
    return cur.fetchone()[0]
