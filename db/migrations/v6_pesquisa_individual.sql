-- v6_pesquisa_individual.sql

CREATE TABLE IF NOT EXISTS sessoes_pesquisa (
    id TEXT PRIMARY KEY,
    utilizador_id INTEGER REFERENCES utilizadores(id),
    modo_entrada TEXT NOT NULL,
    texto_original TEXT,
    nome_ficheiro TEXT,
    filtros_json TEXT,
    estado TEXT DEFAULT 'a_processar',
    total_resultados INTEGER DEFAULT 0,
    tempo_segundos REAL,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS resultados_pesquisa (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sessao_id TEXT REFERENCES sessoes_pesquisa(id),
    api_fonte TEXT NOT NULL,
    titulo TEXT NOT NULL,
    autores TEXT,
    ano INTEGER,
    resumo TEXT,
    url TEXT,
    score_labse REAL,
    chunk_origem TEXT,
    posicao_ranking INTEGER,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
