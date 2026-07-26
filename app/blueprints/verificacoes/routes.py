# IMETRO TFC v3 — Rotas de Verificações (fluxo completo)
import os
import uuid
import time
import threading
import json
from flask import (render_template, request, redirect, url_for, flash,
                   current_app, send_file, jsonify)
from werkzeug.utils import secure_filename
from app.blueprints.verificacoes import verificacoes_bp
import numpy as np
from app.extensions import jobs
from app.services import plagio_service
from app.database import db
from core.auth_helpers import requer_verificador, requer_admin
from core.embeddings import gerar_embeddings_lote, gerar_embedding, EmbeddingServiceError
from core.detector import cosine_similarity
from app.database.db import listar_embeddings_por_tipo


class _EmbeddingAdapter:
    """Adaptador que expoe .encode() e .encode_batch() usando OpenRouter API."""
    def encode(self, text):
        return np.array(gerar_embedding(text))
    
    def encode_batch(self, texts):
        if not texts:
            return []
        embeddings = gerar_embeddings_lote(texts)
        return [np.array(e) for e in embeddings]


@verificacoes_bp.route('/')
@requer_verificador
def nova():
    """Formulário de nova verificação (3 passos)."""
    suspeitos, _ = db.listar_tcc_suspeitos(pagina=1, por_pagina=200)
    cursos = db.listar_cursos_admin()
    limiar = current_app.config.get('LIMIAR_PLAGIO', 0.85)
    opcoes_normas = {
        "normas_imetro_local": True,
        "normas_imetro_ia": False,
        "ia_disponivel": bool(current_app.config.get("LLM_ENABLED", "false").lower() == "true")
    }
    return render_template('verificacoes/nova.html',
                           suspeitos=suspeitos, cursos=cursos, limiar_default=limiar,
                           opcoes_normas=opcoes_normas)


