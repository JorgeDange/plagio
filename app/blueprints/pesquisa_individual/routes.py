import os
import json
import csv
import io
import uuid
from flask import render_template, request, jsonify, Response, current_app, redirect, url_for, flash
from flask_login import current_user
from app.database import db
from core.auth_helpers import requer_verificador
from core.ingestor import extrair, limpar_texto
from core.pesquisa_externa import pesquisar_texto_completo
from core.embeddings import gerar_embedding, gerar_embeddings_lote
from . import pesquisa_individual_bp


class _EmbeddingAdapter:
    """Adaptador que expoe .encode() e .encode_batch() usando OpenRouter API."""
    def encode(self, text):
        import numpy as np
        try:
            return np.array(gerar_embedding(text))
        except Exception as e:
            import logging
            logging.error(f"Erro ao gerar embedding: {e}")
            # Retornar vector zero para evitar crash
            return np.zeros(1024)
    
    def encode_batch(self, texts):
        import numpy as np
        if not texts:
            return []
        try:
            embeddings = gerar_embeddings_lote(texts)
            return [np.array(e) for e in embeddings]
        except Exception as e:
            import logging
            logging.error(f"Erro ao gerar embeddings em lote: {e}")
            return [np.zeros(1024) for _ in texts]

@pesquisa_individual_bp.route('/')
@requer_verificador
def index():
    conn = db.get_db()
    cur = conn.cursor()
    cur.execute('''
        SELECT id, tipo_entrada, total_resultados, criado_em 
        FROM pesquisas_avulsas 
        WHERE utilizador_id = %s 
        ORDER BY criado_em DESC LIMIT 10
    ''', (current_user.id,))
    hist_cols = [d[0] for d in cur.description]
    historico = [dict(zip(hist_cols, row)) for row in cur.fetchall()]
    cur.close()
    
    fontes_disponiveis = [
        {"id":"openalex","nome":"OpenAlex","descricao":"260M+ trabalhos académicos","ativa":True},
        {"id":"semantic_scholar","nome":"Semantic Scholar","descricao":"220M+ artigos científicos","ativa":True},
        {"id":"core","nome":"CORE","descricao":"Acesso aberto internacional","ativa":True},
        {"id":"crossref","nome":"CrossRef","descricao":"Validação de referências bibliográficas","ativa":True},
        {"id":"serper","nome":"Google (Serper)","descricao":"Pesquisa web geral via Google","ativa":os.getenv("SERPER_API_KEY", "") != ""},
    ]
    
    return render_template('pesquisa_individual/index.html', historico=historico, fontes_disponiveis=fontes_disponiveis)

