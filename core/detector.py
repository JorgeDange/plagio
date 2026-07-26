# Sistema de Detecção de Plágio — detector.py
# Módulo principal: indexação e verificação de plágio usando embeddings via OpenRouter API + MySQL.

import os
import numpy as np
from core.ingestor import extrair, limpar_texto
from core.chunker import dividir_em_chunks
from core.embeddings import gerar_embedding, gerar_embeddings_lote, EmbeddingServiceError
from app.database.db import guardar_embedding_chunk, listar_embeddings_por_tipo

# Limiar de plágio (mantido existente)
LIMIAR_PLAGIO: float = 0.85


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Calcula a similaridade de cosseno entre dois vetores.
    """
    a = np.array(vec_a)
    b = np.array(vec_b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def indexar(caminho: str, monografia_id: str, titulo: str, autor: str, curso: str = "", curso_id: str = "", ano: str = "") -> int:
    """
    Indexa um documento armazenando seus chunks e embeddings no MySQL.
    Retorna nº de chunks indexados.
    """
    print(f"\n{'='*60}")
    print(f"A indexar: {titulo} | Autor: {autor} | ID: {monografia_id}")
    print(f"{'='*60}")

    texto_bruto: str = extrair(caminho)
    texto_limpo: str = limpar_texto(texto_bruto)
    print(f"Texto extraído: {len(texto_limpo)} caracteres")

    chunks: list[str] = dividir_em_chunks(texto_limpo)
    total_chunks: int = len(chunks)
    print(f"Chunks gerados: {total_chunks}")

    if total_chunks == 0:
        print("AVISO: Documento sem conteúdo.")
        return 0

    # Determinar se é TCC válido ou suspeito com base na existência no banco
    # Como não temos acesso direto aqui, vamos assumir que chamamos esta função
    # a partir do contexto adequado (valido ou suspeito)
    # Na prática, o tipo será determinado pelo chamador (verificacoes/routes.py)
    # Por agora, vamos deixar como parâmetro ou tentar inferir
    # Na atual arquitetura, indexar é chamado para TCCs válidos durante upload
    # Vamos assumir que é 'valido' para indexação inicial
    tipo = 'valido'  # Isto pode ser ajustado conforme o contexto de chamada

    BATCH_SIZE: int = 16
    chunks_indexados: int = 0

    try:
        for i in range(0, total_chunks, BATCH_SIZE):
            lote: list[str] = chunks[i:i + BATCH_SIZE]
            n: int = len(lote)

            # Gerar embeddings em lote para eficiência
            embeddings = gerar_embeddings_lote(lote)

            for j in range(n):
                chunk_texto = lote[j]
                embedding = embeddings[j]
                chunk_id = f"{monografia_id}_chunk_{i+j}"
                
                # Armazenar no MySQL
                guardar_embedding_chunk(
                    tcc_id=int(monografia_id) if monografia_id.isdigit() else hash(monografia_id) % 10000,
                    tipo=tipo,
                    chunk_texto=chunk_texto,
                    vector=embedding
                )
                
                chunks_indexados += 1
                print(f"  A indexar chunk {chunks_indexados}/{total_chunks}...")

        print(f"Indexação concluída: {chunks_indexados} chunks.\n")
        return chunks_indexados
    except EmbeddingServiceError as e:
        print(f"[ERRO] Falha ao gerar embeddings: {e}")
        return 0
    except Exception as e:
        print(f"[ERRO] Erro inesperado durante indexação: {e}")
        return 0


def verificar(caminho: str, excluir_id: str | None = None, curso: str | None = None) -> dict:
    """
    Verifica um documento contra a base de TCCs válidos armazenados no MySQL.
    Retorna dict com resultados.
    """
    print(f"\n{'='*60}")
    print(f"A verificar: {caminho}")
    print(f"{'='*60}")

    texto_bruto: str = extrair(caminho)
    texto_limpo: str = limpar_texto(texto_bruto)
    chunks: list[str] = dividir_em_chunks(texto_limpo)
    total_chunks: int = len(chunks)
    print(f"Chunks a verificar: {total_chunks}")

    if total_chunks == 0:
        return {"total_chunks": 0, "chunks_suspeitos": 0,
                "percentagem_plagio": 0.0, "nivel": "Baixo", "detalhes": []}

    try:
        # Buscar todos os chunks válidos do MySQL
        validos = listar_embeddings_por_tipo('valido')
        if not validos:
            print("AVISO: Base de dados de TCCs válidos vazia.")
            return {"total_chunks": 0, "chunks_suspeitos": 0,
                    "percentagem_plagio": 0.0, "nivel": "Baixo", "detalhes": []}

        # Preparar dados para comparação
        vetores_validos = [item['vector'] for item in validos]
        textos_validos = [item['chunk_texto'] for item in validos]
        tcc_ids_validos = [item['tcc_id'] for item in validos]

        detalhes: list[dict] = []
        chunks_suspeitos: int = 0
        BATCH_SIZE: int = 16

        for i in range(0, total_chunks, BATCH_SIZE):
            lote: list[str] = chunks[i:i + BATCH_SIZE]
            
            # Gerar embeddings para o lote de suspeitos
            try:
                embeddings_lote = gerar_embeddings_lote(lote)
            except EmbeddingServiceError as e:
                print(f"[ERRO] Falha ao gerar embeddings para lote: {e}")
                continue

            for j in range(len(lote)):
                chunk_suspeito = lote[j]
                embedding_suspeito = embeddings_lote[j]
                posicao_global = i + j

                # Comparar com todos os vetores válidos
                max_similaridade = 0.0
                melhor_indice = -1

                for idx, embedding_valido in enumerate(vetores_validos):
                    simil = cosine_similarity(embedding_suspeito, embedding_valido)
                    if simil > max_similaridade:
                        max_similaridade = simil
                        melhor_indice = idx

                # Verificar se超过了阈值
                if max_similaridade >= LIMIAR_PLAGIO and melhor_indice != -1:
                    chunks_suspeitos += 1
                    detalhes.append({
                        "chunk_texto": chunk_suspeito,
                        "texto_similar": textos_validos[melhor_indice],
                        "similaridade": round(max_similaridade, 4),
                        "titulo_origem": f"TCC ID {tcc_ids_validos[melhor_indice]}",
                        "autor_origem": "Desconhecido",
                        "curso_origem": "Desconhecido",
                        "chroma_id_origem": str(tcc_ids_validos[melhor_indice]),
                        "posicao": posicao_global,
                        "fonte_origem": "local",
                        "url_fonte": None
                    })

                if (posicao_global + 1) % 10 == 0 or posicao_global == total_chunks - 1:
                    print(f"  A verificar chunk {posicao_global+1}/{total_chunks}...")

        percentagem: float = round((chunks_suspeitos / total_chunks) * 100, 1) if total_chunks > 0 else 0.0
        nivel: str = classificar_nivel(percentagem)
        detalhes.sort(key=lambda x: x["similaridade"], reverse=True)

        print(f"\nResultado: {percentagem}% de plágio ({nivel})")
        print(f"Chunks suspeitos: {chunks_suspeitos}/{total_chunks}\n")

        return {
            "total_chunks": total_chunks,
            "chunks_suspeitos": chunks_suspeitos,
            "percentagem_plagio": percentagem,
            "nivel": nivel,
            "detalhes": detalhes
        }
    except Exception as e:
        print(f"[ERRO] Erro durante verificação: {e}")
        return {"total_chunks": total_chunks, "chunks_suspeitos": 0,
                "percentagem_plagio": 0.0, "nivel": "Erro", "detalhes": []}


def classificar_nivel(pct: float) -> str:
    """Classifica: <10% Baixo, <30% Moderado, >=30% Alto."""
    if pct < 10.0:
        return "Baixo"
    elif pct < 30.0:
        return "Moderado"
    else:
        return "Alto"