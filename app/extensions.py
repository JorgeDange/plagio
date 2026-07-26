# Sistema de Deteccao de Plagio — Extensoes Partilhadas
# Variaveis globais acessiveis por todos os modulos da aplicacao.

import threading

# Lock residual (mantido para compatibilidade com tcc_validos/routes.py)
modelo_lock: threading.Lock = threading.Lock()

# Dicionario de jobs em execucao para rastreamento de progresso
# Formato: {job_id: {"status": str, "progresso": int, "total": int, "resultado": dict | None}}
jobs: dict[str, dict] = {}
