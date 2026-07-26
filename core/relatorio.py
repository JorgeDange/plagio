# Sistema de Detecção de Plágio — relatorio.py
# Módulo de geração de relatórios HTML com CSS inline.

from datetime import datetime


def gerar_html(dados: dict, titulo: str, autor: str) -> str:
    """
    Gera o conteúdo HTML completo do relatório de plágio.

    Args:
        dados: Dicionário retornado por detector.verificar().
        titulo: Título do documento verificado.
        autor: Autor do documento verificado.

    Returns:
        String com o HTML completo do relatório.
    """
    nivel: str = dados["nivel"]
    pct: float = dados["percentagem_plagio"]
    total: int = dados.get("total_chunks", 0)
    suspeitos: int = dados.get("chunks_suspeitos", 0)
    detalhes: list[dict] = dados.get("detalhes", [])
    score_abnt: float = dados.get("score_abnt", 0.0)
    score_apa: float = dados.get("score_apa", 0.0)
    data_actual: str = datetime.now().strftime("%d/%m/%Y às %H:%M")

    # Cores do badge por nível
    cores = {
        "Baixo": ("#10b981", "#065f46", "#d1fae5"),
        "Moderado": ("#f59e0b", "#92400e", "#fef3c7"),
        "Alto": ("#ef4444", "#991b1b", "#fee2e2"),
    }
    cor_principal, cor_texto, cor_fundo = cores.get(nivel, cores["Baixo"])

    # Gerar linhas da tabela de detalhes (máx 20)
    linhas_detalhes: str = ""
    for i, d in enumerate(detalhes[:20]):
        sim_pct: float = d["similaridade"] * 100
        # Cor do badge de similaridade
        if sim_pct >= 95:
            badge_cor = "#ef4444"
        elif sim_pct >= 90:
            badge_cor = "#f59e0b"
        else:
            badge_cor = "#3b82f6"

        chunk_orig: str = d["chunk_texto"][:200] + ("..." if len(d["chunk_texto"]) > 200 else "")
        chunk_fonte: str = d["texto_similar"][:200] + ("..." if len(d["texto_similar"]) > 200 else "")

        if d.get("link_id"):
            titulo_html = f'<a href="/monografias/{d["link_id"]}" target="_blank" style="color: inherit; text-decoration: underline;">{d["titulo_origem"]}</a>'
        else:
            titulo_html = d.get("titulo_origem", "Desconhecido")

        # Fonte badge
        fonte_nome = d.get("fonte_origem", "local")
        if fonte_nome == "core":
            fonte_badge = '<span style="display:inline-block;padding:0.15rem 0.5rem;border-radius:12px;font-size:0.7rem;font-weight:600;background:#10b981;color:#fff;margin-left:0.5rem;">CORE</span>'
        elif fonte_nome == "openalex":
            fonte_badge = '<span style="display:inline-block;padding:0.15rem 0.5rem;border-radius:12px;font-size:0.7rem;font-weight:600;background:#3b82f6;color:#fff;margin-left:0.5rem;">OpenAlex</span>'
        elif fonte_nome == "serper":
            fonte_badge = '<span style="display:inline-block;padding:0.15rem 0.5rem;border-radius:12px;font-size:0.7rem;font-weight:600;background:#f59e0b;color:#fff;margin-left:0.5rem;">Google</span>'
        else:
            fonte_badge = '<span style="display:inline-block;padding:0.15rem 0.5rem;border-radius:12px;font-size:0.7rem;font-weight:600;background:#64748b;color:#fff;margin-left:0.5rem;">Local</span>'

        # Link externo
        url_fonte = d.get("url_fonte")
        if url_fonte:
            titulo_html = f'<a href="{url_fonte}" target="_blank" style="color: inherit; text-decoration: underline;">{d["titulo_origem"]} ↗</a>'

        linhas_detalhes += f"""
        <div class="trecho">
            <div class="trecho-header">
                <span class="trecho-num">#{i+1}</span>
                <span class="badge-sim" style="background:{badge_cor}">{sim_pct:.1f}%</span>
                {fonte_badge}
                <span class="fonte-info"><strong>{titulo_html}</strong> — {d["autor_origem"]} ({d["curso_origem"]})</span>
            </div>
            <div class="comparacao">
                <div class="col">
                    <h4>Texto verificado (Posição: {d.get("posicao", "?")})</h4>
                    <p>{chunk_orig}</p>
                </div>
                <div class="col">
                    <h4>Fonte encontrada</h4>
                    <p>{chunk_fonte}</p>
                </div>
            </div>
        </div>"""

    if not linhas_detalhes:
        linhas_detalhes = '<p class="sem-resultados">Nenhum trecho suspeito encontrado.</p>'

    resultado_normas = dados.get("resultado_normas")
    normas_html = ""
    if resultado_normas:
        n_classif = resultado_normas.get('classificacao_final', '').replace('_', ' ').title()
        n_pct = resultado_normas.get('local', {}).get('percentagem', 0)
        n_resumo = resultado_normas.get('resumo_problemas', '')
        
        infracoes_html = ""
        for inf in resultado_normas.get('infracoes', []):
            infracoes_html += f"<li><strong>[{inf.get('gravidade')}]</strong> {inf.get('descricao')} - <em>{inf.get('recomendacao')}</em></li>"
            
        normas_html = f"""
        <div style="margin:2rem 0; padding:1.5rem; background:#1e293b; border-radius:12px; border:1px solid #334155;">
            <h2 style="margin-top:0; border-bottom:none;">Normas IMETRO 2014 — {n_classif}</h2>
            <p style="color:#cbd5e1; margin-bottom:1rem;">Conformidade Estrutural: <strong>{n_pct}%</strong></p>
            <p style="color:#cbd5e1; margin-bottom:1rem;">{n_resumo}</p>
            {f'<ul style="color:#cbd5e1; margin-left:1.5rem;">{infracoes_html}</ul>' if infracoes_html else ''}
        </div>
        """

    html: str = f"""<!DOCTYPE html>
<html lang="pt">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Relatório de Plágio — {titulo}</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:'Segoe UI',system-ui,-apple-system,sans-serif;
  background:#0f172a; color:#e2e8f0; line-height:1.6; padding:2rem; }}
.container {{ max-width:960px; margin:0 auto; }}
header {{ text-align:center; margin-bottom:2rem;
  background:linear-gradient(135deg,#1e293b,#334155);
  border-radius:16px; padding:2rem; border:1px solid #475569; }}
header h1 {{ font-size:1.5rem; color:#f8fafc; margin-bottom:.5rem; }}
header p {{ color:#94a3b8; font-size:.9rem; }}
.badge {{ display:inline-block; padding:.5rem 1.5rem; border-radius:50px;
  font-weight:700; font-size:1.1rem; margin-top:1rem;
  color:{cor_texto}; background:{cor_fundo};
  border:2px solid {cor_principal}; }}
.stats {{ display:grid; grid-template-columns:repeat(3,1fr); gap:1rem;
  margin:1.5rem 0; }}
.stat {{ background:#1e293b; border-radius:12px; padding:1.5rem;
  text-align:center; border:1px solid #334155; }}
.stat .valor {{ font-size:2rem; font-weight:700; color:{cor_principal}; }}
.stat .rotulo {{ font-size:.85rem; color:#94a3b8; margin-top:.25rem; }}
h2 {{ font-size:1.2rem; color:#f8fafc; margin:2rem 0 1rem;
  padding-bottom:.5rem; border-bottom:1px solid #334155; }}
.trecho {{ background:#1e293b; border-radius:12px; padding:1.25rem;
  margin-bottom:1rem; border:1px solid #334155; }}
.trecho-header {{ display:flex; align-items:center; gap:.75rem;
  margin-bottom:.75rem; flex-wrap:wrap; }}
.trecho-num {{ color:#94a3b8; font-weight:700; font-size:.9rem; }}
.badge-sim {{ color:#fff; padding:.2rem .6rem; border-radius:20px;
  font-size:.8rem; font-weight:600; }}
.fonte-info {{ color:#94a3b8; font-size:.8rem; font-style:italic; }}
.comparacao {{ display:grid; grid-template-columns:1fr 1fr; gap:1rem; }}
.col h4 {{ font-size:.8rem; color:#64748b; text-transform:uppercase;
  margin-bottom:.5rem; letter-spacing:.05em; }}
.col p {{ font-size:.85rem; color:#cbd5e1; background:#0f172a;
  padding:.75rem; border-radius:8px; border:1px solid #1e293b; }}
.sem-resultados {{ text-align:center; color:#10b981; padding:2rem;
  font-size:1.1rem; }}
footer {{ text-align:center; margin-top:2rem; color:#475569;
  font-size:.8rem; }}
@media (max-width:640px) {{
  .stats {{ grid-template-columns:1fr; }}
  .comparacao {{ grid-template-columns:1fr; }}
}}
</style>
</head>
<body>
<div class="container">
  <header>
    <h1>Relatório de Análise de Trabalhos</h1>
    <p><strong>{titulo}</strong> — {autor}</p>
    <p>Gerado em {data_actual}</p>
    <div class="badge">{nivel} — {pct}% de similaridade</div>
  </header>
  <div class="stats" style="grid-template-columns:repeat(5,1fr);">
    <div class="stat">
      <div class="valor">{total}</div>
      <div class="rotulo">Total de trechos</div>
    </div>
    <div class="stat">
      <div class="valor">{suspeitos}</div>
      <div class="rotulo">Trechos suspeitos</div>
    </div>
    <div class="stat">
      <div class="valor">{pct}%</div>
      <div class="rotulo">Similaridade máxima encontrada</div>
    </div>
    <div class="stat" style="border-left: 2px solid #3b82f6;">
      <div class="valor" style="color:#3b82f6;">{score_abnt}%</div>
      <div class="rotulo">Norma ABNT</div>
    </div>
    <div class="stat" style="border-left: 2px solid #10b981;">
      <div class="valor" style="color:#10b981;">{score_apa}%</div>
      <div class="rotulo">Norma APA 7ª</div>
    </div>
  </div>
  
  {normas_html}
  
  <h2>Trechos suspeitos (até 20)</h2>
  {linhas_detalhes}
  <footer>
    <p>Sistema de Verificação de Trabalhos Académicos — IMETRO TFC</p>
  </footer>
</div>
</body>
</html>"""
    return html


def guardar_relatorio(dados: dict, titulo: str, autor: str,
                      caminho_saida: str = "relatorio.html") -> str:
    """
    Gera e guarda o relatório HTML em disco.

    Args:
        dados: Dicionário de resultados.
        titulo: Título do documento.
        autor: Autor do documento.
        caminho_saida: Caminho do ficheiro de saída.

    Returns:
        Caminho absoluto do ficheiro gerado.
    """
    html: str = gerar_html(dados, titulo, autor)

    with open(caminho_saida, "w", encoding="utf-8") as f:
        f.write(html)

    caminho_abs: str = os.path.abspath(caminho_saida)
    print(f"Relatório guardado em: {caminho_abs}")
    return caminho_abs


# Necessário para os.path.abspath no guardar_relatorio
import os
