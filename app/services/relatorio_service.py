# Sistema de Detecção de Plágio — Serviço de Relatórios
# Gera e guarda relatórios HTML usando core.relatorio.

import os
import uuid
from flask import current_app
from core.relatorio import gerar_html


from app.database.db import get_db

def gerar_e_guardar(dados_verificacao: dict, titulo: str, autor: str) -> str:
    """
    Gera um relatório HTML e guarda-o em disco com nome único.

    Args:
        dados_verificacao: Dicionário de resultados da verificação.
        titulo: Título do documento verificado.
        autor: Autor do documento verificado.

    Returns:
        Caminho absoluto do ficheiro de relatório gerado.
    """
    db = get_db()
    cur = db.cursor()
    for match in dados_verificacao.get('detalhes', []):
        if match.get('chroma_id_origem'):
            cur.execute(
                "SELECT id FROM monografias WHERE chroma_id = %s",
                (match['chroma_id_origem'],)
            )
            row = cur.fetchone()
            match['link_id'] = row[0] if row else None
    cur.close()

    html: str = gerar_html(dados_verificacao, titulo, autor)

    nome_ficheiro: str = f'relatorio_{uuid.uuid4().hex[:12]}.html'
    pasta_relatorios: str = current_app.config['RELATORIOS_FOLDER']
    caminho_completo: str = os.path.join(pasta_relatorios, nome_ficheiro)

    with open(caminho_completo, 'w', encoding='utf-8') as f:
        f.write(html)

    return caminho_completo


def ler_html(caminho: str) -> str:
    """
    Lê o conteúdo HTML de um relatório para servir inline.

    Args:
        caminho: Caminho absoluto para o ficheiro HTML.

    Returns:
        Conteúdo HTML como string.

    Raises:
        FileNotFoundError: Se o ficheiro não existir.
    """
    if not os.path.exists(caminho):
        raise FileNotFoundError(f'Relatório não encontrado: {caminho}')

    with open(caminho, 'r', encoding='utf-8') as f:
        return f.read()


def listar_relatorios() -> list[dict]:
    """
    Lista todos os relatórios existentes na pasta de relatórios.

    Returns:
        Lista de dicionários com nome e caminho de cada relatório.
    """
    pasta: str = current_app.config['RELATORIOS_FOLDER']
    relatorios: list[dict] = []

    if os.path.exists(pasta):
        for nome in sorted(os.listdir(pasta), reverse=True):
            if nome.endswith('.html'):
                relatorios.append({
                    'nome': nome,
                    'caminho': os.path.join(pasta, nome)
                })

    return relatorios
