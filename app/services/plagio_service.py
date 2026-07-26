# Sistema de Deteccao de Plagio — Servico de Deteccao
# Logica de indexacao e verificacao de plagio.
# Usa embeddings via OpenRouter API + MySQL (core/embeddings.py + app/database/db.py).

import numpy as np
from flask import current_app
from core.ingestor import extrair, limpar_texto
from core.chunker import dividir_em_chunks
from core.embeddings import gerar_embedding, gerar_embeddings_lote, EmbeddingServiceError
from app.database.db import get_db, guardar_embedding_chunk, listar_embeddings_por_tipo
from core.detector import cosine_similarity

# Tamanho de lote para encode (evitar excesso de RAM)
BATCH_SIZE: int = 16


def classificar_nivel(pct: float) -> str:
    """
    Classifica a percentagem de plágio num nivel.

    Args:
        pct: Percentagem de plágio (0-100).

    Returns:
        'Baixo' (<10%), 'Moderado' (10-29.9%) ou 'Alto' (>=30%).
    """
    if pct < 10.0:
        return 'Baixo'
    elif pct < 30.0:
        return 'Moderado'
    else:
        return 'Alto'


def indexar_monografia(caminho: str, titulo: str, autor: str,
                       curso: str, monografia_id: str, curso_id: str = "", ano: str = "") -> dict:
    """
    Indexa uma monografia armazenando chunks e embeddings no MySQL.

    Fluxo: extrair texto -> limpar -> dividir em chunks -> gerar embeddings -> armazenar

    Args:
        caminho: Caminho absoluto para o ficheiro (PDF, DOCX ou TXT).
        titulo: Titulo da monografia.
        autor: Nome do autor.
        curso: Curso associado.
        monografia_id: ID unico para identificacao.
        curso_id: ID do curso associado.
        ano: Ano da monografia.

    Returns:
        Dicionario com sucesso, num_chunks, chroma_id e erro (se houver).
    """
    try:
        # Extrair e limpar texto do documento
        texto_bruto: str = extrair(caminho)
        texto_limpo: str = limpar_texto(texto_bruto)

        if not texto_limpo.strip():
            return {
                'sucesso': False,
                'num_chunks': 0,
                'chroma_id': monografia_id,
                'erro': 'Documento sem conteudo legivel.'
            }

        # Dividir em chunks com parametros da configuracao
        tamanho: int = current_app.config.get('CHUNK_SIZE', 200)
        overlap: int = current_app.config.get('CHUNK_OVERLAP', 50)
        chunks: list[str] = dividir_em_chunks(texto_limpo, tamanho=tamanho, overlap=overlap)
        total_chunks: int = len(chunks)

        if total_chunks == 0:
            return {
                'sucesso': False,
                'num_chunks': 0,
                'chroma_id': monografia_id,
                'erro': 'Nenhum chunk gerado a partir do documento.'
            }

        # Converter monografia_id para inteiro para MySQL
        tcc_id_int: int = int(monografia_id) if monografia_id.isdigit() else hash(monografia_id) % 10000

        chunks_indexados: int = 0

        for i in range(0, total_chunks, BATCH_SIZE):
            lote: list[str] = chunks[i:i + BATCH_SIZE]

            # Gerar embeddings em lote via OpenRouter API
            embeddings = gerar_embeddings_lote(lote)

            n: int = len(lote)
            for j in range(n):
                chunk_texto = lote[j]
                embedding = embeddings[j]

                # Armazenar no MySQL
                guardar_embedding_chunk(
                    tcc_id=tcc_id_int,
                    tipo='valido',
                    chunk_texto=chunk_texto,
                    vector=embedding
                )

                chunks_indexados += 1

        return {
            'sucesso': True,
            'num_chunks': chunks_indexados,
            'chroma_id': monografia_id,
            'erro': ''
        }

    except EmbeddingServiceError as e:
        return {
            'sucesso': False,
            'num_chunks': 0,
            'chroma_id': monografia_id,
            'erro': f'Falha ao gerar embeddings: {e}'
        }
    except Exception as e:
        return {
            'sucesso': False,
            'num_chunks': 0,
            'chroma_id': monografia_id,
            'erro': str(e)
        }


