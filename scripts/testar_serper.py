"""Script de verificacao da integracao Serper (Google Search)."""
import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv
load_dotenv()

from core.pesquisa_externa import pesquisar_serper

def main():
    api_key = os.getenv("SERPER_API_KEY", "")
    if not api_key:
        print("ERRO: SERPER_API_KEY nao configurada no .env")
        sys.exit(1)
    
    query = "plagio academico deteccao"
    print(f"[Teste] Query: {query}")
    print(f"[Teste] API Key: ...{api_key[-6:]}")
    
    print("\n--- Teste 1: Pesquisa simples ---")
    inicio = time.time()
    resultados = pesquisar_serper(query, max_resultados=3)
    duracao = time.time() - inicio
    
    print(f"Resultados: {len(resultados)}")
    for i, r in enumerate(resultados, 1):
        print(f"\n  {i}. {r['titulo']}")
        print(f"     URL: {r['url']}")
        print(f"     Fonte: {r['fonte']}")
        if r['resumo']:
            print(f"     Snippet: {r['resumo'][:100]}...")
    
    print(f"\nTempo: {duracao:.1f}s")
    
    if resultados:
        print("\n[OK] Teste 1 passou!")
    else:
        print("\n[FALHOU] Nenhum resultado retornado.")
        sys.exit(1)
    
    print("\n--- Teste 2: Query vazia ---")
    resultados_vazio = pesquisar_serper("")
    print(f"Resultados: {len(resultados_vazio)} (esperado: 0)")
    if len(resultados_vazio) == 0:
        print("[OK] Teste 2 passou!")
    else:
        print("[FALHOU]")
        sys.exit(1)
    
    print("\n--- Teste 3: Formato de retorno ---")
    if resultados:
        r = resultados[0]
        campos_esperados = {"fonte", "titulo", "autores", "ano", "doi", "url", "resumo"}
        campos_faltam = campos_esperados - set(r.keys())
        if not campos_faltam:
            print("[OK] Teste 3 passou!")
        else:
            print(f"[FALHOU] Campos em falta: {campos_faltam}")
            sys.exit(1)
    
    print("\nTodos os testes passaram!")

if __name__ == "__main__":
    main()
