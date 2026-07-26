# IMETRO TFC v3 — Verificação ABNT e APA (core/abnt_checker.py)
# Funciona como ponte (wrapper) para o novo sistema de regras em normas_regras.py

import re
from core.normas_regras import verificar_normas

def verificar_abnt(texto: str) -> dict:
    """
    Analisa o texto para detectar elementos de conformidade ABNT.
    Delega para core.normas_regras.
    """
    resultado = verificar_normas(texto, "ABNT")
    
    # Adaptar as chaves para compatibilidade com o sistema de base de dados e rotas existentes
    score = resultado.get('pontuacao', 0)
    resultado['score'] = score
    resultado['nivel'] = 'Conforme' if score >= 80 else ('Parcial' if score >= 50 else 'Não Conforme')
    resultado['is_apa'] = False
    
    return resultado


def verificar_apa(texto: str) -> dict:
    """
    Analisa o texto para detectar elementos de conformidade da norma APA.
    Delega para core.normas_regras.
    """
    resultado = verificar_normas(texto, "APA")
    
    score = resultado.get('pontuacao', 0)
    resultado['score'] = score
    resultado['nivel'] = 'Conforme APA' if score >= 80 else ('Parcial APA' if score >= 50 else 'Não Conforme APA')
    resultado['is_apa'] = True
    
    return resultado


def verificar_imetro(texto: str) -> dict:
    """
    Analisa o texto para detectar elementos de conformidade das normas IMETRO 2014.
    Verificação local (sem IA) — delega para core.normas_regras.
    """
    resultado = verificar_normas(texto, "IMETRO")
    
    score = resultado.get('pontuacao', 0)
    resultado['score'] = score
    resultado['nivel'] = 'Conforme IMETRO' if score >= 85 else ('Ressalvas IMETRO' if score >= 60 else 'Não Conforme IMETRO')
    resultado['is_imetro'] = True
    
    return resultado


def estimar_secao(posicao_chunk: int, total_chunks: int) -> str:
    """Estima a secção do documento com base na posição do chunk."""
    if total_chunks == 0:
        return 'desconhecido'
    ratio = posicao_chunk / total_chunks
    if ratio < 0.15:
        return 'introducao'
    elif ratio < 0.85:
        return 'desenvolvimento'
    else:
        return 'conclusao'