def verificar_monografia(caminho: str, excluir_id: str | None = None, curso: str | None = None, limiar: float | None = None) -> dict:
    """
    Verifica um documento contra a base de monografias indexadas.

    Fluxo: extrair -> limpar -> dividir -> gerar embeddings -> comparar com base -> calcular plagio

    Args:
        caminho: Caminho absoluto para o ficheiro a verificar.
        excluir_id: ID de monografia a excluir da comparacao (auto-comparacao).
        curso: Curso para filtrar (opcional, para referencia futura).
        limiar: Limiar de similaridade (opcional).

    Returns:
        Dicionario completo com resultados da verificacao.
    """
    try:
        limiar_usado: float = limiar if limiar is not None else current_app.config.get('LIMIAR_PLAGIO', 0.85)

        # Carregar todos os embeddings validos do MySQL
        validos = listar_embeddings_por_tipo('valido')

        if not validos:
            return {
                'total_chunks': 0,
                'chunks_suspeitos': 0,
                'percentagem_plagio': 0.0,
                'nivel': 'Baixo',
                'detalhes': [],
                'aviso': 'Base de dados vazia — nenhuma monografia indexada para comparacao.'
            }

        # Preparar dados para comparacao
        vetores_validos: list[list[float]] = [item['vector'] for item in validos]
        textos_validos: list[str] = [item['chunk_texto'] for item in validos]
        tcc_ids_validos: list[int] = [item['tcc_id'] for item in validos]

        # Extrair e processar texto
        texto_bruto: str = extrair(caminho)
        texto_limpo: str = limpar_texto(texto_bruto)
        tamanho: int = current_app.config.get('CHUNK_SIZE', 200)
        overlap: int = current_app.config.get('CHUNK_OVERLAP', 50)
        chunks: list[str] = dividir_em_chunks(texto_limpo, tamanho=tamanho, overlap=overlap)
        total_chunks: int = len(chunks)

        if total_chunks == 0:
            return {
                'total_chunks': 0,
                'chunks_suspeitos': 0,
                'percentagem_plagio': 0.0,
                'nivel': 'Baixo',
                'detalhes': []
            }

        detalhes: list[dict] = []
        chunks_suspeitos: int = 0

        for i in range(0, total_chunks, BATCH_SIZE):
            lote: list[str] = chunks[i:i + BATCH_SIZE]

            # Gerar embeddings do lote via OpenRouter API
            try:
                embeddings_lote = gerar_embeddings_lote(lote)
            except EmbeddingServiceError as e:
                print(f"[ERRO] Falha ao gerar embeddings para lote: {e}")
                continue

            for j in range(len(lote)):
                chunk_suspeito = lote[j]
                embedding_suspeito = embeddings_lote[j]

                # Encontrar a maior similaridade contra todos os embeddings validos
                max_similaridade: float = 0.0
                melhor_idx: int = -1

                for idx, embedding_valido in enumerate(vetores_validos):
                    simil = cosine_similarity(embedding_suspeito, embedding_valido)
                    if simil > max_similaridade:
                        max_similaridade = simil
                        melhor_idx = idx

                # Verificar se excluir auto-comparacao
                if excluir_id:
                    tcc_id_str = str(tcc_ids_validos[melhor_idx]) if melhor_idx != -1 else ''
                    if tcc_id_str == excluir_id:
                        continue

                if max_similaridade >= limiar_usado and melhor_idx != -1:
                    chunks_suspeitos += 1
                    detalhes.append({
                        'chunk_texto': chunk_suspeito,
                        'texto_similar': textos_validos[melhor_idx],
                        'similaridade': round(max_similaridade, 4),
                        'titulo_origem': f'TCC ID {tcc_ids_validos[melhor_idx]}',
                        'autor_origem': 'Desconhecido',
                        'curso_origem': 'Desconhecido',
                        'chroma_id_origem': str(tcc_ids_validos[melhor_idx]),
                        'posicao': i + j
                    })

        # Calcular percentagem e nivel
        percentagem: float = round(
            (chunks_suspeitos / total_chunks) * 100, 1
        ) if total_chunks > 0 else 0.0
        nivel: str = classificar_nivel(percentagem)

        # Ordenar detalhes por similaridade decrescente
        detalhes.sort(key=lambda x: x['similaridade'], reverse=True)

        return {
            'total_chunks': total_chunks,
            'chunks_suspeitos': chunks_suspeitos,
            'percentagem_plagio': percentagem,
            'nivel': nivel,
            'detalhes': detalhes
        }

    except Exception as e:
        return {
            'total_chunks': 0,
            'chunks_suspeitos': 0,
            'percentagem_plagio': 0.0,
            'nivel': 'Baixo',
            'detalhes': [],
            'erro': str(e)
        }


def estado_sistema() -> dict:
    """
    Verifica o estado do sistema (API OpenRouter, MySQL, RAM).

    Returns:
        Dicionario com estado dos componentes.
    """
    resultado: dict = {
        'modelo_ok': False,
        'chroma_ok': False,
        'ram_gb': 0.0,
        'chunks': 0
    }

    try:
        # Verificar API OpenRouter
        import os
        api_key = os.getenv('OPENROUTER_API_KEY', '')
        resultado['modelo_ok'] = bool(api_key)

        # Verificar MySQL e contar chunks
        try:
            db = get_db()
            cursor = db.cursor()
            cursor.execute('SELECT COUNT(*) FROM embeddings_chunks WHERE tipo = %s', ('valido',))
            row = cursor.fetchone()
            resultado['chunks'] = row[0] if row else 0
            resultado['chroma_ok'] = True
            cursor.close()
        except Exception:
            resultado['chroma_ok'] = False

        # Verificar RAM com psutil
        try:
            import psutil
            mem = psutil.virtual_memory()
            resultado['ram_gb'] = round(mem.used / (1024 ** 3), 2)
            resultado['ram_total_gb'] = round(mem.total / (1024 ** 3), 2)
            resultado['ram_pct'] = mem.percent
        except ImportError:
            resultado['ram_gb'] = 0.0

    except Exception:
        pass

    return resultado
