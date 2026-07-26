import re
import os
import time
import requests
import concurrent.futures
import difflib
import json
import logging
from typing import List, Dict, Any, Optional

def extrair_frases_chave(texto: str, max_frases: int = 7) -> List[str]:
    """
    Extrai as frases mais representativas de um trecho de texto para usar
    como termos de pesquisa nas APIs externas.
    """
    if not texto or not isinstance(texto, str):
        return []

    # 1. Dividir o texto em frases
    delimiters = re.compile(r'[.!?\n]+')
    frases_brutas = delimiters.split(texto)
    
    frases_limpas = []
    for f in frases_brutas:
        f = f.strip()
        if not f:
            continue
        palavras = f.split()
        
        # 2. Remover frases com menos de 8 palavras
        # 3. Remover frases com mais de 25 palavras
        if len(palavras) < 8 or len(palavras) > 25:
            continue
            
        # 4. Remover frases com mais de 40% de stop words
        stop_words = {
            'de','a','o','que','e','do','da','em','um','para','com','uma','os','no','se','na',
            'por','mais','as','dos','como','mas','foi','ao','ele','das','tem','à','seu','sua',
            'ou','ser','quando','muito','há','nos','já','também','só','pelo','pela',
            'the','is','in','at','of','on','and','a','to','it','for','with','as','by'
        }
        
        stop_count = sum(1 for p in palavras if p.lower() in stop_words)
        if stop_count / len(palavras) > 0.4:
            continue
            
        frases_limpas.append((f, palavras))
        
    # Se não sobrar nada, tenta usar as frases maiores do texto completo
    if not frases_limpas:
        frases_brutas_2 = [f.strip() for f in delimiters.split(texto) if f.strip()]
        frases_brutas_2.sort(key=lambda x: len(x.split()), reverse=True)
        return [f for f in frases_brutas_2 if len(f.split()) >= 3][:max_frases]
        
    # 5. Pontuar cada frase restante pelo número de palavras longas sem stop words
    pontuadas = []
    for f, palavras in frases_limpas:
        score = 0
        for p in palavras:
            p_limpa = re.sub(r'\W+', '', p).lower()
            if len(p_limpa) > 5 and p_limpa not in stop_words:
                score += 1
        pontuadas.append((score, f))
        
    # 6. Retornar as max_frases com maior pontuação
    pontuadas.sort(key=lambda x: x[0], reverse=True)
    return [x[1] for x in pontuadas[:max_frases]]

def pesquisar_openalex(query: str, max_resultados: int = 5, email_cortesia: str = "") -> List[Dict[str, Any]]:
    """Pesquisa trabalhos académicos na API OpenAlex."""
    if not query:
        return []
        
    url = "https://api.openalex.org/works"
    params = {
        "search": query,
        "per_page": max_resultados,
        "select": "id,title,authorships,publication_year,doi,abstract_inverted_index,primary_location,open_access"
    }
    if email_cortesia:
        params["mailto"] = email_cortesia
        
    try:
        response = requests.get(url, params=params, timeout=8)
        response.raise_for_status()
        data = response.json()
        
        resultados = []
        for item in data.get("results", []):
            titulo = item.get("title")
            if not titulo:
                continue
                
            autores = []
            for author_obj in item.get("authorships", []):
                a = author_obj.get("author", {}).get("display_name")
                if a: autores.append(a)
                
            ano = item.get("publication_year")
            doi = item.get("doi")
            
            url_fonte = None
            oa = item.get("open_access", {})
            if oa and oa.get("oa_url"):
                url_fonte = oa.get("oa_url")
            elif item.get("primary_location") and item.get("primary_location").get("landing_page_url"):
                url_fonte = item.get("primary_location").get("landing_page_url")
                
            abstract = ""
            inv_index = item.get("abstract_inverted_index")
            if inv_index:
                max_pos = max(pos for positions in inv_index.values() for pos in positions)
                palavras = [""] * (max_pos + 1)
                for word, positions in inv_index.items():
                    for pos in positions:
                        palavras[pos] = word
                abstract = " ".join(p for p in palavras if p)
                
            resultados.append({
                "fonte": "openalex",
                "titulo": titulo,
                "autores": autores,
                "ano": ano,
                "doi": doi,
                "url": url_fonte,
                "resumo": abstract
            })
            
        return resultados
    except Exception as e:
        import logging
        logging.error(f"Erro na pesquisa OpenAlex: {e}")
        return []

