-- IMETRO TFC v4 — Migração: Sistema de Utilizadores e RBAC
-- Criado: 2026-05-07

-- Tabela de utilizadores com papéis
CREATE TABLE IF NOT EXISTS utilizadores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    papel TEXT NOT NULL CHECK(papel IN ('administrador','carregador','verificador','aprovador')),
    ativo INTEGER NOT NULL DEFAULT 1,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ultimo_login TIMESTAMP
);

-- Administrador padrão (password temporária — usar scripts/criar_admin.py para definir)
INSERT OR IGNORE INTO utilizadores (nome, email, password_hash, papel)
VALUES ('Administrador', 'admin@imetro.ao', 'HASH_PLACEHOLDER', 'administrador');

-- Colunas de aprovação na tabela tcc_suspeitos
-- (executadas separadamente pois ALTER TABLE não suporta IF NOT EXISTS no SQLite)
-- Estas colunas são adicionadas programaticamente em app/database/db.py
