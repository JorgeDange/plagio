# ═══════════════════════════════════
# FICHEIRO: core/normas_verificacao_integrada.py
# ═══════════════════════════════════
import json
import logging
from typing import Dict, Any, Optional

from app.database.db import get_db
from core.normas_regras import verificar_normas
from core.normas_imetro_checker import UnimetroInspector
from core.normas_imetro_prompt import build_normas_payload

logger = logging.getLogger(__name__)

def executar_verificacao_normas(
    verificacao_id: int,
    tcc_id: int,
    texto_completo: str,
    executar_ia: bool = False,
    config_ia: dict = None
) -> dict:
    """
    Executa a verificação local e (opcionalmente) por IA das normas IMETRO.
    Consolida os resultados e guarda na base de dados.
    """
    resultado_ia = None
    
    resultado_local = verificar_normas(texto_completo, norma="IMETRO")
    
    total_regras = resultado_local.get("total_regras", 16)
    erros_e_avisos = len(resultado_local.get("erros", [])) + len(resultado_local.get("avisos", []))
    regras_ok = len(resultado_local.get("aprovadas", [])) + len(resultado_local.get("info", []))
    regras_falhou = erros_e_avisos
    local_percentagem = resultado_local.get("pontuacao", 0.0)

    if executar_ia and config_ia:
        try:
            conn = get_db()
            c = conn.cursor()
            c.execute('''
                SELECT t.titulo, t.autor as autores, c.nome as curso, o.nome as orientador, 
                       DATE_FORMAT(t.criado_em, '%%Y') as ano, t.caminho_ficheiro
                FROM tcc_suspeitos t
                LEFT JOIN cursos c ON t.curso_id = c.id
                LEFT JOIN orientadores o ON t.orientador_id = o.id
                WHERE t.id = %s
            ''', (tcc_id,))
            cols = [d[0] for d in c.description]
            _row = c.fetchone()
            row = dict(zip(cols, _row)) if _row else None
            c.close()

            if row:
                titulo = row['titulo'] or "Sem título"
                autores = row['autores'] or "Desconhecido"
                curso = row['curso'] or "Desconhecido"
                orientador = row['orientador'] or "Desconhecido"
                ano = row['ano'] or "2024"
                caminho = row['caminho_ficheiro'] or ""
                formato = caminho.split('.')[-1].upper() if '.' in caminho else "PDF"
                
                payload = build_normas_payload(
                    titulo=titulo,
                    autores=autores,
                    curso=curso,
                    orientador=orientador,
                    ano=ano,
                    num_paginas="N/D",
                    formato_ficheiro=formato,
                    texto_extraido=texto_completo
                )
                
                inspector = UnimetroInspector(
                    provider=config_ia.get("provider", "openai"),
                    model=config_ia.get("model", "gpt-4o-mini"),
                    api_key=config_ia.get("api_key", ""),
                    ollama_url=config_ia.get("ollama_url", "http://localhost:11434")
                )
                
                resultado_ia = inspector.analisar_tfc(json.dumps(payload, ensure_ascii=False))
        except Exception as e:
            logger.error(f"Erro na verificação de normas por IA: {e}")
            resultado_ia = None

    classificacao_final = _consolidar_classificacao(resultado_local, resultado_ia)
    requer_correcao = _calcular_requer_correcao(resultado_local, resultado_ia)
    resumo_problemas = _gerar_resumo_problemas(resultado_local, resultado_ia)

    conn = get_db()
    c = conn.cursor()
    
    ia_executada = 1 if resultado_ia is not None else 0
    ia_pontuacao = resultado_ia.get("pontuacao_total") if ia_executada else None
    if ia_pontuacao is None and ia_executada:
        ia_pontuacao = resultado_ia.get("pontuacao", None)
        
    ia_classificacao = resultado_ia.get("classificacao_global") if ia_executada else None
    
    infracoes_ia = resultado_ia.get("infracoes_criticas", []) if ia_executada else []
    if not infracoes_ia and ia_executada:
        infracoes_ia = resultado_ia.get("infracoes", [])
        
    ia_num_infracoes = len(infracoes_ia)
    ia_tem_bloqueante = 1 if any(i.get("gravidade", "").upper() == "BLOQUEANTE" for i in infracoes_ia) else 0

    try:
        c.execute("SELECT id FROM verificacoes_normas WHERE verificacao_id = %s", (verificacao_id,))
        row_vn = c.fetchone()
        
        local_json_str = json.dumps(resultado_local, ensure_ascii=False, separators=(',', ':'))
        ia_json_str = json.dumps(resultado_ia, ensure_ascii=False, separators=(',', ':')) if ia_executada else None
        
        if row_vn:
            normas_id = row_vn[0]
            if ia_executada:
                c.execute('''
                    UPDATE verificacoes_normas SET
                        ia_executada = %s, ia_pontuacao_total = %s, ia_classificacao = %s,
                        ia_num_infracoes = %s, ia_tem_bloqueante = %s, ia_resultado_json = %s,
                        classificacao_final = %s, requer_correcao = %s, resumo_problemas = %s,
                        atualizado_em = NOW()
                    WHERE id = %s
                ''', (ia_executada, ia_pontuacao, ia_classificacao, ia_num_infracoes,
                      ia_tem_bloqueante, ia_json_str, classificacao_final, 
                      1 if requer_correcao else 0, resumo_problemas, normas_id))
                
                c.execute("DELETE FROM verificacoes_normas_infracoes WHERE normas_id = %s AND origem = 'ia'", (normas_id,))
        else:
            c.execute('''
                INSERT INTO verificacoes_normas (
                    verificacao_id, local_executada, local_total_regras, local_regras_ok,
                    local_regras_falhou, local_percentagem, local_resultado_json,
                    ia_executada, ia_pontuacao_total, ia_classificacao, ia_num_infracoes,
                    ia_tem_bloqueante, ia_resultado_json, classificacao_final,
                    requer_correcao, resumo_problemas
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                verificacao_id, 1, total_regras, regras_ok, regras_falhou, local_percentagem, local_json_str,
                ia_executada, ia_pontuacao, ia_classificacao, ia_num_infracoes, ia_tem_bloqueante,
                ia_json_str, classificacao_final, 1 if requer_correcao else 0, resumo_problemas
            ))
            normas_id = c.lastrowid
            
        if row_vn:
            c.execute("DELETE FROM verificacoes_normas_infracoes WHERE normas_id = %s AND origem = 'local'", (normas_id,))
            
        for erro in resultado_local.get("erros", []):
            c.execute('''
                INSERT INTO verificacoes_normas_infracoes (normas_id, codigo, origem, gravidade, elemento, descricao, recomendacao, norma_violada)
                VALUES (%s, %s, 'local', 'GRAVE', 'Geral', %s, 'Corrigir de acordo com a norma do IMETRO.', %s)
            ''', (normas_id, erro.get("id"), erro.get("mensagem"), erro.get("referencia")))
            
        for aviso in resultado_local.get("avisos", []):
            c.execute('''
                INSERT INTO verificacoes_normas_infracoes (normas_id, codigo, origem, gravidade, elemento, descricao, recomendacao, norma_violada)
                VALUES (%s, %s, 'local', 'MODERADA', 'Geral', %s, 'Rever e ajustar conforme recomendado.', %s)
            ''', (normas_id, aviso.get("id"), aviso.get("mensagem"), aviso.get("referencia")))
            
        if ia_executada:
            for inf in infracoes_ia:
                c.execute('''
                    INSERT INTO verificacoes_normas_infracoes (normas_id, codigo, origem, gravidade, elemento, descricao, recomendacao, norma_violada)
                    VALUES (%s, %s, 'ia', %s, %s, %s, %s, %s)
                ''', (
                    normas_id, 
                    inf.get("codigo", "IA-ERR"), 
                    inf.get("gravidade", "MODERADA").upper(),
                    inf.get("elemento", "Desconhecido"),
                    inf.get("descricao", ""),
                    inf.get("recomendacao", ""),
                    inf.get("norma_violada", "")
                ))
                
        conn.commit()
    except Exception as e:
        logger.error(f"Erro a persistir resultados de normas: {e}")
        conn.rollback()
        return {"sucesso": False, "erro": str(e)}

    infracoes_retorno = []
    c2 = conn.cursor()
    c2.execute("SELECT * FROM verificacoes_normas_infracoes WHERE normas_id = %s ORDER BY CASE gravidade WHEN 'BLOQUEANTE' THEN 1 WHEN 'GRAVE' THEN 2 WHEN 'MODERADA' THEN 3 ELSE 4 END", (normas_id,))
    inf_cols = [d[0] for d in c2.description]
    for row in c2.fetchall():
        infracoes_retorno.append(dict(zip(inf_cols, row)))
    c2.close()

    return {
        "sucesso": True,
        "normas_id": normas_id,
        "classificacao_final": classificacao_final,
        "requer_correcao": requer_correcao,
        "resumo_problemas": resumo_problemas,
        "local": {
            "percentagem": local_percentagem,
            "regras_ok": regras_ok,
            "regras_falhou": regras_falhou,
            "resultado_completo": resultado_local
        },
        "ia": {
            "executada": bool(ia_executada),
            "pontuacao": ia_pontuacao,
            "classificacao": ia_classificacao,
            "num_infracoes": ia_num_infracoes,
            "tem_bloqueante": bool(ia_tem_bloqueante),
            "resultado_completo": resultado_ia
        },
        "infracoes": infracoes_retorno,
        "erro": None
    }


def _consolidar_classificacao(resultado_local: dict, resultado_ia: Optional[dict]) -> str:
    local_percentagem = resultado_local.get("pontuacao", 0.0)
    
    if resultado_ia is not None:
        ia_classificacao = resultado_ia.get("classificacao_global", "PENDENTE").upper()
        if ia_classificacao == "CONFORME COM RESSALVAS":
            ia_classificacao = "COM_RESSALVAS"
        elif "NÃO" in ia_classificacao or "NAO" in ia_classificacao:
            ia_classificacao = "NAO_CONFORME"
            
        if local_percentagem < 50.0:
            return "NAO_CONFORME"
        
        if ia_classificacao not in ["CONFORME", "COM_RESSALVAS", "NAO_CONFORME"]:
            if ia_classificacao == "INCONFORME": return "NAO_CONFORME"
            return "PENDENTE"
            
        return ia_classificacao
    else:
        if local_percentagem >= 85.0:
            return "CONFORME"
        elif local_percentagem >= 60.0:
            return "COM_RESSALVAS"
        else:
            return "NAO_CONFORME"


def _calcular_requer_correcao(resultado_local: dict, resultado_ia: Optional[dict]) -> bool:
    classificacao = _consolidar_classificacao(resultado_local, resultado_ia)
    if classificacao == "NAO_CONFORME":
        return True
        
    local_percentagem = resultado_local.get("pontuacao", 0.0)
    if local_percentagem < 60.0:
        return True
        
    if resultado_ia is not None:
        infracoes = resultado_ia.get("infracoes_criticas", []) or resultado_ia.get("infracoes", [])
        bloqueantes = sum(1 for i in infracoes if i.get("gravidade", "").upper() == "BLOQUEANTE")
        graves = sum(1 for i in infracoes if i.get("gravidade", "").upper() == "GRAVE")
        
        if bloqueantes > 0 or graves >= 2:
            return True
            
    return False


def _gerar_resumo_problemas(resultado_local: dict, resultado_ia: Optional[dict]) -> str:
    problemas = []
    
    local_percentagem = resultado_local.get("pontuacao", 0.0)
    
    if resultado_ia is not None:
        infracoes = resultado_ia.get("infracoes_criticas", []) or resultado_ia.get("infracoes", [])
        bloqueantes = sum(1 for i in infracoes if i.get("gravidade", "").upper() == "BLOQUEANTE")
        graves = sum(1 for i in infracoes if i.get("gravidade", "").upper() == "GRAVE")
        
        if bloqueantes > 0:
            problemas.append(f"{bloqueantes} infracções bloqueantes.")
        elif graves > 0:
            problemas.append(f"{graves} infracções graves.")
            
        ia_classificacao = resultado_ia.get("classificacao_global", "").upper()
        if ia_classificacao == "CONFORME":
            return "Conforme — apenas sugestões de melhoria pontuais."
    
    erros_locais = len(resultado_local.get("erros", []))
    if erros_locais > 0:
        problemas.append(f"{erros_locais} erros de estrutura/metodologia obrigatória.")
        
    if not problemas:
        if local_percentagem >= 85.0:
            return "Sem problemas relevantes detectados."
        else:
            return "Algumas regras locais não foram validadas."
            
    return " ".join(problemas)[:120]


def obter_resultado_normas_por_verificacao(verificacao_id: int) -> Optional[dict]:
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM verificacoes_normas WHERE verificacao_id = %s", (verificacao_id,))
    vn_cols = [d[0] for d in c.description]
    row = c.fetchone()
    
    if not row:
        c.close()
        return None
    
    row = dict(zip(vn_cols, row))
    normas_id = row['id']
    
    c.execute("SELECT * FROM verificacoes_normas_infracoes WHERE normas_id = %s ORDER BY CASE gravidade WHEN 'BLOQUEANTE' THEN 1 WHEN 'GRAVE' THEN 2 WHEN 'MODERADA' THEN 3 ELSE 4 END", (normas_id,))
    inf_cols = [d[0] for d in c.description]
    infracoes = [dict(zip(inf_cols, inf)) for inf in c.fetchall()]
    c.close()
    
    local_json = {}
    if row['local_resultado_json']:
        try:
            local_json = json.loads(row['local_resultado_json'])
        except:
            pass
            
    ia_json = None
    if row['ia_resultado_json']:
        try:
            ia_json = json.loads(row['ia_resultado_json'])
        except:
            pass

    return {
        "id": normas_id,
        "classificacao_final": row['classificacao_final'],
        "requer_correcao": bool(row['requer_correcao']),
        "resumo_problemas": row['resumo_problemas'],
        "local": {
            "percentagem": row['local_percentagem'],
            "regras_ok": row['local_regras_ok'],
            "regras_falhou": row['local_regras_falhou'],
            "resultado_completo": local_json
        },
        "ia": {
            "executada": bool(row['ia_executada']),
            "pontuacao": row['ia_pontuacao_total'],
            "classificacao": row['ia_classificacao'],
            "num_infracoes": row['ia_num_infracoes'],
            "tem_bloqueante": bool(row['ia_tem_bloqueante']),
            "resultado_completo": ia_json
        },
        "infracoes": infracoes
    }