def pesquisar_semantic_scholar(query: str, max_resultados: int = 5, api_key: str = "") -> List[Dict[str, Any]]:
    """Pesquisa na API Semantic Scholar."""
    if not query:
        return []
        
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {
        "query": query,
        "limit": max_resultados,
        "fields": "title,authors,year,externalIds,abstract,openAccessPdf,url"
    }
    headers = {}
    if api_key:
        headers["x-api-key"] = api_key
        
    try:
        response = requests.get(url, params=params, headers=headers, timeout=8)
        response.raise_for_status()
        data = response.json()
        
        resultados = []
        for item in data.get("data", []):
            titulo = item.get("title")
            if not titulo:
                continue
                
            autores = [a.get("name") for a in item.get("authors", []) if a.get("name")]
            ano = item.get("year")
            doi = item.get("externalIds", {}).get("DOI")
            
            url_fonte = None
            if item.get("openAccessPdf") and item.get("openAccessPdf").get("url"):
                url_fonte = item.get("openAccessPdf").get("url")
            elif item.get("url"):
                url_fonte = item.get("url")
                
            resumo = item.get("abstract") or ""
            
            resultados.append({
                "fonte": "semantic_scholar",
                "titulo": titulo,
                "autores": autores,
                "ano": ano,
                "doi": doi,
                "url": url_fonte,
                "resumo": resumo
            })
            
        return resultados
    except Exception as e:
        import logging
        logging.error(f"Erro na pesquisa Semantic Scholar: {e}")
        return []

def pesquisar_core(query: str, max_resultados: int = 5, api_key: str = "") -> List[Dict[str, Any]]:
    """Pesquisa na API CORE."""
    if not query:
        return []
        
    url = "https://api.core.ac.uk/v3/search/works"
    params = {
        "q": query,
        "limit": max_resultados
    }
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
        
    try:
        response = requests.get(url, params=params, headers=headers, timeout=8)
        response.raise_for_status()
        data = response.json()
        
        resultados = []
        for item in data.get("results", []):
            titulo = item.get("title")
            if not titulo:
                continue
                
            autores = [a.get("name") for a in item.get("authors", []) if a.get("name")]
            ano = item.get("yearPublished")
            doi = item.get("doi")
            url_fonte = item.get("downloadUrl")
            resumo = item.get("abstract") or ""
            
            resultados.append({
                "fonte": "core",
                "titulo": titulo,
                "autores": autores,
                "ano": ano,
                "doi": doi,
                "url": url_fonte,
                "resumo": resumo
            })
            
        return resultados
    except Exception as e:
        import logging
        logging.error(f"Erro na pesquisa CORE: {e}")
        return []

def pesquisar_crossref(query: str, max_resultados: int = 5, email_cortesia: str = "") -> List[Dict[str, Any]]:
    """Pesquisa metadados na API CrossRef."""
    if not query:
        return []
        
    url = "https://api.crossref.org/works"
    params = {
        "query": query,
        "rows": max_resultados,
        "select": "title,author,published,DOI,URL,abstract"
    }
    if email_cortesia:
        params["mailto"] = email_cortesia
        
    try:
        response = requests.get(url, params=params, timeout=8)
        response.raise_for_status()
        data = response.json()
        
        resultados = []
        for item in data.get("message", {}).get("items", []):
            titles = item.get("title", [])
            titulo = titles[0] if titles else None
            if not titulo:
                continue
                
            autores = []
            for a in item.get("author", []):
                given = a.get("given", "")
                family = a.get("family", "")
                nome = f"{given} {family}".strip()
                if nome:
                    autores.append(nome)
                    
            ano = None
            published = item.get("published", {})
            date_parts = published.get("date-parts", [])
            if date_parts and date_parts[0]:
                ano = date_parts[0][0]
                
            doi = item.get("DOI")
            url_fonte = item.get("URL")
            
            resumo = item.get("abstract") or ""
            resumo = re.sub(r'<[^>]+>', '', resumo).strip()
            
            resultados.append({
                "fonte": "crossref",
                "titulo": titulo,
                "autores": autores,
                "ano": ano,
                "doi": doi,
                "url": url_fonte,
                "resumo": resumo
            })
            
        return resultados
    except Exception as e:
        import logging
        logging.error(f"Erro na pesquisa CrossRef: {e}")
        return []
        
