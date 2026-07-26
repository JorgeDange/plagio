"""
blueprints/analise_ia.py
========================
IMETRO TFC v3 — Blueprint do Módulo de Análise IA

Rotas:
    GET  /ia/configuracoes          → Página de configuração da IA
    POST /ia/configuracoes/salvar   → Salva config na BD (tabela configuracoes)
    GET  /ia/teste                  → Página de teste manual com par de chunks
    POST /ia/teste/analisar         → Analisa o par enviado pelo formulário
    POST /ia/verificacao/<id>/enriquecer → (API interna) Re-corre Fase 2 numa verificação já existente
    GET  /ia/status                 → JSON com estado actual do módulo
"""

from __future__ import annotations

import json
import logging
from flask import (
    Blueprint, current_app, flash, jsonify,
    redirect, render_template, request, url_for,
)
from core.auth_helpers import requer_admin

from core.llm_analyzer import (
    ChunkParaAnalise,
    LLMAnalyzer,
    ResultadoLLM,
    get_analyzer_from_app_config,
    resultados_para_dict,
)

logger = logging.getLogger(__name__)

analise_ia_bp = Blueprint(
    "analise_ia",
    __name__,
    url_prefix="/ia",
    template_folder="../templates/analise_ia",
)


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _get_db():
    from app.database.db import get_db
    return get_db()


def _get_config_from_db() -> dict:
    import os
    config = {}
    db = _get_db()
    cur = db.cursor()
    cur.execute(
        "SELECT chave, valor FROM configuracoes WHERE chave LIKE 'LLM_%' OR chave = 'OLLAMA_URL'"
    )
    cols = [d[0] for d in cur.description]
    rows = [dict(zip(cols, row)) for row in cur.fetchall()]
    cur.close()
    config = {r["chave"]: r["valor"] for r in rows}

    env_map = {
        "LLM_ENABLED": "LLM_ENABLED",
        "LLM_PROVIDER": "LLM_PROVIDER",
        "LLM_MODEL": "LLM_MODEL",
        "LLM_API_KEY": "LLM_API_KEY",
        "LLM_SCORE_THRESHOLD": "LLM_SCORE_THRESHOLD",
        "LLM_MAX_CHUNKS": "LLM_MAX_CHUNKS",
        "OLLAMA_URL": "OLLAMA_URL",
    }
    for env_key, cfg_key in env_map.items():
        val = os.environ.get(env_key)
        if val is not None:
            config[cfg_key] = val

    return config


def _salvar_config_no_db(config: dict) -> None:
    db = _get_db()
    cur = db.cursor()
    for chave, valor in config.items():
        cur.execute(
            """
            INSERT INTO configuracoes (chave, valor)
            VALUES (%s, %s)
            ON CONFLICT (chave) DO UPDATE SET valor = EXCLUDED.valor
            """,
            (chave, str(valor)),
        )
    db.commit()
    cur.close()


def _build_analyzer_from_db() -> LLMAnalyzer | None:
    try:
        config_db = _get_config_from_db()
        return get_analyzer_from_app_config(config_db)
    except Exception as exc:
        logger.error("Erro ao criar LLMAnalyzer: %s", exc)
        return None


def _salvar_analises_ia(verificacao_id: int, resultados: list[ResultadoLLM]) -> None:
    db = _get_db()
    cur = db.cursor()
    for r in resultados:
        cur.execute(
            """
            INSERT INTO analises_ia
              (verificacao_id, chunk_id, plagio, nivel, tipo,
               similaridade_llm, score_labse, justificativa,
               modelo_usado, tempo_ms, erro)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (verificacao_id, chunk_id) DO UPDATE SET
              plagio           = EXCLUDED.plagio,
              nivel            = EXCLUDED.nivel,
              tipo             = EXCLUDED.tipo,
              similaridade_llm = EXCLUDED.similaridade_llm,
              score_labse      = EXCLUDED.score_labse,
              justificativa    = EXCLUDED.justificativa,
              modelo_usado     = EXCLUDED.modelo_usado,
              tempo_ms         = EXCLUDED.tempo_ms,
              erro             = EXCLUDED.erro
            """,
            (
                verificacao_id,
                r.chunk_suspeito_id,
                int(r.plagio),
                r.nivel,
                r.tipo,
                r.similaridade_llm,
                round(r.score_labse, 4),
                r.justificativa,
                r.modelo_usado,
                r.tempo_ms,
                r.erro,
            ),
        )
    db.commit()
    cur.close()


