import threading
import time
import json
import uuid
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

# Global state for SSE
sessoes_ativas = {}

def processar_sessao_pesquisa(sessao_id: str, db_path: str):
    from core.pesquisa_externa import CoreAPI, OpenAlexAPI, SemanticScholarAPI, RCAAPApi, ArxivAPI
    from core.chunker import dividir_em_chunks
    from app.database.db import get_db
    
    sessoes_ativas[sessao_id] = {
        "status_geral": "a_processar",
        "apis": {},
        "resultados": [],
        "total_encontrado": 0,
        "inicio": time.time()
    }
    estado = sessoes_ativas[sessao_id]
    
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM sessoes_pesquisa WHERE id = %s", (sessao_id,))
        s_cols = [d[0] for d in cur.description]
        sessao_row = cur.fetchone()
        sessao = dict(zip(s_cols, sessao_row)) if sessao_row else None
        
        if not sessao:
            logging.error(f"Sessão {sessao_id} não encontrada.")
            cur.close()
            return
            
        filtros = json.loads(sessao["filtros_json"])
        apis_activas = filtros.get("apis", ["core", "openalex", "semanticscholar", "rcaap", "arxiv"])
        modo = sessao["modo_entrada"]
        texto_original = sessao["texto_original"]
        score_minimo = float(filtros.get("score_minimo", 0.60))
        limite_resultados = int(filtros.get("limite_resultados", 20))
        
        cur.execute("SELECT chave, valor FROM config_pesquisa_externa")
        c_cols = [d[0] for d in cur.description]
        configs_db = [dict(zip(c_cols, row)) for row in cur.fetchall()]
        configs = {row['chave']: row['valor'] for row in configs_db}
        timeout_api = int(configs.get('timeout_api', '8'))
        core_api_key = configs.get('core_api_key', '')
        
        motores = {}
        if "core" in apis_activas: motores["core"] = CoreAPI(core_api_key, timeout_api)
        if "openalex" in apis_activas: motores["openalex"] = OpenAlexAPI(timeout_api)
        if "semanticscholar" in apis_activas: motores["semanticscholar"] = SemanticScholarAPI(timeout_api)
        if "rcaap" in apis_activas: motores["rcaap"] = RCAAPApi(timeout_api)
        if "arxiv" in apis_activas: motores["arxiv"] = ArxivAPI(timeout_api)
        
        for api in apis_activas:
            estado["apis"][api] = {"status": "pesquisando", "encontrados": 0}
            
        queries = []
        chunks_utilizados = []
        
        if modo == "titulo":
            queries.append((texto_original, texto_original))
        else:
            from core.pesquisa_externa import extrair_palavras_chave
            chunks = dividir_em_chunks(texto_original, tamanho=400, overlap=50)
            chunks_validos = [c for c in chunks if len(c) > 150 and not c.replace(" ", "").isdigit()]
            chunks_validos = sorted(chunks_validos, key=len, reverse=True)[:5]
            
            for c in chunks_validos:
                q = extrair_palavras_chave(c, max_palavras=12)
                if q:
                    queries.append((q, c))
                    
        modelo_labse = None
        if modo != "titulo":
            from core.embeddings import modelo
            modelo_labse = modelo
            
        def pesquisar_api(api_nome, motor):
            try:
                for query, chunk_origem in queries:
                    lim_por_query = limite_resultados if modo == "titulo" else 10
                    res_raw = motor.pesquisar(query, limite=lim_por_query)
                    
                    for r in res_raw:
                        resumo_texto = r.get("resumo") or r.get("titulo")
                        sim = 1.0
                        
                        if modo != "titulo" and modelo_labse and resumo_texto:
                            from sentence_transformers.util import cos_sim
                            emb_chunk = modelo_labse.encode([chunk_origem], normalize_embeddings=True)
                            emb_res = modelo_labse.encode([resumo_texto], normalize_embeddings=True)
                            sim = cos_sim(emb_chunk, emb_res)[0][0].item()
                            
                        if sim >= score_minimo:
                            r["score"] = float(sim)
                            r["chunk_origem"] = chunk_origem
                            r["api_fonte_id"] = api_nome
                            
                            estado["resultados"].append(r)
                            estado["apis"][api_nome]["encontrados"] += 1
                            estado["total_encontrado"] += 1
                            
                estado["apis"][api_nome]["status"] = "concluido"
            except Exception as e:
                logging.error(f"Erro na API {api_nome}: {e}")
                estado["apis"][api_nome]["status"] = "erro"

        with ThreadPoolExecutor(max_workers=len(motores)) as executor:
            futuros = [executor.submit(pesquisar_api, nome, motor) for nome, motor in motores.items()]
            try:
                for futuro in as_completed(futuros, timeout=300):
                    pass
            except TimeoutError:
                logging.warning(f"Timeout global na sessão {sessao_id}. Algumas APIs podem não ter concluído.")
                
        vistos = set()
        resultados_finais = []
        
        estado["resultados"].sort(key=lambda x: x.get("score", 0), reverse=True)
        
        for r in estado["resultados"]:
            chave = (r["titulo"].lower().strip(), r.get("ano"))
            if chave not in vistos:
                vistos.add(chave)
                resultados_finais.append(r)
                
        resultados_finais = resultados_finais[:limite_resultados]
        estado["resultados"] = resultados_finais
        estado["total_encontrado"] = len(resultados_finais)
        
        tempo_total = round(time.time() - estado["inicio"], 2)
        
        for idx, r in enumerate(resultados_finais):
            r["posicao_ranking"] = idx + 1
            cur.execute('''
                INSERT INTO resultados_pesquisa 
                (sessao_id, api_fonte, titulo, autores, ano, resumo, url, score_labse, chunk_origem, posicao_ranking)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                sessao_id, r.get("api_fonte", r["api_fonte_id"]), r["titulo"], r.get("autores"),
                r.get("ano"), r.get("resumo"), r.get("url"), r.get("score"), r.get("chunk_origem"), r["posicao_ranking"]
            ))
            
        cur.execute('''
            UPDATE sessoes_pesquisa 
            SET estado = 'concluido', total_resultados = %s, tempo_segundos = %s
            WHERE id = %s
        ''', (len(resultados_finais), tempo_total, sessao_id))
        
        conn.commit()
        cur.close()
        estado["status_geral"] = "concluido"
        estado["tempo_segundos"] = tempo_total
        
    except Exception as e:
        logging.error(f"Erro ao processar sessão {sessao_id}: {e}")
        estado["status_geral"] = "erro"
        if 'conn' in locals():
            try:
                cur2 = conn.cursor()
                cur2.execute("UPDATE sessoes_pesquisa SET estado = 'erro' WHERE id = %s", (sessao_id,))
                conn.commit()
                cur2.close()
            except:
                pass
