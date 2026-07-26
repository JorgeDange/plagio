-- v7_normas_na_verificacao.sql

CREATE TABLE IF NOT EXISTS verificacoes_normas (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Ligação à verificação de plágio
    verificacao_id          INTEGER NOT NULL UNIQUE
                            REFERENCES verificacoes(id) ON DELETE CASCADE,

    -- Resultado da verificação local (regex) — sempre presente
    local_executada         INTEGER NOT NULL DEFAULT 0,  -- 0=não, 1=sim
    local_total_regras      INTEGER DEFAULT 0,
    local_regras_ok         INTEGER DEFAULT 0,
    local_regras_falhou     INTEGER DEFAULT 0,
    local_percentagem       REAL DEFAULT 0.0,  -- 0.0 a 100.0
    local_resultado_json    TEXT,  -- JSON completo da verificação local

    -- Resultado da verificação por IA — opcional
    ia_executada            INTEGER NOT NULL DEFAULT 0,
    ia_pontuacao_total      INTEGER DEFAULT NULL,  -- 0 a 100
    ia_classificacao        TEXT DEFAULT NULL,
                            -- 'CONFORME'|'CONFORME_COM_RESSALVAS'|'NAO_CONFORME'
    ia_num_infracoes        INTEGER DEFAULT 0,
    ia_tem_bloqueante       INTEGER DEFAULT 0,  -- 0=não, 1=sim
    ia_resultado_json       TEXT,  -- JSON completo retornado pela IA

    -- Estado consolidado (combina local + IA)
    classificacao_final     TEXT NOT NULL DEFAULT 'PENDENTE',
                            -- 'CONFORME'|'COM_RESSALVAS'|'NAO_CONFORME'|'PENDENTE'
    requer_correcao         INTEGER NOT NULL DEFAULT 0,  -- 0=não, 1=sim
    resumo_problemas        TEXT,  -- texto curto para mostrar ao aprovador

    -- Rastreabilidade
    criado_em               DATETIME DEFAULT CURRENT_TIMESTAMP,
    atualizado_em           DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS verificacoes_normas_infracoes (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    normas_id           INTEGER NOT NULL
                        REFERENCES verificacoes_normas(id) ON DELETE CASCADE,
    codigo              TEXT NOT NULL,   -- ex: 'IMETRO-003', 'LOCAL-RES-001'
    origem              TEXT NOT NULL,   -- 'local' | 'ia'
    gravidade           TEXT NOT NULL,
                        -- 'BLOQUEANTE'|'GRAVE'|'MODERADA'|'LEVE'
    elemento            TEXT NOT NULL,   -- ex: 'resumo', 'citacoes'
    descricao           TEXT NOT NULL,
    recomendacao        TEXT,
    norma_violada       TEXT             -- ex: 'Secção 3.7 — Espaçamento'
);

-- Evitar erro se as colunas já existirem por re-execução
BEGIN TRANSACTION;

-- Utilizar pragma para ver se as colunas já existem
-- SQLite não tem "ADD COLUMN IF NOT EXISTS", logo adicionamos de forma segura se possível,
-- Ou apenas corremos sabendo que o app/database/migrations handle os erros (vamos assumir que a app apenas tenta 1x)
-- No python chamamos com try/except.
COMMIT;

ALTER TABLE verificacoes ADD COLUMN normas_incluidas INTEGER NOT NULL DEFAULT 0;
ALTER TABLE verificacoes ADD COLUMN normas_ia_incluida INTEGER NOT NULL DEFAULT 0;

CREATE INDEX IF NOT EXISTS idx_vn_verificacao  ON verificacoes_normas(verificacao_id);
CREATE INDEX IF NOT EXISTS idx_vni_normas      ON verificacoes_normas_infracoes(normas_id);
CREATE INDEX IF NOT EXISTS idx_vni_gravidade   ON verificacoes_normas_infracoes(gravidade);
CREATE INDEX IF NOT EXISTS idx_vni_origem      ON verificacoes_normas_infracoes(origem);
