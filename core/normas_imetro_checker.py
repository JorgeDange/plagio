import json
import logging
import requests
import re
from core.normas_imetro_prompt import PROMPT_SISTEMA_IMETRO, build_normas_payload

logger = logging.getLogger(__name__)

class UnimetroInspector:
    def __init__(self, provider: str, model: str, api_key: str, ollama_url: str):
        self.provider = provider.lower()
        self.model = model
        self.api_key = api_key
        self.ollama_url = ollama_url.rstrip("/")

    def analisar_tfc(self, texto: str) -> dict:
        prompt = f"Analise o seguinte TFC de acordo com as normas do IMETRO:\n\n{texto[:50000]}"
        
        try:
            if self.provider == "ollama":
                resp_json = self._call_ollama(prompt)
            elif self.provider == "openai":
                resp_json = self._call_openai(prompt)
            elif self.provider == "anthropic":
                resp_json = self._call_anthropic(prompt)
            else:
                raise ValueError(f"Provedor não suportado: {self.provider}")
                
            return self._parse_json(resp_json)
        except Exception as e:
            logger.error(f"Erro no Unimetro Inspector: {e}")
            return {
                "classificacao_global": "NÃO CONFORME",
                "pontuacao": 0,
                "infracoes": [{"codigo": "ERR", "gravidade": "Bloqueante", "descricao": str(e)}],
                "elementos_estruturais": {},
                "metodologia": {},
                "recomendacoes": []
            }

    def _parse_json(self, response_text: str) -> dict:
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except json.JSONDecodeError:
                    pass
            raise ValueError(f"A resposta do LLM não é um JSON válido: {response_text}")

    def _call_ollama(self, prompt: str) -> str:
        is_remote = "ollama.com" in self.ollama_url or bool(self.api_key)

        if is_remote:
            url = f"{self.ollama_url}/api/chat"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": PROMPT_SISTEMA_IMETRO},
                    {"role": "user", "content": prompt}
                ],
                "stream": False
            }
            res = requests.post(url, headers=headers, json=payload, timeout=120)
            res.raise_for_status()
            return res.json()["message"]["content"]
        else:
            url = f"{self.ollama_url}/api/generate"
            payload = {
                "model": self.model,
                "system": PROMPT_SISTEMA_IMETRO,
                "prompt": prompt,
                "stream": False,
                "format": "json"
            }
            res = requests.post(url, json=payload, timeout=120)
            res.raise_for_status()
            return res.json().get("response", "{}")

    def _call_openai(self, prompt: str) -> str:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": PROMPT_SISTEMA_IMETRO}, {"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"},
            "temperature": 0.0
        }
        res = requests.post(url, headers=headers, json=payload, timeout=60)
        res.raise_for_status()
        return res.json()["choices"][0]["message"]["content"]

    def _call_anthropic(self, prompt: str) -> str:
        url = "https://api.anthropic.com/v1/messages"
        headers = {"x-api-key": self.api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"}
        payload = {
            "model": self.model,
            "system": PROMPT_SISTEMA_IMETRO,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1024,
            "temperature": 0.0
        }
        res = requests.post(url, headers=headers, json=payload, timeout=60)
        res.raise_for_status()
        return res.json()["content"][0]["text"]


def get_llm_config(db_path: str) -> dict:
    """Lê as configurações de IA da tabela `configuracoes` via MySQL."""
    try:
        from app.database.db import get_db
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "SELECT chave, valor FROM configuracoes WHERE chave LIKE 'LLM_%' OR chave = 'OLLAMA_URL'"
        )
        cols = [d[0] for d in cur.description]
        rows = [dict(zip(cols, row)) for row in cur.fetchall()]
        cur.close()
        return {r["chave"]: r["valor"] for r in rows}
    except Exception as e:
        logger.error("Erro ao ler config IA da BD: %s", e)
        return {}


def verificar_normas_imetro(
    texto_extraido: str,
    titulo: str,
    autores: str,
    curso: str,
    orientador: str,
    ano: str,
    num_paginas: int,
    formato_ficheiro: str,
    config_db: dict,
) -> dict:
    """Executa a verificação de normas IMETRO via IA (UnimetroInspector)."""
    if config_db.get("LLM_ENABLED", "false").lower() != "true":
        return {"erro": "IA não está ativa no sistema. Ative em IA → Configurações."}

    provider = config_db.get("LLM_PROVIDER", "openai")
    model = config_db.get("LLM_MODEL", "")
    api_key = config_db.get("LLM_API_KEY", "")
    ollama_url = config_db.get("OLLAMA_URL", "http://localhost:11434")

    if not model:
        return {"erro": "Modelo LLM não configurado. Configure em IA → Configurações."}

    if provider != "ollama" and not api_key:
        return {"erro": f"API Key não configurada para o provedor '{provider}'. Configure em IA → Configurações."}

    try:
        payload = build_normas_payload(
            titulo=titulo,
            autores=autores,
            curso=curso,
            orientador=orientador,
            ano=ano,
            num_paginas=str(num_paginas),
            formato_ficheiro=formato_ficheiro,
            texto_extraido=texto_extraido,
        )

        inspector = UnimetroInspector(
            provider=provider,
            model=model,
            api_key=api_key,
            ollama_url=ollama_url,
        )

        resultado_ia = inspector.analisar_tfc(json.dumps(payload, ensure_ascii=False))

        score = resultado_ia.get("pontuacao", 0)
        return {
            "classificacao": resultado_ia.get("classificacao_global", "NÃO CONFORME"),
            "pontuacao_total": score,
            "categorias": [
                {"nome": "Estrutura",      "pontuacao": round(score * 0.25), "max": 25},
                {"nome": "Apresentação",   "pontuacao": round(score * 0.20), "max": 20},
                {"nome": "Citações",       "pontuacao": round(score * 0.20), "max": 20},
                {"nome": "Bibliografia",   "pontuacao": round(score * 0.20), "max": 20},
                {"nome": "Metodologia",    "pontuacao": round(score * 0.15), "max": 15},
            ],
            "infracoes": resultado_ia.get("infracoes", []),
            "recomendacoes": resultado_ia.get("recomendacoes", []),
        }
    except Exception as e:
        logger.error("Erro na verificação de normas por IA: %s", e)
        return {"erro": str(e)}
