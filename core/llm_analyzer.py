"""
core/llm_analyzer.py
======================
Módulo responsável por conectar o IMETRO TFC v3 a modelos LLM
para a Fase 2 de análise de plágio (Unimetro Analista).
Suporta Ollama, OpenAI e Anthropic.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
import json
import time
import requests
import logging
import re

logger = logging.getLogger(__name__)

@dataclass
class ChunkParaAnalise:
    chunk_suspeito_id: int
    texto_suspeito: str
    texto_original: str
    tcc_original_id: int
    tcc_original_titulo: str
    score_labse: float

@dataclass
class ResultadoLLM:
    chunk_suspeito_id: int
    plagio: bool
    nivel: str  # "baixo", "moderado", "alto", "critico"
    tipo: str
    similaridade_llm: int
    score_labse: float
    justificativa: str
    modelo_usado: str
    tempo_ms: int
    erro: str = ""

def resultados_para_dict(resultados: list[ResultadoLLM]) -> list[dict]:
    """Converte uma lista de objectos ResultadoLLM em dicionários para JSON."""
    return [asdict(r) for r in resultados]

class LLMAnalyzer:
    """
    Classe responsável por orquestrar a análise Fase 2.
    O Unimetro Analista recebe chunks de texto e valida o grau e o tipo de plágio usando LLMs.
    """
    def __init__(self, provider: str, model: str, api_key: str, ollama_url: str):
        self.provider = provider.lower()
        self.model = model
        self.api_key = api_key
        self.ollama_url = ollama_url.rstrip("/")

        self.system_prompt = (
            "És o 'Unimetro Analista', um sistema perito em revisão de plágio da Universidade IMETRO em Angola. "
            "A tua tarefa é comparar dois textos (um suspeito e um original) e determinar de forma precisa e técnica se houve plágio "
            "(ex: cópia directa, mosaico, paráfrase ou tradução disfarçada). "
            "Deves avaliar rigorosamente: "
            "1. 'plagio': boolean (true ou false) indicando se é plágio.\n"
            "2. 'nivel': gravidade do plágio, DEVE ser estritamente uma destas strings: 'baixo', 'moderado', 'alto', 'critico'. "
            "Se não for plágio, usa 'baixo'.\n"
            "3. 'tipo': classificação do plágio (ex: 'Cópia Directa', 'Paráfrase', 'Mosaico', 'Sem Plágio').\n"
            "4. 'similaridade_llm': valor inteiro de 0 a 100 indicando a tua confiança/percentagem de sobreposição semântica.\n"
            "5. 'justificativa': explicação rigorosa em português baseada em normas académicas.\n\n"
            "Responde ESTRITAMENTE em formato JSON com essas chaves e nada mais."
        )

    def analisar_verificacao(self, chunks: list[ChunkParaAnalise]) -> list[ResultadoLLM]:
        """Processa uma lista de chunks e devolve os respectivos resultados."""
        resultados = []
        for chunk in chunks:
            resultados.append(self.analisar_chunk_unico(chunk))
        return resultados

    def analisar_chunk_unico(self, chunk: ChunkParaAnalise) -> ResultadoLLM:
        """Analisa um chunk singular submetendo ao LLM e realizando parse da resposta."""
        start_time = time.time()
        resultado = ResultadoLLM(
            chunk_suspeito_id=chunk.chunk_suspeito_id,
            plagio=False,
            nivel="baixo",
            tipo="",
            similaridade_llm=0,
            score_labse=chunk.score_labse,
            justificativa="",
            modelo_usado=f"{self.provider}/{self.model}",
            tempo_ms=0,
            erro=""
        )

        user_prompt = (
            f"Texto Original (Autor): \"{chunk.texto_original}\"\n\n"
            f"Texto Suspeito (Aluno): \"{chunk.texto_suspeito}\"\n\n"
            "Analisa o par acima conforme as tuas directrizes."
        )

        try:
            if self.provider == "ollama":
                resp_json = self._call_ollama(user_prompt)
            elif self.provider == "openai":
                resp_json = self._call_openai(user_prompt)
            elif self.provider == "anthropic":
                resp_json = self._call_anthropic(user_prompt)
            else:
                raise ValueError(f"Provedor LLM não suportado: {self.provider}")
            
            parsed = self._parse_json(resp_json)
            
            resultado.plagio = bool(parsed.get("plagio", False))
            
            nivel_extraido = str(parsed.get("nivel", "baixo")).lower().strip()
            if nivel_extraido in ["baixo", "moderado", "alto", "critico"]:
                resultado.nivel = nivel_extraido
            else:
                resultado.nivel = "baixo"
                
            resultado.tipo = str(parsed.get("tipo", ""))
            
            try:
                resultado.similaridade_llm = int(parsed.get("similaridade_llm", 0))
            except ValueError:
                resultado.similaridade_llm = 0
                
            resultado.justificativa = str(parsed.get("justificativa", ""))

        except Exception as e:
            logger.error(f"Erro na análise do chunk_id {chunk.chunk_suspeito_id} com Unimetro Analista ({self.provider}): {e}")
            resultado.erro = str(e)

        resultado.tempo_ms = int((time.time() - start_time) * 1000)
        return resultado

    def _parse_json(self, response_text: str) -> dict:
        """Tenta fazer o parse seguro de uma resposta em string para dicionário JSON."""
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            # Caso a IA inclua backticks Markdown (```json ... ```), ou outro texto, tentamos extrair o JSON
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
                    {"role": "system", "content": self.system_prompt},
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
                "system": self.system_prompt,
                "prompt": prompt,
                "stream": False,
                "format": "json"
            }
            res = requests.post(url, json=payload, timeout=120)
            res.raise_for_status()
            return res.json().get("response", "{}")

    def _call_openai(self, prompt: str) -> str:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.0
        }
        res = requests.post(url, headers=headers, json=payload, timeout=60)
        res.raise_for_status()
        return res.json()["choices"][0]["message"]["content"]

    def _call_anthropic(self, prompt: str) -> str:
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        # Claude expects prompt in JSON response to have instructions inline if JSON format is strictly required,
        # but it usually handles it well if specified in the system prompt.
        payload = {
            "model": self.model,
            "system": self.system_prompt,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 1024,
            "temperature": 0.0
        }
        res = requests.post(url, headers=headers, json=payload, timeout=60)
        res.raise_for_status()
        return res.json()["content"][0]["text"]

def get_analyzer_from_app_config(config_db: dict) -> LLMAnalyzer | None:
    """Instancia o LLMAnalyzer baseado no dicionário de configurações da base de dados."""
    if config_db.get("LLM_ENABLED", "false").lower() != "true":
        return None
    
    provider = config_db.get("LLM_PROVIDER", "ollama")
    model = config_db.get("LLM_MODEL", "unimetro_analista")
    api_key = config_db.get("LLM_API_KEY", "")
    ollama_url = config_db.get("OLLAMA_URL", "http://localhost:11434")
    
    return LLMAnalyzer(provider=provider, model=model, api_key=api_key, ollama_url=ollama_url)