# ─────────────────────────────────────────────────────────────────────────────
# ROTAS
# ─────────────────────────────────────────────────────────────────────────────

@analise_ia_bp.route("/configuracoes")
@requer_admin
def configuracoes():
    """Página de configuração do módulo IA."""
    config = _get_config_from_db()
    config_display = dict(config)
    if config_display.get("LLM_API_KEY"):
        key = config_display["LLM_API_KEY"]
        config_display["LLM_API_KEY"] = key[:8] + "•" * (len(key) - 8) if len(key) > 8 else "••••••••"
    return render_template("ia_configuracoes.html", config=config_display)


@analise_ia_bp.route("/configuracoes/salvar", methods=["POST"])
@requer_admin
def salvar_configuracoes():
    """Salva as configurações de IA na BD."""
    form = request.form

    nova_key = form.get("LLM_API_KEY", "").strip()
    config = {
        "LLM_ENABLED":        "true" if form.get("LLM_ENABLED") == "on" else "false",
        "LLM_PROVIDER":       form.get("LLM_PROVIDER", "anthropic"),
        "LLM_MODEL":          form.get("LLM_MODEL", "").strip(),
        "LLM_SCORE_THRESHOLD": form.get("LLM_SCORE_THRESHOLD", "0.75").strip(),
        "LLM_MAX_CHUNKS":     form.get("LLM_MAX_CHUNKS", "15").strip(),
        "OLLAMA_URL":         form.get("OLLAMA_URL", "http://localhost:11434").strip(),
    }
    if nova_key and "•" not in nova_key:
        config["LLM_API_KEY"] = nova_key

    try:
        _salvar_config_no_db(config)
        for k, v in config.items():
            current_app.config[k] = v
        flash("Configurações de IA guardadas com sucesso.", "success")
    except Exception as exc:
        logger.error("Erro ao salvar config IA: %s", exc)
        flash(f"Erro ao guardar configurações: {exc}", "danger")

    return redirect(url_for("analise_ia.configuracoes"))


@analise_ia_bp.route("/teste")
@requer_admin
def teste():
    """Página de teste manual."""
    return render_template("ia_teste.html")


@analise_ia_bp.route("/teste/analisar", methods=["POST"])
@requer_admin
def teste_analisar():
    """Analisa o par de textos enviado pelo formulário de teste."""
    texto_suspeito = request.form.get("texto_suspeito", "").strip()
    texto_original = request.form.get("texto_original", "").strip()
    score_labse    = float(request.form.get("score_labse", "0.85"))

    if not texto_suspeito or not texto_original:
        flash("Ambos os textos são obrigatórios.", "warning")
        return redirect(url_for("analise_ia.teste"))

    analyzer = _build_analyzer_from_db()
    if not analyzer:
        flash("Módulo IA não configurado ou desactivado. Configure em IA → Configurações.", "danger")
        return redirect(url_for("analise_ia.teste"))

    chunk = ChunkParaAnalise(
        chunk_suspeito_id    = 0,
        texto_suspeito       = texto_suspeito,
        texto_original       = texto_original,
        tcc_original_id      = 0,
        tcc_original_titulo  = "Teste Manual",
        score_labse          = score_labse,
    )

    try:
        resultado = analyzer.analisar_chunk_unico(chunk)
    except Exception as exc:
        flash(f"Erro na análise: {exc}", "danger")
        return redirect(url_for("analise_ia.teste"))

    return render_template(
        "ia_teste.html",
        resultado       = resultado,
        texto_suspeito  = texto_suspeito,
        texto_original  = texto_original,
        score_labse     = score_labse,
    )


