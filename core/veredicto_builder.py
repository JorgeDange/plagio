from __future__ import annotations
import logging
import requests
from app.database.db import (
    obter_dados_relatorio_completo,
    guardar_veredicto_final,
)

logger = logging.getLogger(__name__)


def classificar_score(score: float) -> tuple[str, str | None]:
    if score < 0.30:
        return ('Sem plágio', None)
    elif score < 0.50:
        return ('Suspeita leve', 'Baixa')
    elif score < 0.70:
        return ('Plágio confirmado', 'Média')
    elif score < 0.85:
        return ('Plágio confirmado', 'Alta')
    else:
        return ('Plágio grave', 'Crítica')


_PRIORIDADE_TIPO = {
    'Cópia Directa':       4,
    'Tradução Disfarçada': 3,
    'Mosaico':             2,
    'Paráfrase Excessiva': 1,
}


def determinar_tipo_predominante(chunks: list[dict]) -> str | None:
    contagem: dict[str, int] = {}
    for chunk in chunks:
        tipo = chunk.get('ia_tipo')
        if tipo and tipo in _PRIORIDADE_TIPO:
            contagem[tipo] = contagem.get(tipo, 0) + 1
    if not contagem:
        return None
    return sorted(
        contagem.keys(),
        key=lambda t: (_PRIORIDADE_TIPO[t], contagem[t]),
        reverse=True
    )[0]


def _conclusao_local(dados: dict, classificacao: str, tipo: str | None, gravidade: str | None) -> str:
    vf = dados['verificacao']
    score_pct = round(float(vf.get('percentagem_plagio', vf.get('score_global', 0))))
    n_matches = len(dados['matches'])
    n_chunks  = len(dados['chunks'])
    titulo    = vf.get('titulo', 'Trabalho sem título')
    autor     = vf.get('autor', 'Autor desconhecido')

    if classificacao == 'Sem plágio':
        return (
            f'O trabalho "{titulo}" de {autor} apresentou um índice de similaridade de '
            f'{score_pct}%, abaixo do limiar de alerta. Não foram identificadas correspondências '
            f'significativas com os trabalhos do repositório institucional ou fontes externas. '
            f'O trabalho pode ser considerado original para efeitos de avaliação académica.'
        )

    fontes_desc = ""
    if n_matches > 0:
        top = dados['matches'][0]
        fonte_nome = top.get('titulo_fonte') or top.get('fonte_externa') or 'fonte externa'
        fontes_desc = f' A principal correspondência foi identificada com "{fonte_nome}" ({round(top["similaridade_max"]*100) if top.get("similaridade_max") else round(top.get("contribuicao_pct", 0))}% de similaridade).'

    tipo_desc = f' O tipo de plágio predominante identificado é {tipo}.' if tipo else ''

    return (
        f'O trabalho "{titulo}" de {autor} apresentou um índice de similaridade global de '
        f'{score_pct}%, com {n_matches} fonte(s) com correspondência significativa e '
        f'{n_chunks} trecho(s) suspeito(s) identificados.{fontes_desc}{tipo_desc} '
        f'A gravidade foi classificada como {gravidade or "indeterminada"}. '
        f'Recomenda-se análise detalhada dos trechos antes da decisão final.'
    )


def _call_llm_direct(prompt: str, provider: str, model: str, api_key: str, ollama_url: str) -> str | None:
    try:
        if provider == "ollama" and ollama_url:
            is_remote = "ollama.com" in ollama_url or bool(api_key)
            if is_remote:
                headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
                payload = {"model": model, "messages": [{"role": "user", "content": prompt}], "stream": False}
                res = requests.post(f"{ollama_url}/api/chat", headers=headers, json=payload, timeout=60)
                res.raise_for_status()
                return res.json()["message"]["content"]
            else:
                payload = {"model": model, "prompt": prompt, "stream": False}
                res = requests.post(f"{ollama_url}/api/generate", json=payload, timeout=60)
                res.raise_for_status()
                return res.json().get("response")
        elif provider == "openai" and api_key:
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            payload = {"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": 0.0}
            res = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=60)
            res.raise_for_status()
            return res.json()["choices"][0]["message"]["content"]
        elif provider == "anthropic" and api_key:
            headers = {"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"}
            payload = {"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": 400}
            res = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload, timeout=60)
            res.raise_for_status()
            return res.json()["content"][0]["text"]
    except Exception as e:
        logger.warning(f"Erro ao chamar LLM para conclusão: {e}")
    return None


