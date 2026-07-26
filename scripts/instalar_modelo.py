# scripts/instalar_modelo.py
# Script de instalação offline do modelo LaBSE.
# Descarrega o modelo uma única vez e guarda em modelos/labse/.
# Após execução, o sistema funciona 100% offline.

import os
import sys

# Caminho base do projecto (pasta acima de scripts/)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
MODEL_DIR = os.path.join(BASE_DIR, 'app', 'models', 'labse')

# Ficheiros mínimos que o SentenceTransformer precisa para funcionar offline
FICHEIROS_NECESSARIOS = [
    'config.json',
    'tokenizer_config.json',
    'modules.json',
    'config_sentence_transformers.json',
]


def modelo_instalado() -> bool:
    """Verifica se a pasta do modelo existe e tem os ficheiros essenciais."""
    if not os.path.isdir(MODEL_DIR):
        return False
    for f in FICHEIROS_NECESSARIOS:
        if not os.path.isfile(os.path.join(MODEL_DIR, f)):
            return False
    # Verificar se existe pelo menos um ficheiro de pesos
    tem_pesos = (
        os.path.isfile(os.path.join(MODEL_DIR, 'model.safetensors'))
        or os.path.isfile(os.path.join(MODEL_DIR, 'pytorch_model.bin'))
    )
    return tem_pesos


def descarregar_modelo():
    """Descarrega o modelo LaBSE do HuggingFace e guarda em modelos/labse/."""
    print(f'[Instalação] A descarregar modelo LaBSE para: {MODEL_DIR}')
    print('[Instalação] Isto pode demorar alguns minutos (~1.88GB)...')
    print()

    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        print('[ERRO] A biblioteca sentence-transformers não está instalada.')
        print('       Execute: pip install "sentence-transformers>=2.2.0,<4.0.0"')
        sys.exit(1)

    # Descarregar o modelo da internet
    modelo = SentenceTransformer('sentence-transformers/LaBSE')

    # Guardar localmente
    os.makedirs(MODEL_DIR, exist_ok=True)
    modelo.save(MODEL_DIR)

    print()
    print(f'[Instalação] Modelo guardado com sucesso em: {MODEL_DIR}')

    # Remover ficheiros desnecessários para poupar espaço
    ficheiros_remover = ['flax_model.msgpack', 'tf_model.h5']
    for f in ficheiros_remover:
        caminho = os.path.join(MODEL_DIR, f)
        if os.path.isfile(caminho):
            os.remove(caminho)
            print(f'[Instalação] Removido ficheiro desnecessário: {f}')


def testar_modelo():
    """Carrega o modelo offline e testa com uma frase de exemplo."""
    print()
    print('[Teste] A carregar modelo a partir da pasta local...')

    # Forçar modo offline
    os.environ['TRANSFORMERS_OFFLINE'] = '1'
    os.environ['HF_DATASETS_OFFLINE'] = '1'

    from sentence_transformers import SentenceTransformer

    modelo = SentenceTransformer(MODEL_DIR)
    frase_teste = 'Teste de funcionamento'
    embedding = modelo.encode(frase_teste, normalize_embeddings=True)

    print(f'[Teste] Frase: "{frase_teste}"')
    print(f'[Teste] Dimensão do vector gerado: {embedding.shape}')
    print(f'[Teste] Primeiros 5 valores: {embedding[:5].tolist()}')
    print()
    print('[OK] O modelo está funcional e pronto para uso offline!')


def main():
    print('=' * 60)
    print(' IMETRO TFC v3 — Instalação do Modelo LaBSE')
    print('=' * 60)
    print()

    if modelo_instalado():
        print('[Info] Modelo já instalado em:')
        print(f'       {MODEL_DIR}')
        print()
        testar_modelo()
    else:
        descarregar_modelo()
        testar_modelo()

    print()
    print('=' * 60)
    print(' Instalação concluída. Execute: python run.py')
    print('=' * 60)


if __name__ == '__main__':
    main()