@analise_ia_bp.route("/verificacao/<int:verificacao_id>/enriquecer", methods=["POST"])
@requer_admin
def enriquecer_verificacao(verificacao_id: int):
    """
    API interna: corre a Fase 2 (LLM) sobre uma verificação já existente.
    """
    db = _get_db()
    force = (request.json or {}).get("force", False)

    if not force:
        cur = db.cursor()
        cur.execute(
            "SELECT 1 FROM analises_ia WHERE verificacao_id = %s LIMIT 1",
            (verificacao_id,),
        )
        existe = cur.fetchone()
        cur.close()
        if existe:
            return jsonify({"ok": True, "msg": "Análise IA já existente. Use force=true para re-analisar."}), 200

    config = _get_config_from_db()
    threshold = float(config.get("LLM_SCORE_THRESHOLD", "0.75"))

    cur = db.cursor()
    cur.execute(
        """
        SELECT
            cs.id               AS chunk_id,
            cs.texto_suspeito   AS texto_suspeito,
            cs.texto_origem     AS texto_original,
            m.tcc_valido_id     AS tcc_original_id,
            m.tcc_valido_titulo AS tcc_original_titulo,
            cs.similaridade     AS score_labse
        FROM chunks_suspeitos cs
        JOIN matches m         ON m.id = cs.match_id
        WHERE cs.verificacao_id = %s
          AND cs.similaridade >= %s
        ORDER BY cs.similaridade DESC
        """,
        (verificacao_id, threshold),
    )
    ia_cols = [d[0] for d in cur.description]
    rows = [dict(zip(ia_cols, row)) for row in cur.fetchall()]
    cur.close()

    if not rows:
        return jsonify({"ok": True, "msg": "Nenhum match acima do threshold. LLM não chamada.", "total": 0}), 200

    chunks = [
        ChunkParaAnalise(
            chunk_suspeito_id   = r["chunk_id"],
            texto_suspeito      = r["texto_suspeito"],
            texto_original      = r["texto_original"],
            tcc_original_id     = r["tcc_original_id"],
            tcc_original_titulo = r["tcc_original_titulo"],
            score_labse         = float(r["score_labse"]),
        )
        for r in rows
    ]

    analyzer = _build_analyzer_from_db()
    if not analyzer:
        return jsonify({"ok": False, "msg": "Módulo IA não configurado ou desactivado."}), 503

    try:
        resultados = analyzer.analisar_verificacao(chunks)
        _salvar_analises_ia(verificacao_id, resultados)

        if resultados:
            plagio_confirmados = [r for r in resultados if r.plagio]
            if plagio_confirmados:
                nivel_max = max(
                    ["baixo", "moderado", "alto", "critico"].index(r.nivel)
                    for r in plagio_confirmados
                )
                nivel_geral = ["baixo", "moderado", "alto", "critico"][nivel_max]
            else:
                nivel_geral = "baixo"

            try:
                cur2 = db.cursor()
                cur2.execute(
                    "UPDATE verificacoes SET nivel_ia = %s, analise_ia_ok = 1 WHERE id = %s",
                    (nivel_geral, verificacao_id),
                )
                db.commit()
                cur2.close()
            except Exception as e:
                logger.warning(f"Não foi possível atualizar nivel_ia na tabela verificacoes (ignorado): {e}")

        return jsonify({
            "ok":              True,
            "total_analisados": len(resultados),
            "plagio_confirmado": sum(1 for r in resultados if r.plagio),
            "resultados":       resultados_para_dict(resultados),
        }), 200

    except Exception as exc:
        logger.error("Erro na Fase 2 da verificação %d: %s", verificacao_id, exc)
        return jsonify({"ok": False, "msg": str(exc)}), 500


@analise_ia_bp.route("/status")
@requer_admin
def status():
    """JSON com o estado actual do módulo IA."""
    config = _get_config_from_db()
    enabled  = config.get("LLM_ENABLED", "false").lower() == "true"
    provider = config.get("LLM_PROVIDER", "—")
    model    = config.get("LLM_MODEL", "—")
    has_key  = bool(config.get("LLM_API_KEY", ""))

    return jsonify({
        "ia_enabled":      enabled,
        "provider":        provider,
        "model":           model,
        "api_key_present": has_key,
        "score_threshold": config.get("LLM_SCORE_THRESHOLD", "0.75"),
        "max_chunks":      config.get("LLM_MAX_CHUNKS", "15"),
    })