def pesquisar_serper(query: str, max_resultados: int = 5, config: Dict = None) -> List[Dict[str, Any]]:
    """Pesquisa na web (Google) via API Serper.dev."""
    if not query:
        return []
    
    if config is None:
        config = {}
    
    api_key = config.get("serper_api_key") or os.getenv("SERPER_API_KEY", "")
    api_url = config.get("serper_api_url") or os.getenv("SERPER_API_URL", "https://google.serper.dev/search")
    timeout = int(config.get("serper_timeout") or os.getenv("SERPER_TIMEOUT_SECONDS", 15))
    max_retries = int(config.get("serper_max_retries") or os.getenv("SERPER_MAX_RETRIES", 2))
    
    if not api_key:
        logging.debug("SERPER_API_KEY nao configurada — pesquisa Serper desactivada.")
        return []
    
    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json"
    }
    payload = {"q": query}
    
    last_error = None
    for attempt in range(max_retries):
        try:
            response = requests.post(
                api_url,
                json=payload,
                headers=headers,
                timeout=timeout
            )
            
            if response.status_code in (401, 403, 429):
                logging.warning(f"Serper API erro {response.status_code}: {response.text[:200]}")
                return []
            
            response.raise_for_status()
            data = response.json()
            
            resultados = []
            for item in data.get("organic", [])[:max_resultados]:
                titulo = item.get("title")
                if not titulo:
                    continue
                
                autores = []
                snippet = item.get("snippet", "")
                
                resultados.append({
                    "fonte": "Google (Serper)",
                    "titulo": titulo,
                    "autores": autores,
                    "ano": None,
                    "doi": None,
                    "url": item.get("link"),
                    "resumo": snippet
                })
            
            return resultados
        
        except requests.exceptions.Timeout:
            last_error = "timeout"
            if attempt < max_retries - 1:
                wait = 2 ** attempt
                time.sleep(wait)
        except requests.exceptions.ConnectionError:
            last_error = "connection_error"
            if attempt < max_retries - 1:
                wait = 2 ** attempt
                time.sleep(wait)
        except Exception as e:
            logging.warning(f"Erro inesperado na pesquisa Serper: {e}")
            return []
    
    logging.warning(f"Serper: todas as {max_retries} tentativas falharam ({last_error}).")
    return []

def pesquisar_todas_fontes(query: str, fontes: List[str] = None, max_por_fonte: int = 5, config: Dict = None) -> List[Dict]:
    """
    Orquestrador que executa as 5 pesquisas em paralelo e devolve os
    resultados fundidos e deduplicados.
    """
    if config is None:
        config = {}
        
    fontes_disponiveis = {
        "openalex": lambda: pesquisar_openalex(query, max_por_fonte, config.get("email_cortesia", "")),
        "semantic_scholar": lambda: pesquisar_semantic_scholar(query, max_por_fonte, config.get("semantic_scholar_key", "")),
        "core": lambda: pesquisar_core(query, max_por_fonte, config.get("core_key", "")),
        "crossref": lambda: pesquisar_crossref(query, max_por_fonte, config.get("email_cortesia", "")),
        "serper": lambda: pesquisar_serper(query, max_por_fonte, config)
    }
    
    if fontes is None:
        fontes_a_usar = list(fontes_disponiveis.keys())
    else:
        fontes_a_usar = [f for f in fontes if f in fontes_disponiveis]
        
    resultados_brutos = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futuros = {executor.submit(fontes_disponiveis[f]): f for f in fontes_a_usar}
        for futuro in concurrent.futures.as_completed(futuros, timeout=15):
            try:
                resultados = futuro.result()
                if resultados:
                    resultados_brutos.extend(resultados)
            except Exception as e:
                import logging
                logging.error(f"Erro numa das threads de pesquisa: {e}")
                
    # Deduplicação
    resultados_deduplicados = []
    for res in resultados_brutos:
        is_duplicate = False
        for existente in resultados_deduplicados:
            if res.get("doi") and existente.get("doi") and res["doi"].lower() == existente["doi"].lower():
                is_duplicate = True
            elif res.get("titulo") and existente.get("titulo"):
                sim = difflib.SequenceMatcher(None, res["titulo"].lower(), existente["titulo"].lower()).ratio()
                if sim > 0.92:
                    is_duplicate = True
                    
            if is_duplicate:
                if len(res.get("resumo", "")) > len(existente.get("resumo", "")):
                    existente["resumo"] = res.get("resumo", "")
                break
                
        if not is_duplicate:
            resultados_deduplicados.append(res)
            
    resultados_deduplicados.sort(key=lambda x: (x.get("ano") or 0, len(x.get("resumo", ""))), reverse=True)
    return resultados_deduplicados

