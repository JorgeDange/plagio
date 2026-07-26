# core/embeddings.py
# Módulo centralizado para geração de embeddings via OpenRouter API (qwen3-embedding-8b).
# Funciona 100% via API HTTP, sem dependência de modelos locais.

import os
import json
import time
import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Logger
logger = logging.getLogger(__name__)

# Variáveis de ambiente
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_EMBEDDING_MODEL = os.getenv("OPENROUTER_EMBEDDING_MODEL", "qwen/qwen3-embedding-8b")
OPENROUTER_EMBEDDING_URL = os.getenv("OPENROUTER_EMBEDDING_URL", "https://openrouter.ai/api/v1/embeddings")
OPENROUTER_TIMEOUT_SECONDS = int(os.getenv("OPENROUTER_TIMEOUT_SECONDS", "30"))
OPENROUTER_MAX_RETRIES = int(os.getenv("OPENROUTER_MAX_RETRIES", "3"))

class EmbeddingServiceError(Exception):
    """Exceção levantada quando o serviço de embeddings falha após todas as tentativas."""
    pass

def _get_session():
    """
    Cria uma sessão requests com retry automático para erros de rede e 5xx.
    Não faz retry em 401, 403, 429 (estes são tratados imediatamente).
    """
    session = requests.Session()
    retry_strategy = Retry(
        total=OPENROUTER_MAX_RETRIES,
        backoff_factor=1,  # fator de espera: 1s, 2s, 4s, ...
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["POST"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session

def _make_request(payload: dict) -> dict:
    """
    Faz a requisição HTTP para o OpenRouter API com retry e tratamento de erros.
    """
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    session = _get_session()
    try:
        response = session.post(
            OPENROUTER_EMBEDDING_URL,
            headers=headers,
            json=payload,
            timeout=OPENROUTER_TIMEOUT_SECONDS
        )
        # Se for erro de cliente (4xx) que não devemos retryar, levanta exceção imediatamente
        if response.status_code in (401, 403, 429):
            logger.error(f"OpenRouter API erro HTTP {response.status_code}: {response.text[:500]}")
            response.raise_for_status()
        # Para outros 4xx e 5xx, o retry strategy já tratou os 5xx, mas 4xx não são retried
        # Vamos levantar para que o retry trate os 5xx e nós tratemos os 4xx abaixo
        response.raise_for_status()
        # Verificar se a resposta é JSON antes de tentar fazer parse
        content_type = response.headers.get("content-type", "")
        if "application/json" not in content_type:
            logger.error(f"OpenRouter API respondeu com content-type '{content_type}': {response.text[:500]}")
            raise EmbeddingServiceError(
                f"OpenRouter API respondeu com formato inválido ({content_type}). "
                f"Verifique se a chave OPENROUTER_API_KEY é válida."
            )
        return response.json()
    except requests.exceptions.RequestException as e:
        # Se for um erro de conexão, timeout, etc., o retry já foi aplicado pelo adapter
        # Se ainda assim falhou, levanta exceção
        logger.warning(f"Requisição falhou após {OPENROUTER_MAX_RETRIES} tentativas: {e}")
        raise
    finally:
        session.close()

def gerar_embedding(texto: str) -> list[float]:
    """
    Gera o embedding (vector) para um texto usando a API do OpenRouter.
    Args:
        texto: Texto para codificar.
    Returns:
        Lista com os valores do vector de embedding.
    Raises:
        EmbeddingServiceError: Se todas as tentativas falharem.
    """
    if not OPENROUTER_API_KEY:
        raise EmbeddingServiceError("OPENROUTER_API_KEY não configurada no ambiente.")
    
    # Limitar texto a 8000 caracteres para evitar payloads excessivamente grandes
    texto_limitado = texto[:8000] if texto else ""
    
    payload = {
        "model": OPENROUTER_EMBEDDING_MODEL,
        "input": texto_limitado
    }
    
    try:
        response_json = _make_request(payload)
        # Extrair o embedding
        embedding = response_json["data"][0]["embedding"]
        # Log de uso de tokens, se disponível
        usage = response_json.get("usage")
        if usage:
            tokens = usage.get("total_tokens")
            if tokens is not None:
                logger.info(f"Embedding gerado. Tokens usados: {tokens}")
        return embedding
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        logger.error(f"Resposta inválida da API de embeddings: {e}")
        raise EmbeddingServiceError(f"Resposta inválida da API: {e}")
    except EmbeddingServiceError:
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"Falha na chamada à API de embeddings após {OPENROUTER_MAX_RETRIES} tentativas: {e}")
        raise EmbeddingServiceError(f"Falha na chamada à API de embeddings: {e}")

def gerar_embeddings_lote(textos: list[str]) -> list[list[float]]:
    """
    Gera embeddings para uma lista de textos usando a API do OpenRouter.
    Args:
        textos: Lista de textos para codificar.
    Returns:
        Lista de embeddings, na mesma ordem dos textos de entrada.
    Raises:
        EmbeddingServiceError: Se todas as tentativas falharem.
    """
    if not OPENROUTER_API_KEY:
        raise EmbeddingServiceError("OPENROUTER_API_KEY não configurada no ambiente.")
    
    if not textos:
        return []
    
    # Limitar cada texto a 8000 caracteres
    textos_limitados = [t[:8000] if t else "" for t in textos]
    
    payload = {
        "model": OPENROUTER_EMBEDDING_MODEL,
        "input": textos_limitados
    }
    
    try:
        response_json = _make_request(payload)
        # Extrair embeddings na mesma ordem
        embeddings = [item["embedding"] for item in response_json["data"]]
        # Log de uso de tokens, se disponível
        usage = response_json.get("usage")
        if usage:
            tokens = usage.get("total_tokens")
            if tokens is not None:
                logger.info(f"Embeddings em lote gerados. Tokens usados: {tokens} para {len(textos)} textos.")
        return embeddings
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        logger.error(f"Resposta inválida da API de embeddings em lote: {e}")
        raise EmbeddingServiceError(f"Resposta inválida da API: {e}")
    except EmbeddingServiceError:
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"Falha na chamada à API de embeddings em lote após {OPENROUTER_MAX_RETRIES} tentativas: {e}")
        raise EmbeddingServiceError(f"Falha na chamada à API de embeddings em lote: {e}")

# Retrocompatibilidade: modelo = None (antigo LaBSE local removido)
modelo = None
