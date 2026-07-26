# Sistema de Detecção de Plágio — ingestor.py
# Módulo responsável pela extracção e limpeza de texto de ficheiros PDF, DOCX e TXT.

import os
import re
import fitz  # PyMuPDF
from docx import Document


def extrair(caminho: str) -> str:
    """
    Extrai texto de um ficheiro .pdf, .docx ou .txt.
    
    Args:
        caminho: Caminho absoluto ou relativo para o ficheiro.
    
    Returns:
        Texto extraído como string.
    
    Raises:
        FileNotFoundError: Se o ficheiro não existir.
        ValueError: Se o formato não for suportado.
    """
    if not os.path.exists(caminho):
        raise FileNotFoundError(f"Ficheiro não encontrado: {caminho}")

    extensao = os.path.splitext(caminho)[1].lower()

    if extensao == ".pdf":
        return _extrair_pdf(caminho)
    elif extensao == ".docx":
        return _extrair_docx(caminho)
    elif extensao == ".txt":
        return _extrair_txt(caminho)
    else:
        raise ValueError(
            f"Formato não suportado: '{extensao}'. "
            f"Usa .pdf, .docx ou .txt."
        )


def _extrair_pdf(caminho: str) -> str:
    """Extrai texto de um ficheiro PDF usando PyMuPDF."""
    texto_paginas: list[str] = []
    try:
        doc = fitz.open(caminho)
        for num_pagina in range(len(doc)):
            pagina = doc[num_pagina]
            texto = pagina.get_text("text")
            if texto:
                texto_paginas.append(texto)
        doc.close()
    except Exception as e:
        raise RuntimeError(f"Erro ao ler PDF '{caminho}': {e}")

    return "\n".join(texto_paginas)


def _extrair_docx(caminho: str) -> str:
    """Extrai texto de um ficheiro DOCX usando python-docx."""
    try:
        doc = Document(caminho)
        paragrafos: list[str] = []
        for paragrafo in doc.paragraphs:
            texto = paragrafo.text.strip()
            if texto:
                paragrafos.append(texto)
        return "\n".join(paragrafos)
    except Exception as e:
        raise RuntimeError(f"Erro ao ler DOCX '{caminho}': {e}")


def _extrair_txt(caminho: str) -> str:
    """Extrai texto de um ficheiro TXT em UTF-8."""
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        # Fallback para latin-1 (comum em documentos angolanos mais antigos)
        with open(caminho, "r", encoding="latin-1") as f:
            return f.read()
    except Exception as e:
        raise RuntimeError(f"Erro ao ler TXT '{caminho}': {e}")


def limpar_texto(texto: str) -> str:
    """
    Limpa o texto extraído:
    - Remove sequências de 3+ linhas em branco (substitui por \\n\\n)
    - Remove espaços duplos
    - Remove números de página soltos (linhas apenas com dígitos)
    - Aplica .strip() no final
    
    Args:
        texto: Texto bruto extraído do documento.
    
    Returns:
        Texto limpo pronto para chunking.
    """
    # Remover linhas que contêm apenas números (números de página)
    texto = re.sub(r"^\s*\d+\s*$", "", texto, flags=re.MULTILINE)

    # Substituir sequências de 3+ linhas em branco por apenas 2
    texto = re.sub(r"\n{3,}", "\n\n", texto)

    # Remover espaços duplos (ou mais)
    texto = re.sub(r" {2,}", " ", texto)

    return texto.strip()


if __name__ == "__main__":
    # Teste rápido com ficheiro .txt
    import sys
    if len(sys.argv) < 2:
        print("Uso: python ingestor.py <caminho_do_ficheiro>")
        sys.exit(1)

    caminho = sys.argv[1]
    texto_bruto = extrair(caminho)
    texto_limpo = limpar_texto(texto_bruto)
    print(f"Caracteres extraídos: {len(texto_bruto)}")
    print(f"Caracteres após limpeza: {len(texto_limpo)}")
    print(f"\nPrimeiros 500 caracteres:\n{texto_limpo[:500]}")