@verificacoes_bp.route('/iniciar', methods=['POST'])
@requer_verificador
def iniciar():
    """Inicia uma verificação de plágio."""
    tcc_id = request.form.get('tcc_suspeito_id', type=int)
    curso_filtro_id = request.form.get('curso_filtro_id', type=int)
    limiar = request.form.get('limiar', type=float) or current_app.config.get('LIMIAR_PLAGIO', 0.85)
    verificar_abnt = request.form.get('verificar_abnt', '1') == '1'
    pesquisa_externa_ativa = request.form.get('pesquisa_externa_ativa', '0') == '1'
    
    normas_incluir = request.form.get('normas_incluir', 'on') == 'on'
    normas_ia_incluir = request.form.get('normas_ia', 'off') == 'on'
    
    if normas_ia_incluir and current_app.config.get("LLM_ENABLED", "false").lower() != "true":
        normas_ia_incluir = False

    if not tcc_id:
        flash('Seleccione um TCC suspeito.', 'erro')
        return redirect(url_for('verificacoes.nova'))

    tcc = db.buscar_tcc_suspeito(tcc_id)
    if not tcc:
        flash('TCC suspeito não encontrado.', 'erro')
        return redirect(url_for('verificacoes.nova'))

    curso_nome = ''
    if curso_filtro_id:
        c = db.buscar_curso(curso_filtro_id)
        curso_nome = c['nome'] if c else ''

    job_id = uuid.uuid4().hex[:12]
    jobs[job_id] = {
        'status': 'em_progresso', 'etapa': 'extraindo', 'progresso': 0,
        'total': 100, 'tcc_titulo': tcc['titulo'] or 'Sem título',
        'verificacao_id': None, 'erro': None
    }

    db.actualizar_estado_suspeito(tcc_id, 'em_verificacao')

    app_ref = current_app._get_current_object()

    def executar(app_r, job_r, tcc_r, curso_filtro_r, curso_nome_r, limiar_r, abnt_r, externa_ativa_r, n_incluir, n_ia_incluir):
        with app_r.app_context():
            try:
                inicio = time.time()

                jobs[job_r]['etapa'] = 'extraindo'
                jobs[job_r]['progresso'] = 10
                from core.ingestor import extrair, limpar_texto
                from core.chunker import dividir_em_chunks

                texto_bruto = extrair(tcc_r['caminho_ficheiro'])
                texto_limpo = limpar_texto(texto_bruto)

                jobs[job_r]['etapa'] = 'chunking'
                jobs[job_r]['progresso'] = 20
                tamanho = app_r.config.get('CHUNK_SIZE', 200)
                overlap = app_r.config.get('CHUNK_OVERLAP', 50)
                chunks = dividir_em_chunks(texto_limpo, tamanho=tamanho, overlap=overlap)
                total_chunks = len(chunks)

                resultados_externos = []
                chunks_suspeitos = 0
                
                if externa_ativa_r:
                    jobs[job_r]['etapa'] = 'pesquisa_externa'
                    jobs[job_r]['progresso'] = 30
                    from core.pesquisa_externa import pesquisar_texto_completo
                    
                    config_externa = {
                        "email_cortesia": app_r.config.get("EMAIL_CORTESIA", ""),
                        "semantic_scholar_key": app_r.config.get("SEMANTIC_SCHOLAR_KEY", ""),
                        "core_key": app_r.config.get("CORE_KEY", ""),
                        "serper_api_key": os.getenv("SERPER_API_KEY", ""),
                        "serper_api_url": os.getenv("SERPER_API_URL", "https://google.serper.dev/search"),
                        "serper_timeout": os.getenv("SERPER_TIMEOUT_SECONDS", 15),
                        "serper_max_retries": os.getenv("SERPER_MAX_RETRIES", 2),
                    }
                    
                    for idx_c, chunk_texto in enumerate(chunks):
                        resultado = pesquisar_texto_completo(
                            texto=chunk_texto,
                            modelo_embeddings=_EmbeddingAdapter(),
                            config=config_externa,
                            limiar_alerta=limiar_r
                        )
                        if resultado.get("sucesso") and resultado.get("suspeitos"):
                            for suspeito in resultado["suspeitos"]:
                                suspeito["chunk_index"] = idx_c
                                suspeito["chunk_texto"] = chunk_texto
                                resultados_externos.append(suspeito)

                jobs[job_r]['etapa'] = 'embeddings'
                BATCH = 16
                detalhes = []

                validos = listar_embeddings_por_tipo('valido')
                vetores_validos = [item['vector'] for item in validos]
                textos_validos = [item['chunk_texto'] for item in validos]
                tcc_ids_validos = [item['tcc_id'] for item in validos]

                for i in range(0, total_chunks, BATCH):
                    lote = chunks[i:i + BATCH]

                    try:
                        emb_lote = gerar_embeddings_lote(lote)
                    except EmbeddingServiceError as e:
                        print(f"[ERRO] Falha ao gerar embeddings para lote: {e}")
                        continue

                    for j in range(len(lote)):
                        embedding_suspeito = emb_lote[j]

                        max_sim = 0.0
                        melhor_idx = -1
                        for idx, emb_valido in enumerate(vetores_validos):
                            simil = cosine_similarity(embedding_suspeito, emb_valido)
                            if simil > max_sim:
                                max_sim = simil
                                melhor_idx = idx

                        if max_sim >= limiar_r and melhor_idx != -1:
                            chunks_suspeitos += 1
                            from core.abnt_checker import estimar_secao
                            detalhes.append({
                                'chunk_texto': lote[j], 'texto_similar': textos_validos[melhor_idx],
                                'similaridade': round(max_sim, 4),
                                'titulo_origem': f'TCC ID {tcc_ids_validos[melhor_idx]}',
                                'autor_origem': 'Desconhecido',
                                'curso_origem': 'Desconhecido',
                                'chroma_id_origem': str(tcc_ids_validos[melhor_idx]),
                                'posicao': i + j,
                                'secao': estimar_secao(i + j, total_chunks)
                            })

                    pct_prog = 30 + int((i + len(lote)) / total_chunks * 50)
                    jobs[job_r]['progresso'] = min(pct_prog, 80)
                    jobs[job_r]['etapa'] = 'comparando'

                score_abnt = 0
                score_apa = 0
                if abnt_r:
                    jobs[job_r]['etapa'] = 'abnt'
                    jobs[job_r]['progresso'] = 85
                    from core.abnt_checker import verificar_abnt, verificar_apa
                    
                    abnt_result = verificar_abnt(texto_bruto)
                    apa_result = verificar_apa(texto_bruto)
                    
                    score_abnt = abnt_result.get('score', 0)
                    score_apa = apa_result.get('score', 0)

                jobs[job_r]['etapa'] = 'relatorio'
                jobs[job_r]['progresso'] = 90
                pct = round((chunks_suspeitos / total_chunks) * 100, 1) if total_chunks > 0 else 0.0
                nivel = plagio_service.classificar_nivel(pct)
                duracao = round(time.time() - inicio, 1)
                detalhes.sort(key=lambda x: x['similaridade'], reverse=True)

                verif_id = db.inserir_verificacao(
                    tcc_suspeito_id=tcc_r['id'], curso_id_filtro=curso_filtro_r,
                    curso_nome_filtro=curso_nome_r, limiar_usado=limiar_r,
                    pct=pct, nivel=nivel, num_total=total_chunks,
                    num_suspeitos=chunks_suspeitos, duracao=duracao,
                    score_abnt=score_abnt, score_apa=score_apa)
                    
                conn = db.get_db()
                cur = conn.cursor()
                
                cur.execute(
                    "UPDATE verificacoes SET normas_incluidas=%s, normas_ia_incluida=%s WHERE id=%s",
                    (1 if n_incluir else 0, 1 if n_ia_incluir else 0, verif_id)
                )
                conn.commit()
                
                for res in resultados_externos:
                    autores_json = json.dumps(res.get("autores", [])) if res.get("autores") else None
                    cur.execute('''
                        INSERT INTO fontes_externas_resultados 
                        (verificacao_id, chunk_id, fonte, titulo_externo, autores, ano_publicacao, doi, url_fonte, resumo_externo, score_semantico)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ''', (
                        verif_id, None, res.get('fonte'), res.get('titulo'), autores_json,
                        res.get('ano'), res.get('doi'), res.get('url'), res.get('resumo'), res.get('score_semantico')
                    ))
                    fonte_externa_id = cur.lastrowid
                    
                    if res.get('score_semantico') >= limiar_r:
                        chunks_suspeitos += 1
                        match_id = db.inserir_match(
                            verificacao_id=verif_id, tcc_valido_id=None,
                            tcc_valido_titulo=f"[{res['fonte'].upper()}] {res['titulo']}",
                            tcc_valido_autor=autores_json,
                            num_chunks_comuns=1,
                            similaridade_max=res['score_semantico'],
                            similaridade_media=res['score_semantico'],
                            contribuicao_pct=round((1 / total_chunks) * 100, 1) if total_chunks > 0 else 0,
                            fonte_tipo='externo',
                            fonte_externa_id=fonte_externa_id,
                            fonte_origem=res.get('fonte', 'desconhecida'),
                            titulo_fonte=res.get('titulo'),
                            url_fonte=res.get('url'),
                            trecho_similar=res.get('resumo'),
                            trecho_original=res.get('chunk_texto')
                        )
                        posicao_chunk = res.get('chunk_index', 0)
                        chunk_id = db.inserir_chunk_suspeito(
                            verificacao_id=verif_id, match_id=match_id,
                            posicao=posicao_chunk, texto_suspeito=res.get('chunk_texto'),
                            texto_origem=res.get('resumo') or res.get('titulo'),
                            similaridade=res['score_semantico'], secao='externo'
                        )
                        cur.execute("UPDATE fontes_externas_resultados SET chunk_id = %s WHERE id = %s", (chunk_id, fonte_externa_id))
                        
                conn.commit()

                fontes = {}
                for d in detalhes:
                    cid = d.get('chroma_id_origem', '')
                    if not cid:
                        continue
                    if cid not in fontes:
                        tv = db.buscar_tcc_valido_por_chroma(cid)
                        fontes[cid] = {
                            'tcc_valido_id': tv['id'] if tv else None,
                            'titulo': d['titulo_origem'], 'autor': d['autor_origem'],
                            'chunks': 0, 'sims': [], 'detalhes_chunks': []
                        }
                    fontes[cid]['chunks'] += 1
                    fontes[cid]['sims'].append(d['similaridade'])
                    fontes[cid]['detalhes_chunks'].append(d)

                for cid, f in fontes.items():
                    contrib = round((f['chunks'] / total_chunks) * 100, 1) if total_chunks > 0 else 0
                    match_id = db.inserir_match(
                        verificacao_id=verif_id, tcc_valido_id=f['tcc_valido_id'],
                        tcc_valido_titulo=f['titulo'], tcc_valido_autor=f['autor'],
                        num_chunks_comuns=f['chunks'],
                        similaridade_max=max(f['sims']) if f['sims'] else 0,
                        similaridade_media=round(sum(f['sims'])/len(f['sims']), 4) if f['sims'] else 0,
                        contribuicao_pct=contrib)

                    for dc in f['detalhes_chunks']:
                        db.inserir_chunk_suspeito(
                            verificacao_id=verif_id, match_id=match_id,
                            posicao=dc['posicao'], texto_suspeito=dc['chunk_texto'],
                            texto_origem=dc['texto_similar'],
                            similaridade=dc['similaridade'], secao=dc.get('secao', ''))

                conn = db.get_db()
                
                jobs[job_r]['etapa'] = 'analise_ia'
                try:
                    from app.blueprints.analise_ia import _get_config_from_db, _build_analyzer_from_db, _salvar_analises_ia
                    from core.llm_analyzer import ChunkParaAnalise
                    
                    config_ia = _get_config_from_db()
                    if config_ia.get("LLM_ENABLED", "false").lower() == "true":
                        threshold_ia = float(config_ia.get("LLM_SCORE_THRESHOLD", "0.75"))
                        analyzer = _build_analyzer_from_db()
                        if analyzer:
                            cur2 = conn.cursor()
                            cur2.execute(
                                """
                                SELECT cs.id AS chunk_id, cs.texto_suspeito, cs.texto_origem, 
                                       m.tcc_valido_id, m.tcc_valido_titulo, cs.similaridade
                                FROM chunks_suspeitos cs
                                JOIN matches m ON m.id = cs.match_id
                                WHERE cs.verificacao_id = %s AND cs.similaridade >= %s
                                """, (verif_id, threshold_ia))
                                
                            ia_cols = [d[0] for d in cur2.description]
                            rows_ia = [dict(zip(ia_cols, row)) for row in cur2.fetchall()]
                            cur2.close()
                                 
                            if rows_ia:
                                chunks_ia = [
                                    ChunkParaAnalise(
                                        chunk_suspeito_id=r["chunk_id"],
                                        texto_suspeito=r["texto_suspeito"],
                                        texto_original=r["texto_origem"],
                                        tcc_original_id=r["tcc_valido_id"],
                                        tcc_original_titulo=r["tcc_valido_titulo"],
                                        score_labse=float(r["similaridade"])
                                    ) for r in rows_ia
                                ]
                                resultados_ia = analyzer.analisar_verificacao(chunks_ia)
                                _salvar_analises_ia(verif_id, resultados_ia)
                                
                                plagio_confirmados = [r for r in resultados_ia if r.plagio]
                                if plagio_confirmados:
                                    nivel_max = max(["baixo", "moderado", "alto", "critico"].index(r.nivel) for r in plagio_confirmados)
                                    nivel = ["baixo", "moderado", "alto", "critico"][nivel_max]
                                    
                                try:
                                    cur3 = conn.cursor()
                                    cur3.execute("UPDATE verificacoes SET nivel_ia = %s, analise_ia_ok = 1 WHERE id = %s", (nivel, verif_id))
                                    conn.commit()
                                    cur3.close()
                                except:
                                    pass
                except Exception as exc:
                    print("Erro ao executar IA:", exc)

                if n_incluir:
                    try:
                        from core.normas_verificacao_integrada import executar_verificacao_normas
                        
                        config_ia = None
                        if n_ia_incluir:
                            from app.blueprints.analise_ia import _get_config_from_db
                            cfg = _get_config_from_db()
                            config_ia = {
                                "provider": cfg.get("LLM_PROVIDER", "openai"),
                                "api_key": cfg.get("LLM_API_KEY", ""),
                                "model": cfg.get("LLM_MODEL", "gpt-4o-mini"),
                                "ollama_url": cfg.get("OLLAMA_URL", "http://localhost:11434"),
                            }
                            
                        resultado_normas = executar_verificacao_normas(
                            verificacao_id=verif_id,
                            tcc_id=tcc_r['id'],
                            texto_completo=texto_bruto,
                            executar_ia=n_ia_incluir,
                            config_ia=config_ia
                        )
                        
                        if getattr(app_r, 'logger', None):
                            app_r.logger.info(f"Normas concluídas para {verif_id}")
                    except Exception as e:
                        print(f"Erro na verificação de normas (verificacao {verif_id}): {e}")

                from core.relatorio import gerar_html
                html = gerar_html({
                    'percentagem_plagio': pct, 'nivel': nivel,
                    'total_chunks': total_chunks, 'chunks_suspeitos': chunks_suspeitos,
                    'detalhes': detalhes,
                    'score_abnt': score_abnt, 'score_apa': score_apa,
                    'resultado_normas': resultado_normas if 'resultado_normas' in locals() else None
                }, tcc_r['titulo'] or 'Sem título', tcc_r['autor'])
                nome_rel = f'relatorio_{verif_id}.html'
                cam_rel = os.path.join(app_r.config['RELATORIOS_FOLDER'], nome_rel)
                with open(cam_rel, 'w', encoding='utf-8') as f:
                    f.write(html)

                cur4 = conn.cursor()
                cur4.execute('UPDATE verificacoes SET caminho_relatorio=%s WHERE id=%s', (cam_rel, verif_id))
                conn.commit()
                cur4.close()

                db.actualizar_resultado_suspeito(tcc_r['id'], verif_id, pct, nivel)

                jobs[job_r]['progresso'] = 100
                jobs[job_r]['etapa'] = 'concluido'
                jobs[job_r]['status'] = 'concluido'
                jobs[job_r]['verificacao_id'] = verif_id

            except Exception as e:
                jobs[job_r]['status'] = 'erro'
                jobs[job_r]['erro'] = str(e)
                db.actualizar_estado_suspeito(tcc_r['id'], 'pendente')

    thread = threading.Thread(target=executar, daemon=True,
        args=(app_ref, job_id, dict(tcc), curso_filtro_id, curso_nome, limiar, verificar_abnt, pesquisa_externa_ativa, normas_incluir, normas_ia_incluir))
    thread.start()

    return render_template('verificacoes/progresso.html', job_id=job_id,
                           tcc_titulo=tcc['titulo'] or 'Sem título')