@pesquisa_individual_bp.route('/executar', methods=['POST'])
@requer_verificador
def executar():
    tipo_entrada = request.form.get('tipo_entrada')
    texto = request.form.get('texto', '').strip()
    titulo = request.form.get('titulo', '').strip()
    fontes = request.form.getlist('fontes[]')
    limiar_str = request.form.get('limiar', '0.65')
    
    try:
        limiar = float(limiar_str)
        if limiar > 1.0:
            limiar = limiar / 100.0
    except ValueError:
        limiar = 0.65
        
    texto_pesquisa = ""
    if tipo_entrada == 'texto':
        texto_pesquisa = texto
    elif tipo_entrada == 'titulo':
        texto_pesquisa = titulo
    elif tipo_entrada == 'ficheiro':
        if 'ficheiro' not in request.files:
            return jsonify({'sucesso': False, 'erro': 'Nenhum ficheiro enviado'}), 400
        ficheiro = request.files['ficheiro']
        if not ficheiro.filename:
            return jsonify({'sucesso': False, 'erro': 'Nenhum ficheiro seleccionado'}), 400
            
        extensao = os.path.splitext(ficheiro.filename)[1].lower()
        if extensao not in ['.pdf', '.docx', '.txt']:
            return jsonify({'sucesso': False, 'erro': 'Formato não suportado'}), 400
            
        caminho_tmp = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'instance/uploads'), f"tmp_{uuid.uuid4().hex}{extensao}")
        os.makedirs(os.path.dirname(caminho_tmp), exist_ok=True)
        ficheiro.save(caminho_tmp)
        
        try:
            texto_bruto = extrair(caminho_tmp)
            texto_pesquisa = limpar_texto(texto_bruto)
        except Exception as e:
            return jsonify({'sucesso': False, 'erro': f'Erro ao processar ficheiro: {str(e)}'}), 500
        finally:
            if os.path.exists(caminho_tmp):
                os.remove(caminho_tmp)
                
    if not texto_pesquisa or (tipo_entrada != 'titulo' and len(texto_pesquisa) < 50):
        return jsonify({'sucesso': False, 'erro': 'O texto de pesquisa deve ter no mínimo 50 caracteres'}), 400
        
    if not fontes:
        fontes = ['openalex', 'semantic_scholar', 'core', 'crossref', 'serper']
        
    config = {
        "email_cortesia": current_app.config.get("EMAIL_CORTESIA", ""),
        "semantic_scholar_key": current_app.config.get("SEMANTIC_SCHOLAR_KEY", ""),
        "core_key": current_app.config.get("CORE_KEY", ""),
        "serper_api_key": os.getenv("SERPER_API_KEY", ""),
        "serper_api_url": os.getenv("SERPER_API_URL", "https://google.serper.dev/search"),
        "serper_timeout": os.getenv("SERPER_TIMEOUT_SECONDS", 15),
        "serper_max_retries": os.getenv("SERPER_MAX_RETRIES", 2),
    }
    
    if tipo_entrada == 'titulo':
        from core.pesquisa_externa import pesquisar_todas_fontes, calcular_scores_semanticos
        res_brutos = pesquisar_todas_fontes(texto_pesquisa, fontes, config=config)
        res_scores = calcular_scores_semanticos(texto_pesquisa, res_brutos, _EmbeddingAdapter())
        suspeitos = []
        for r in res_scores:
            if r["score_semantico"] >= limiar:
                r["frase_origem"] = texto_pesquisa
                suspeitos.append(r)
                
        resultado_externo = {
            "sucesso": True,
            "frases_pesquisadas": [texto_pesquisa],
            "total_resultados_brutos": len(res_brutos),
            "total_suspeitos": len(suspeitos),
            "suspeitos": suspeitos,
            "erro": None
        }
    else:
        resultado_externo = pesquisar_texto_completo(
            texto=texto_pesquisa,
            modelo_embeddings=_EmbeddingAdapter(),
            config=config,
            limiar_alerta=limiar,
            max_frases=7,
            fontes=fontes
        )
        
    if not resultado_externo.get("sucesso"):
        return jsonify({"sucesso": False, "erro": resultado_externo.get("erro")}), 500
        
    conn = db.get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO pesquisas_avulsas (utilizador_id, tipo_entrada, texto_consulta, fontes_usadas, total_resultados)
        VALUES (%s, %s, %s, %s, %s) RETURNING id
    ''', (current_user.id, tipo_entrada, texto_pesquisa, json.dumps(fontes), resultado_externo.get("total_suspeitos", 0)))
    pesquisa_id = cursor.fetchone()[0]
    
    suspeitos = resultado_externo.get("suspeitos", [])
    for s in suspeitos:
        autores = json.dumps(s.get("autores", [])) if s.get("autores") else None
        cursor.execute('''
            INSERT INTO fontes_externas_resultados (
                fonte, titulo_externo, autores, ano_publicacao, doi, url_fonte, resumo_externo, score_semantico, pesquisa_id
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (
            s.get("fonte"),
            s.get("titulo"),
            autores,
            s.get("ano"),
            s.get("doi"),
            s.get("url"),
            s.get("resumo"),
            s.get("score_semantico"),
            pesquisa_id
        ))
        
    conn.commit()
    cursor.close()
    
    return jsonify({
        "sucesso": True,
        "pesquisa_id": pesquisa_id,
        "total_suspeitos": len(suspeitos),
        "suspeitos": suspeitos,
        "frases_pesquisadas": resultado_externo.get("frases_pesquisadas", [])
    })

@pesquisa_individual_bp.route('/resultado/<int:pesquisa_id>')
@requer_verificador
def resultado(pesquisa_id):
    conn = db.get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM pesquisas_avulsas WHERE id = %s AND utilizador_id = %s", (pesquisa_id, current_user.id))
    p_cols = [d[0] for d in cur.description]
    row = cur.fetchone()
    pesquisa = dict(zip(p_cols, row)) if row else None
    if not pesquisa:
        cur.close()
        flash("Pesquisa não encontrada ou acesso negado.", "erro")
        return redirect(url_for('pesquisa_individual.index'))
        
    cur.execute("SELECT * FROM fontes_externas_resultados WHERE pesquisa_id = %s ORDER BY score_semantico DESC", (pesquisa_id,))
    r_cols = [d[0] for d in cur.description]
    resultados = [dict(zip(r_cols, row)) for row in cur.fetchall()]
    cur.close()
    
    return render_template('pesquisa_individual/resultado.html', pesquisa=pesquisa, resultados=resultados)

