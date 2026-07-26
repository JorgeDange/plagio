-- v8_veredicto_final.sql
-- Adiciona tabela de veredictos consolidados gerados pelo Unimetro Analista

CREATE TABLE IF NOT EXISTS veredictos_finais (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    verificacao_id      INTEGER NOT NULL UNIQUE,
    data_geracao        TEXT NOT NULL DEFAULT (datetime('now')),
    score_global        REAL NOT NULL DEFAULT 0,
    classificacao       TEXT NOT NULL DEFAULT 'Sem plágio',
    tipo_predominante   TEXT,
    gravidade           TEXT,
    conclusao_ia        TEXT,
    modelo_ia_usado     TEXT,
    chunks_analisados   INTEGER NOT NULL DEFAULT 0,
    gerado_por_ia       INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (verificacao_id) REFERENCES verificacoes(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_veredictos_verificacao ON veredictos_finais(verificacao_id);