@verificacoes_bp.route('/historico')
@requer_verificador
def historico():
    curso_id = request.args.get('curso_id', type=int)
    nivel = request.args.get('nivel', '').strip()
    data_de = request.args.get('data_de', '').strip()
    data_ate = request.args.get('data_ate', '').strip()
    pagina = request.args.get('pagina', 1, type=int)

    verifs, total = db.listar_verificacoes_filtro(
        curso_id=curso_id, nivel=nivel or None,
        data_de=data_de or None, data_ate=data_ate or None, pagina=pagina)
    cursos = db.listar_cursos_admin()
    total_paginas = max(1, (total + 19) // 20)

    stats_nivel = db.contar_por_nivel()

    return render_template('verificacoes/historico.html', verificacoes=verifs,
                           cursos=cursos, total=total, pagina=pagina,
                           total_paginas=total_paginas, stats_nivel=stats_nivel,
                           filtro_curso=curso_id, filtro_nivel=nivel,
                           filtro_data_de=data_de, filtro_data_ate=data_ate)


@verificacoes_bp.route('/<int:id>/resultado')
@requer_verificador
def resultado(id):
    verif = db.buscar_verificacao(id)
    if not verif:
        flash('Verificação não encontrada.', 'erro')
        return redirect(url_for('verificacoes.historico'))

    matches = db.listar_matches(id)
    chunks = db.listar_chunks_suspeitos(id)

    seccoes = {}
    for c in chunks:
        sec = c['secao_estimada'] or 'outro'
        if sec not in seccoes:
            seccoes[sec] = {'total': 0, 'suspeitos': 0}
        seccoes[sec]['suspeitos'] += 1

    conn = db.get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM fontes_externas_resultados WHERE verificacao_id = %s ORDER BY score_semantico DESC", (id,))
    fe_cols = [d[0] for d in cur.description]
    fontes_externas = [dict(zip(fe_cols, row)) for row in cur.fetchall()]
    cur.close()
    
    from core.normas_verificacao_integrada import obter_resultado_normas_por_verificacao
    resultado_normas = obter_resultado_normas_por_verificacao(id)

    from app.blueprints.analise_ia import _get_config_from_db
    llm_config = _get_config_from_db()
    return render_template('verificacoes/resultado.html',
                           verificacao=verif, matches=matches, chunks=chunks, seccoes=seccoes,
                           fontes_externas=fontes_externas, resultado_normas=resultado_normas,
                           llm_config=llm_config)


@verificacoes_bp.route('/<int:id>/observacao', methods=['POST'])
@requer_verificador
def observacao(id):
    obs = request.form.get('observacoes', '').strip()
    conn = db.get_db()
    cur = conn.cursor()
    cur.execute('UPDATE verificacoes SET observacoes=%s WHERE id=%s', (obs, id))
    conn.commit()
    cur.close()
    flash('Observação guardada.', 'sucesso')
    return redirect(url_for('verificacoes.resultado', id=id))


@verificacoes_bp.route('/relatorio/<int:id>')
@requer_verificador
def descarregar(id):
    verif = db.buscar_verificacao(id)
    if verif and verif['caminho_relatorio'] and os.path.exists(verif['caminho_relatorio']):
        return send_file(verif['caminho_relatorio'], as_attachment=True,
                         download_name=f'relatorio_plagio_{id}.html')
    flash('Relatório não encontrado.', 'erro')
    return redirect(url_for('verificacoes.resultado', id=id))


@verificacoes_bp.route('/<int:id>/remover', methods=['POST'])
@requer_verificador
def remover(id):
    db.remover_verificacao(id)
    flash('Verificação removida.', 'sucesso')
    return redirect(url_for('verificacoes.historico'))


@verificacoes_bp.route('/<int:id>/normas-ia', methods=['POST'])
@requer_verificador
def executar_normas_ia(id):
    """Executa a análise de IA de normas para uma verificação existente."""
    verif = db.buscar_verificacao(id)
    if not verif:
        return jsonify({"sucesso": False, "erro": "Verificação não encontrada"}), 404
        
    cfg_llm_enabled = current_app.config.get("LLM_ENABLED", "false").lower() == "true"
    if not cfg_llm_enabled:
        return jsonify({"sucesso": False, "erro": "A IA não está ativa no sistema"}), 400
        
    from core.normas_verificacao_integrada import obter_resultado_normas_por_verificacao, executar_verificacao_normas
    res_normas = obter_resultado_normas_por_verificacao(id)
    
    if res_normas and res_normas.get('ia', {}).get('executada'):
        return jsonify({"sucesso": False, "erro": "A análise por IA já foi executada para este trabalho"}), 409
        
    tcc = db.buscar_tcc_suspeito(verif['tcc_suspeito_id'])
    if not tcc or not tcc['caminho_ficheiro'] or not os.path.exists(tcc['caminho_ficheiro']):
        return jsonify({"sucesso": False, "erro": "Ficheiro do trabalho não encontrado"}), 404
        
    try:
        from core.ingestor import extrair
        texto_bruto = extrair(tcc['caminho_ficheiro'])
        
        from app.blueprints.analise_ia import _get_config_from_db
        cfg = _get_config_from_db()
        config_ia = {
            "provider": cfg.get("LLM_PROVIDER", "openai"),
            "api_key": cfg.get("LLM_API_KEY", ""),
            "model": cfg.get("LLM_MODEL", "gpt-4o-mini"),
            "ollama_url": cfg.get("OLLAMA_URL", "http://localhost:11434"),
        }
        
        resultado = executar_verificacao_normas(
            verificacao_id=id,
            tcc_id=tcc['id'],
            texto_completo=texto_bruto,
            executar_ia=True,
            config_ia=config_ia
        )
        
        conn = db.get_db()
        cur = conn.cursor()
        cur.execute("UPDATE verificacoes SET normas_ia_incluida=1 WHERE id=%s", (id,))
        conn.commit()
        cur.close()
        
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"sucesso": False, "erro": str(e)}), 500