def _conclusao_llm(dados: dict, classificacao: str, tipo: str | None) -> tuple[str, str] | None:
    try:
        from app.blueprints.analise_ia import _get_config_from_db
        cfg = _get_config_from_db()
        provider   = cfg.get("LLM_PROVIDER", "ollama")
        model      = cfg.get("LLM_MODEL", "")
        api_key    = cfg.get("LLM_API_KEY", "")
        ollama_url = cfg.get("OLLAMA_URL", "http://localhost:11434")
    except Exception as e:
        logger.warning(f"Não foi possível ler config IA: {e}")
        return None

    if not model:
        return None

    vf        = dados['verificacao']
    chunks    = dados['chunks'][:10]
    matches   = dados['matches'][:5]
    score_val = float(vf.get('percentagem_plagio', vf.get('score_global', 0)))
    score_pct = round(score_val)

    fontes_texto = "\n".join([
        f"- {m.get('titulo_fonte') or m.get('fonte_externa', 'N/D')} "
        f"({round(float(m.get('similaridade_max', m.get('contribuicao_pct', 0))) * 100)}%)"
        for m in matches
    ])

    exemplos_texto = "\n".join([
        f"[Trecho suspeito]: {c.get('texto_suspeito', '')[:200]}\n"
        f"[Fonte]: {c.get('texto_original', '')[:200]}\n"
        f"[Tipo IA]: {c.get('ia_tipo', 'N/A')}"
        for c in chunks[:3]
    ])

    prompt = f"""És o Unimetro Analista, perito em integridade académica do IMETRO Angola.

Analisa os dados abaixo e escreve uma CONCLUSÃO NARRATIVA em português de Portugal, em texto corrido (sem bullets, sem títulos, sem markdown). A conclusão deve:
1. Mencionar o título e autor do trabalho
2. Descrever o padrão de plágio encontrado com precisão técnica
3. Referenciar as fontes mais afectadas
4. Usar linguagem institucional adequada para um relatório académico formal
5. Ter entre 80 e 150 palavras
6. Nunca incluir recomendações de aprovação/reprovação — isso compete ao avaliador humano

DADOS:
- Trabalho: "{vf.get('titulo')}" por {vf.get('autor')}
- Score global: {score_pct}%
- Classificação: {classificacao}
- Tipo predominante: {tipo or 'Não determinado'}
- Fontes com correspondência:
{fontes_texto}

Exemplos de trechos (score > 70%):
{exemplos_texto}

Escreve APENAS a conclusão narrativa, sem introdução, sem título, sem assinatura."""

    texto = _call_llm_direct(prompt, provider, model, api_key, ollama_url)
    if texto:
        return (texto.strip(), f"{provider}/{model}")
    return None


def construir_e_guardar_veredicto(verificacao_id: int, usar_llm: bool = True) -> dict:
    dados = obter_dados_relatorio_completo(verificacao_id)
    if not dados:
        raise ValueError(f"Verificação {verificacao_id} não encontrada.")

    score_global  = float(dados['verificacao'].get('percentagem_plagio', dados['verificacao'].get('score_global', 0))) / 100.0
    chunks        = dados['chunks']
    n_chunks      = len(chunks)
    n_ia          = sum(1 for c in chunks if c.get('ia_tipo'))

    classificacao, gravidade   = classificar_score(score_global)
    tipo_predominante          = determinar_tipo_predominante(chunks)

    modelo_usado  = None
    conclusao     = None

    if usar_llm and n_ia > 0:
        resultado_llm = _conclusao_llm(dados, classificacao, tipo_predominante)
        if resultado_llm:
            conclusao, modelo_usado = resultado_llm

    if not conclusao:
        conclusao = _conclusao_local(dados, classificacao, tipo_predominante, gravidade)

    veredicto_dados = {
        'score_global':       score_global,
        'classificacao':      classificacao,
        'tipo_predominante':  tipo_predominante,
        'gravidade':          gravidade,
        'conclusao_ia':       conclusao,
        'modelo_ia_usado':    modelo_usado,
        'chunks_analisados':  n_chunks,
        'gerado_por_ia':      1 if modelo_usado else 0,
    }

    guardar_veredicto_final(verificacao_id, veredicto_dados)
    logger.info(
        f"Veredicto final gerado para verificação {verificacao_id}: "
        f"{classificacao} ({round(score_global*100)}%) — LLM: {modelo_usado or 'local'}"
    )
    return veredicto_dados
