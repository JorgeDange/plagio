#!/usr/bin/env python3
"""
Script de verificacao manual para testar a integracao com OpenRouter API (qwen3-embedding-8b).
Le as variaveis de ambiente, chama gerar_embedding e verifica a resposta.
"""

import os
import time
import sys
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    print("=== Teste de Integracao OpenRouter Embeddings ===\n")

    load_dotenv()

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key or api_key == "coloque_a_chave_aqui":
        print("[ERRO] OPENROUTER_API_KEY nao configurada ou usando valor de exemplo.")
        print("Por favor, configure uma chave valida no arquivo .env")
        return 1

    print("API Key configurada: " + api_key[:10] + "...")
    print("Modelo: " + os.getenv("OPENROUTER_EMBEDDING_MODEL", "qwen/qwen3-embedding-8b"))
    print("URL: " + os.getenv("OPENROUTER_EMBEDDING_URL", "https://openrouter.ai/api/v1/embeddings"))
    print()

    try:
        from core.embeddings import gerar_embedding, gerar_embeddings_lote, EmbeddingServiceError

        # Teste 1: Embedding simples
        print("--- Teste 1: Embedding simples ---")
        texto_teste = "Texto de teste em portugues para verificar embeddings via OpenRouter"
        inicio = time.time()
        try:
            embedding = gerar_embedding(texto_teste)
            tempo = time.time() - inicio

            print("[OK] Embedding gerado com sucesso!")
            print("  Dimensao: %d" % len(embedding))
            print("  Tempo de resposta: %.2fs" % tempo)
            print("  Primeiros 5 valores: %s" % str(embedding[:5]))
            print()
        except EmbeddingServiceError as e:
            print("[ERRO] Erro ao gerar embedding: %s" % str(e))
            return 1
        except Exception as e:
            print("[ERRO] Erro inesperado: %s" % str(e))
            return 1

        # Teste 2: Embedding em lote
        print("--- Teste 2: Embedding em lote ---")
        textos_teste = [
            "Primeiro texto para teste",
            "Segundo texto para teste",
            "Terceiro texto para teste em portugues"
        ]
        inicio = time.time()
        try:
            embeddings_lote = gerar_embeddings_lote(textos_teste)
            tempo = time.time() - inicio

            print("[OK] Embeddings em lote gerados com sucesso!")
            print("  Numero de embeddings: %d" % len(embeddings_lote))
            print("  Dimensao de cada embedding: %d" % (len(embeddings_lote[0]) if embeddings_lote else 0))
            print("  Tempo de resposta: %.2fs" % tempo)
            print()

            if embeddings_lote:
                dim_list = [len(e) for e in embeddings_lote]
                if len(set(dim_list)) == 1:
                    print("[OK] Todos os embeddings tem a mesma dimensao: %d" % dim_list[0])
                else:
                    print("[ERRO] Dimensoes inconsistentes: %s" % str(dim_list))
                    return 1
            print()
        except EmbeddingServiceError as e:
            print("[ERRO] Erro ao gerar embeddings em lote: %s" % str(e))
            return 1
        except Exception as e:
            print("[ERRO] Erro inesperado no lote: %s" % str(e))
            return 1

        # Teste 3: Verificar consistencia
        print("--- Teste 3: Consistencia ---")
        inicio = time.time()
        embedding1 = gerar_embedding(texto_teste)
        tempo1 = time.time() - inicio

        inicio = time.time()
        embedding2 = gerar_embedding(texto_teste)
        tempo2 = time.time() - inicio

        if embedding1 == embedding2:
            print("[OK] Embeddings consistentes para o mesmo texto")
            print("  Tempo primeira chamada: %.2fs" % tempo1)
            print("  Tempo segunda chamada: %.2fs" % tempo2)
        else:
            print("[ERRO] Embeddings inconsistentes para o mesmo texto")
            print("  Primeira chamada: %s..." % str(embedding1[:5]))
            print("  Segunda chamada: %s..." % str(embedding2[:5]))
            return 1
        print()

        print("=== Todos os testes passaram! ===")
        print("A integracao com OpenRouter API esta funcionando corretamente.")
        return 0

    except ImportError as e:
        print("[ERRO] Erro ao importar modulos: %s" % str(e))
        print("Certifique-se de que as dependencias estao instaladas:")
        print("  pip install -r requirements.txt")
        return 1
    except Exception as e:
        print("[ERRO] Erro inesperado durante os testes: %s" % str(e))
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