@verificacoes_bp.route('/<int:verificacao_id>/veredicto')
@requer_verificador
def ver_veredicto(verificacao_id):
    from app.database.db import obter_dados_relatorio_completo, obter_veredicto_final
    from core.veredicto_builder import construir_e_guardar_veredicto

    dados = obter_dados_relatorio_completo(verificacao_id)
    if not dados:
        flash('Verificação não encontrada.', 'danger')
        return redirect(url_for('verificacoes.historico'))

    if not dados['veredicto']:
        try:
            construir_e_guardar_veredicto(verificacao_id, usar_llm=True)
            dados = obter_dados_relatorio_completo(verificacao_id)
        except Exception as e:
            current_app.logger.error(f"Erro ao gerar veredicto: {e}")
            flash('Erro ao gerar veredicto. Tente novamente.', 'warning')

    return render_template(
        'veredicto/relatorio.html',
        dados=dados,
        titulo_pagina='Relatório de Veredicto Final',
    )


@verificacoes_bp.route('/<int:verificacao_id>/veredicto/regenerar', methods=['POST'])
@requer_admin
def regenerar_veredicto(verificacao_id):
    from core.veredicto_builder import construir_e_guardar_veredicto
    try:
        construir_e_guardar_veredicto(verificacao_id, usar_llm=True)
        flash('Veredicto regenerado com sucesso.', 'success')
    except ValueError:
        flash('Verificação não encontrada.', 'danger')
    except Exception as e:
        current_app.logger.error(f"Erro ao regenerar veredicto: {e}")
        flash('Erro ao regenerar. Verifique os logs.', 'warning')
    return redirect(url_for('verificacoes.ver_veredicto', verificacao_id=verificacao_id))
