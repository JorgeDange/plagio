CREATE TABLE IF NOT EXISTS fontes_externas_resultados (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    verificacao_id   INTEGER  REFERENCES verificacoes(id) ON DELETE CASCADE,
    chunk_id         INTEGER  REFERENCES chunks_suspeitos(id),
    fonte            TEXT NOT NULL,
    titulo_externo   TEXT NOT NULL,
    autores          TEXT,
    ano_publicacao   INTEGER,
    doi              TEXT,
    url_fonte        TEXT,
    resumo_externo   TEXT,
    score_semantico  REAL NOT NULL,
    pesquisa_id      INTEGER  REFERENCES pesquisas_avulsas(id),
    criado_em        DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pesquisas_avulsas (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    utilizador_id    INTEGER  REFERENCES utilizadores(id),
    tipo_entrada     TEXT NOT NULL,
    texto_consulta   TEXT NOT NULL,
    fontes_usadas    TEXT,
    total_resultados INTEGER DEFAULT 0,
    exportado_csv    INTEGER DEFAULT 0,
    exportado_pdf    INTEGER DEFAULT 0,
    criado_em        DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_fontes_ext_verificacao ON fontes_externas_resultados(verificacao_id);
CREATE INDEX IF NOT EXISTS idx_fontes_ext_score       ON fontes_externas_resultados(score_semantico DESC);
CREATE INDEX IF NOT EXISTS idx_pesquisas_avulsas_user ON pesquisas_avulsas(utilizador_id);
