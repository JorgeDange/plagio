# Sistema de Detecção de Plágio — chunker.py
# Módulo responsável pela divisão do texto em chunks com janela deslizante.


def dividir_em_chunks(texto: str, tamanho: int = 200, overlap: int = 50) -> list[str]:
    """
    Divide o texto em chunks usando janela deslizante por palavras.
    
    Cada chunk contém 'tamanho' palavras. A janela avança (tamanho - overlap)
    palavras de cada vez, criando sobreposição entre chunks consecutivos.
    
    Exemplo com tamanho=200, overlap=50:
        Chunk 0: palavras [0, 200)
        Chunk 1: palavras [150, 350)
        Chunk 2: palavras [300, 500)
    
    Args:
        texto: Texto completo a dividir.
        tamanho: Número de palavras por chunk (padrão: 200).
        overlap: Número de palavras de sobreposição (padrão: 50).
    
    Returns:
        Lista de strings, cada uma representando um chunk.
    
    Raises:
        ValueError: Se o tamanho ou overlap forem inválidos.
    """
    if tamanho <= 0:
        raise ValueError(f"O tamanho deve ser positivo, recebeu: {tamanho}")
    if overlap < 0:
        raise ValueError(f"O overlap não pode ser negativo, recebeu: {overlap}")
    if overlap >= tamanho:
        raise ValueError(
            f"O overlap ({overlap}) deve ser menor que o tamanho ({tamanho})"
        )

    palavras: list[str] = texto.split()
    total_palavras: int = len(palavras)

    # Se o texto tiver menos palavras que o tamanho, retorna tudo como um único chunk
    if total_palavras == 0:
        return []

    if total_palavras <= tamanho:
        return [" ".join(palavras)]

    chunks: list[str] = []
    passo: int = tamanho - overlap  # Quantas palavras a janela avança
    inicio: int = 0

    while inicio < total_palavras:
        fim: int = min(inicio + tamanho, total_palavras)
        chunk: str = " ".join(palavras[inicio:fim])
        chunks.append(chunk)

        # Se já chegámos ao final, parar
        if fim == total_palavras:
            break

        inicio += passo

    return chunks


if __name__ == "__main__":
    # Teste rápido
    texto_exemplo = " ".join([f"palavra{i}" for i in range(500)])
    chunks = dividir_em_chunks(texto_exemplo, tamanho=200, overlap=50)
    print(f"Total de palavras: 500")
    print(f"Chunks gerados: {len(chunks)}")
    for i, chunk in enumerate(chunks):
        palavras = chunk.split()
        print(f"  Chunk {i}: {len(palavras)} palavras — "
              f"'{palavras[0]}' ... '{palavras[-1]}'")