@pesquisa_individual_bp.route('/exportar/<int:pesquisa_id>/<formato>')
@requer_verificador
def exportar(pesquisa_id, formato):
    conn = db.get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM pesquisas_avulsas WHERE id = %s AND utilizador_id = %s", (pesquisa_id, current_user.id))
    p_cols = [d[0] for d in cur.description]
    row = cur.fetchone()
    pesquisa = dict(zip(p_cols, row)) if row else None
    if not pesquisa:
        cur.close()
        flash("Pesquisa não encontrada.", "erro")
        return redirect(url_for('pesquisa_individual.index'))
        
    cur.execute("SELECT * FROM fontes_externas_resultados WHERE pesquisa_id = %s ORDER BY score_semantico DESC", (pesquisa_id,))
    r_cols = [d[0] for d in cur.description]
    resultados = [dict(zip(r_cols, row)) for row in cur.fetchall()]
    
    if formato == 'csv':
        output = io.StringIO()
        output.write('\ufeff')
        writer = csv.writer(output)
        writer.writerow(['Posição', 'Título', 'Autores', 'Ano', 'DOI', 'Fonte', 'Semelhança (%)', 'URL'])
        
        for idx, r in enumerate(resultados, 1):
            score_pct = round(r['score_semantico'] * 100, 1) if r['score_semantico'] else 0
            autores = r['autores']
            if autores:
                try:
                    autores = ", ".join(json.loads(autores))
                except:
                    pass
            writer.writerow([
                idx, r['titulo_externo'], autores, r['ano_publicacao'], r['doi'], 
                r['fonte'], f"{score_pct}%", r['url_fonte']
            ])
            
        cur.execute("UPDATE pesquisas_avulsas SET exportado_csv = 1 WHERE id = %s", (pesquisa_id,))
        conn.commit()
        cur.close()
            
        return Response(output.getvalue(), mimetype="text/csv", headers={"Content-Disposition": f"attachment;filename=pesquisa_externa_{pesquisa_id}.csv"})
        
    elif formato == 'pdf':
        cur.close()
        try:
            import pdfkit
            html = "<html><head><meta charset='utf-8'></head><body><h1>Relatório de Pesquisa Externa</h1>"
            for r in resultados:
                score = round(r['score_semantico'] * 100, 1)
                html += f"<h3>{r['titulo_externo']} - {score}%</h3>"
                html += f"<p>Fonte: {r['fonte']} | Ano: {r['ano_publicacao']}</p>"
                html += f"<p>{r['resumo_externo']}</p><hr>"
            html += "</body></html>"
            
            pdf = pdfkit.from_string(html, False)
            cur2 = conn.cursor()
            cur2.execute("UPDATE pesquisas_avulsas SET exportado_pdf = 1 WHERE id = %s", (pesquisa_id,))
            conn.commit()
            cur2.close()
            return Response(pdf, mimetype="application/pdf", headers={"Content-Disposition": f"attachment;filename=pesquisa_externa_{pesquisa_id}.pdf"})
        except Exception:
            return "Biblioteca para gerar PDF (pdfkit/wkhtmltopdf) não disponível. Utilize a exportação CSV.", 501
            
    cur.close()
    return "Formato inválido", 400

@pesquisa_individual_bp.route('/historico/<int:pesquisa_id>', methods=['DELETE'])
@requer_verificador
def apagar_historico(pesquisa_id):
    conn = db.get_db()
    cur = conn.cursor()
    cur.execute("SELECT id FROM pesquisas_avulsas WHERE id = %s AND utilizador_id = %s", (pesquisa_id, current_user.id))
    row = cur.fetchone()
    if not row:
        cur.close()
        return jsonify({"sucesso": False, "erro": "Pesquisa não encontrada"}), 404
        
    cur.execute("DELETE FROM fontes_externas_resultados WHERE pesquisa_id = %s", (pesquisa_id,))
    cur.execute("DELETE FROM pesquisas_avulsas WHERE id = %s", (pesquisa_id,))
    conn.commit()
    cur.close()
    
    return jsonify({"sucesso": True})