def calcular_scores_semanticos(texto_original: str, resultados: List[Dict], modelo_embeddings) -> List[Dict]:
    """Compara semanticamente o texto original com os resultados encontrados."""
    if not resultados or not texto_original:
        return []
        
    import numpy as np
    
    def cosine_sim(a, b):
        a = np.asarray(a, dtype=np.float32)
        b = np.asarray(b, dtype=np.float32)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))
    
    # Gerar embedding do texto original UMA vez
    emb_original = modelo_embeddings.encode(texto_original[:8000])
    
    # Coletar todos os textos para gerar embeddings em lote
    textos_comparar = []
    indices_validos = []
    for idx, res in enumerate(resultados):
        titulo = res.get("titulo", "")
        resumo = res.get("resumo", "")
        if not titulo and not resumo:
            continue
        texto_comparar = f"{titulo}. {resumo}" if resumo else titulo
        textos_comparar.append(texto_comparar[:8000])
        indices_validos.append(idx)
    
    if not textos_comparar:
        return []
    
    # Gerar embeddings em lote (MUCHO mais rapido que um por um)
    try:
        emb_lote = modelo_embeddings.encode_batch(textos_comparar)
    except AttributeError:
        # Fallback: se o adapter nao tem encode_batch, usar individual
        emb_lote = [modelo_embeddings.encode(t) for t in textos_comparar]
    
    resultados_finais = []
    for i, texto_idx in enumerate(indices_validos):
        score = cosine_sim(emb_original, emb_lote[i])
        resultados[texto_idx]["score_semantico"] = score
        if score >= 0.30:
            resultados_finais.append(resultados[texto_idx])
            
    resultados_finais.sort(key=lambda x: x.get("score_semantico", 0.0), reverse=True)
    return resultados_finais

def pesquisar_texto_completo(texto: str, modelo_embeddings, config: Dict = None, limiar_alerta: float = 0.70, max_frases: int = 7, fontes: List[str] = None) -> Dict:
    """Orquestra o fluxo de pesquisa para um texto completo."""
    try:
        frases_chave = extrair_frases_chave(texto, max_frases=max_frases)
        
        if not frases_chave:
            frases_chave = [texto[:200]]
            
        todos_suspeitos = []
        
        for frase in frases_chave:
            resultados = pesquisar_todas_fontes(frase, fontes=fontes, config=config)
            resultados_com_score = calcular_scores_semanticos(texto, resultados, modelo_embeddings)
            
            for res in resultados_com_score:
                if res["score_semantico"] >= limiar_alerta:
                    res_copy = dict(res)
                    res_copy["frase_origem"] = frase
                    todos_suspeitos.append(res_copy)
                    
        suspeitos_dedup = []
        for res in todos_suspeitos:
            is_duplicate = False
            for existente in suspeitos_dedup:
                if res.get("doi") and existente.get("doi") and res["doi"].lower() == existente["doi"].lower():
                    is_duplicate = True
                elif res.get("titulo") and existente.get("titulo"):
                    sim = difflib.SequenceMatcher(None, res["titulo"].lower(), existente["titulo"].lower()).ratio()
                    if sim > 0.92:
                        is_duplicate = True
                        
                if is_duplicate:
                    if res.get("score_semantico", 0) > existente.get("score_semantico", 0):
                        existente["score_semantico"] = res["score_semantico"]
                        existente["frase_origem"] = res["frase_origem"]
                    break
                    
            if not is_duplicate:
                suspeitos_dedup.append(res)
                
        suspeitos_dedup.sort(key=lambda x: x.get("score_semantico", 0.0), reverse=True)
        
        return {
            "sucesso": True,
            "frases_pesquisadas": frases_chave,
            "total_resultados_brutos": len(todos_suspeitos),
            "total_suspeitos": len(suspeitos_dedup),
            "suspeitos": suspeitos_dedup,
            "erro": None
        }
    except Exception as e:
        return {
            "sucesso": False,
            "frases_pesquisadas": [],
            "total_resultados_brutos": 0,
            "total_suspeitos": 0,
            "suspeitos": [],
            "erro": str(e)
        }
