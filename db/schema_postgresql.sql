-- ============================================================
-- IMETRO TFC v3 — Schema Completo do Banco de Dados
-- PostgreSQL / utf8
-- Gerado: 2026-07-26
-- ============================================================

-- ============================================================
-- 1. TABELAS SEM FOREIGN KEYS
-- ============================================================

CREATE TABLE IF NOT EXISTS cursos (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(200) NOT NULL UNIQUE,
    codigo VARCHAR(20),
    departamento VARCHAR(200),
    descricao TEXT,
    data_criacao TEXT NOT NULL,
    activo INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS orientadores (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(200) NOT NULL,
    email VARCHAR(200),
    titulacao VARCHAR(100),
    curso_id INTEGER,
    activo INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS utilizadores (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(200) NOT NULL,
    email VARCHAR(200) NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    papel VARCHAR(20) NOT NULL,
    ativo INTEGER NOT NULL DEFAULT 1,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ultimo_login TIMESTAMP NULL
);

CREATE TABLE IF NOT EXISTS configuracoes (
    chave VARCHAR(200) PRIMARY KEY,
    valor VARCHAR(500)
);

CREATE TABLE IF NOT EXISTS config_pesquisa_externa (
    chave VARCHAR(200) PRIMARY KEY,
    valor VARCHAR(500) NOT NULL,
    descricao VARCHAR(500)
);

CREATE TABLE IF NOT EXISTS tcc_validos (
    id SERIAL PRIMARY KEY,
    titulo TEXT NOT NULL,
    autor VARCHAR(200) NOT NULL,
    orientador_id INTEGER,
    orientador_nome VARCHAR(200) DEFAULT '',
    curso_id INTEGER,
    curso_nome VARCHAR(200) DEFAULT '',
    ano_defesa INTEGER,
    semestre VARCHAR(20) DEFAULT '',
    palavras_chave TEXT,
    resumo TEXT,
    nota_final REAL,
    data_indexacao TEXT NOT NULL,
    num_chunks INTEGER DEFAULT 0,
    caminho_ficheiro TEXT,
    chroma_id VARCHAR(100) UNIQUE,
    tem_capa INTEGER DEFAULT 0,
    tem_folha_rosto INTEGER DEFAULT 0,
    tem_resumo INTEGER DEFAULT 0,
    tem_abstract INTEGER DEFAULT 0,
    tem_sumario INTEGER DEFAULT 0,
    tem_referencias INTEGER DEFAULT 0,
    score_abnt REAL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS tcc_suspeitos (
    id SERIAL PRIMARY KEY,
    titulo TEXT,
    autor VARCHAR(200) NOT NULL,
    orientador_id INTEGER,
    orientador_nome VARCHAR(200) DEFAULT '',
    curso_id INTEGER,
    curso_nome VARCHAR(200) DEFAULT '',
    ano_submissao INTEGER,
    estado VARCHAR(20) DEFAULT 'pendente',
    data_submissao TEXT NOT NULL,
    caminho_ficheiro TEXT NOT NULL,
    ultima_verificacao_id INTEGER,
    ultima_pct_plagio REAL,
    ultimo_nivel VARCHAR(20) DEFAULT '',
    aprovado_por INTEGER,
    submetido_por INTEGER,
    aprovado_em TIMESTAMP NULL,
    nota_aprovacao VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS verificacoes (
    id SERIAL PRIMARY KEY,
    tcc_suspeito_id INTEGER,
    curso_id_filtro INTEGER,
    curso_nome_filtro VARCHAR(200) DEFAULT '',
    limiar_usado REAL NOT NULL,
    percentagem_plagio REAL DEFAULT 0.0,
    nivel VARCHAR(20) DEFAULT 'Baixo',
    num_chunks_total INTEGER DEFAULT 0,
    num_chunks_suspeitos INTEGER DEFAULT 0,
    data TEXT NOT NULL,
    duracao_segundos REAL DEFAULT 0,
    caminho_relatorio TEXT,
    score_abnt REAL DEFAULT 0,
    observacoes TEXT,
    score_apa REAL DEFAULT 0,
    nivel_ia VARCHAR(20) DEFAULT '',
    analise_ia_ok INTEGER DEFAULT 0,
    normas_incluidas INTEGER NOT NULL DEFAULT 0,
    normas_ia_incluida INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS pesquisas_avulsas (
    id SERIAL PRIMARY KEY,
    utilizador_id INTEGER,
    tipo_entrada VARCHAR(50) NOT NULL,
    texto_consulta TEXT NOT NULL,
    fontes_usadas TEXT,
    total_resultados INTEGER DEFAULT 0,
    exportado_csv INTEGER DEFAULT 0,
    exportado_pdf INTEGER DEFAULT 0,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- 2. TABELAS COM FOREIGN KEYS
-- ============================================================

CREATE TABLE IF NOT EXISTS matches (
    id SERIAL PRIMARY KEY,
    verificacao_id INTEGER,
    tcc_valido_id INTEGER,
    tcc_valido_titulo TEXT,
    tcc_valido_autor TEXT,
    num_chunks_comuns INTEGER DEFAULT 0,
    similaridade_max REAL DEFAULT 0,
    similaridade_media REAL DEFAULT 0,
    contribuicao_pct REAL DEFAULT 0,
    fonte_tipo VARCHAR(20) DEFAULT 'interno',
    fonte_externa_id INTEGER,
    fonte_origem VARCHAR(50) NOT NULL DEFAULT 'desconhecida',
    titulo_fonte VARCHAR(500) NULL,
    url_fonte VARCHAR(1000) NULL,
    trecho_similar TEXT NULL,
    trecho_original TEXT NULL
);

CREATE TABLE IF NOT EXISTS chunks_suspeitos (
    id SERIAL PRIMARY KEY,
    verificacao_id INTEGER,
    match_id INTEGER,
    posicao_chunk INTEGER,
    texto_suspeito TEXT,
    texto_origem TEXT,
    similaridade REAL DEFAULT 0,
    secao_estimada VARCHAR(50) DEFAULT ''
);

CREATE TABLE IF NOT EXISTS fontes_externas (
    id SERIAL PRIMARY KEY,
    verificacao_id INTEGER NOT NULL,
    chunk_suspeito_id INTEGER,
    api_fonte VARCHAR(50) NOT NULL,
    titulo_externo TEXT,
    autores TEXT,
    ano INTEGER,
    resumo_externo TEXT,
    url_externo TEXT,
    score_similaridade REAL,
    chunk_texto TEXT,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS fontes_externas_resultados (
    id SERIAL PRIMARY KEY,
    verificacao_id INTEGER,
    chunk_id INTEGER,
    fonte VARCHAR(50) NOT NULL,
    titulo_externo TEXT NOT NULL,
    autores TEXT,
    ano_publicacao INTEGER,
    doi VARCHAR(200),
    url_fonte TEXT,
    resumo_externo TEXT,
    score_semantico REAL NOT NULL,
    pesquisa_id INTEGER,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS analises_ia (
    id SERIAL PRIMARY KEY,
    verificacao_id INTEGER NOT NULL,
    chunk_id INTEGER NOT NULL,
    plagio INTEGER NOT NULL DEFAULT 0,
    nivel VARCHAR(20) DEFAULT '',
    tipo VARCHAR(20) DEFAULT '',
    similaridade_llm INTEGER DEFAULT 0,
    score_labse REAL DEFAULT 0,
    justificativa TEXT,
    modelo_usado VARCHAR(100) DEFAULT '',
    tempo_ms INTEGER DEFAULT 0,
    erro TEXT,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (verificacao_id, chunk_id)
);

CREATE TABLE IF NOT EXISTS verificacoes_normas (
    id SERIAL PRIMARY KEY,
    verificacao_id INTEGER NOT NULL UNIQUE,
    local_executada INTEGER NOT NULL DEFAULT 0,
    local_total_regras INTEGER DEFAULT 0,
    local_regras_ok INTEGER DEFAULT 0,
    local_regras_falhou INTEGER DEFAULT 0,
    local_percentagem REAL DEFAULT 0.0,
    local_resultado_json TEXT,
    ia_executada INTEGER NOT NULL DEFAULT 0,
    ia_pontuacao_total INTEGER DEFAULT NULL,
    ia_classificacao VARCHAR(50) DEFAULT NULL,
    ia_num_infracoes INTEGER DEFAULT 0,
    ia_tem_bloqueante INTEGER DEFAULT 0,
    ia_resultado_json TEXT,
    classificacao_final VARCHAR(30) NOT NULL DEFAULT 'PENDENTE',
    requer_correcao INTEGER NOT NULL DEFAULT 0,
    resumo_problemas TEXT,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS verificacoes_normas_infracoes (
    id SERIAL PRIMARY KEY,
    normas_id INTEGER NOT NULL,
    codigo VARCHAR(50) NOT NULL,
    origem VARCHAR(10) NOT NULL,
    gravidade VARCHAR(20) NOT NULL,
    elemento VARCHAR(100) NOT NULL,
    descricao TEXT NOT NULL,
    recomendacao TEXT,
    norma_violada TEXT
);

CREATE TABLE IF NOT EXISTS veredictos_finais (
    id SERIAL PRIMARY KEY,
    verificacao_id INTEGER NOT NULL UNIQUE,
    data_geracao TEXT NOT NULL,
    score_global REAL NOT NULL DEFAULT 0,
    classificacao VARCHAR(50) NOT NULL DEFAULT 'Sem plagio',
    tipo_predominante VARCHAR(50),
    gravidade VARCHAR(20),
    conclusao_ia TEXT,
    modelo_ia_usado VARCHAR(100),
    chunks_analisados INTEGER NOT NULL DEFAULT 0,
    gerado_por_ia INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS embeddings_chunks (
    id SERIAL PRIMARY KEY,
    tcc_id INTEGER NOT NULL,
    tipo VARCHAR(10) NOT NULL CHECK (tipo IN ('valido','suspeito')),
    chunk_texto TEXT NOT NULL,
    vector JSONB NOT NULL,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sessoes_pesquisa (
    id VARCHAR(100) PRIMARY KEY,
    utilizador_id INTEGER,
    modo_entrada VARCHAR(50) NOT NULL,
    texto_original TEXT,
    nome_ficheiro VARCHAR(500),
    filtros_json TEXT,
    estado VARCHAR(20) DEFAULT 'a_processar',
    total_resultados INTEGER DEFAULT 0,
    tempo_segundos REAL,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS resultados_pesquisa (
    id SERIAL PRIMARY KEY,
    sessao_id VARCHAR(100),
    api_fonte VARCHAR(50) NOT NULL,
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

-- ============================================================
-- 3. INDEXES
-- ============================================================

-- fontes_externas_resultados
CREATE INDEX IF NOT EXISTS idx_fontes_ext_verificacao ON fontes_externas_resultados(verificacao_id);
CREATE INDEX IF NOT EXISTS idx_fontes_ext_score ON fontes_externas_resultados(score_semantico DESC);
CREATE INDEX IF NOT EXISTS idx_fontes_ext_pesquisa ON fontes_externas_resultados(pesquisa_id);

-- pesquisas_avulsas
CREATE INDEX IF NOT EXISTS idx_pesquisas_avulsas_user ON pesquisas_avulsas(utilizador_id);

-- verificacoes_normas
CREATE INDEX IF NOT EXISTS idx_vn_verificacao ON verificacoes_normas(verificacao_id);

-- verificacoes_normas_infracoes
CREATE INDEX IF NOT EXISTS idx_vni_normas ON verificacoes_normas_infracoes(normas_id);
CREATE INDEX IF NOT EXISTS idx_vni_gravidade ON verificacoes_normas_infracoes(gravidade);
CREATE INDEX IF NOT EXISTS idx_vni_origem ON verificacoes_normas_infracoes(origem);

-- veredictos_finais
CREATE INDEX IF NOT EXISTS idx_veredictos_verificacao ON veredictos_finais(verificacao_id);

-- embeddings_chunks
CREATE INDEX IF NOT EXISTS idx_tcc ON embeddings_chunks(tcc_id, tipo);

-- ============================================================
-- 4. FOREIGN KEYS
-- ============================================================

ALTER TABLE orientadores
    ADD CONSTRAINT fk_orientadores_curso_id FOREIGN KEY (curso_id) REFERENCES cursos(id);

ALTER TABLE tcc_validos
    ADD CONSTRAINT fk_tcc_validos_orientador_id FOREIGN KEY (orientador_id) REFERENCES orientadores(id),
    ADD CONSTRAINT fk_tcc_validos_curso_id FOREIGN KEY (curso_id) REFERENCES cursos(id);

ALTER TABLE tcc_suspeitos
    ADD CONSTRAINT fk_tcc_suspeitos_orientador_id FOREIGN KEY (orientador_id) REFERENCES orientadores(id),
    ADD CONSTRAINT fk_tcc_suspeitos_curso_id FOREIGN KEY (curso_id) REFERENCES cursos(id),
    ADD CONSTRAINT fk_tcc_suspeitos_aprovado_por FOREIGN KEY (aprovado_por) REFERENCES utilizadores(id);

ALTER TABLE verificacoes
    ADD CONSTRAINT fk_verificacoes_tcc_suspeito_id FOREIGN KEY (tcc_suspeito_id) REFERENCES tcc_suspeitos(id),
    ADD CONSTRAINT fk_verificacoes_curso_id_filtro FOREIGN KEY (curso_id_filtro) REFERENCES cursos(id);

ALTER TABLE chunks_suspeitos
    ADD CONSTRAINT fk_chunks_suspeitos_verificacao_id FOREIGN KEY (verificacao_id) REFERENCES verificacoes(id),
    ADD CONSTRAINT fk_chunks_suspeitos_match_id FOREIGN KEY (match_id) REFERENCES matches(id);

ALTER TABLE fontes_externas
    ADD CONSTRAINT fk_fontes_externas_verificacao_id FOREIGN KEY (verificacao_id) REFERENCES verificacoes(id),
    ADD CONSTRAINT fk_fontes_externas_chunk_suspeito_id FOREIGN KEY (chunk_suspeito_id) REFERENCES chunks_suspeitos(id);

ALTER TABLE matches
    ADD CONSTRAINT fk_matches_verificacao_id FOREIGN KEY (verificacao_id) REFERENCES verificacoes(id),
    ADD CONSTRAINT fk_matches_tcc_valido_id FOREIGN KEY (tcc_valido_id) REFERENCES tcc_validos(id),
    ADD CONSTRAINT fk_matches_fonte_externa_id FOREIGN KEY (fonte_externa_id) REFERENCES fontes_externas(id);

ALTER TABLE fontes_externas_resultados
    ADD CONSTRAINT fk_fer_verificacao_id FOREIGN KEY (verificacao_id) REFERENCES verificacoes(id),
    ADD CONSTRAINT fk_fer_chunk_id FOREIGN KEY (chunk_id) REFERENCES chunks_suspeitos(id),
    ADD CONSTRAINT fk_fer_pesquisa_id FOREIGN KEY (pesquisa_id) REFERENCES pesquisas_avulsas(id);

ALTER TABLE analises_ia
    ADD CONSTRAINT fk_analises_ia_verificacao_id FOREIGN KEY (verificacao_id) REFERENCES verificacoes(id),
    ADD CONSTRAINT fk_analises_ia_chunk_id FOREIGN KEY (chunk_id) REFERENCES chunks_suspeitos(id);

ALTER TABLE verificacoes_normas
    ADD CONSTRAINT fk_vn_verificacao_id FOREIGN KEY (verificacao_id) REFERENCES verificacoes(id);

ALTER TABLE verificacoes_normas_infracoes
    ADD CONSTRAINT fk_vni_normas_id FOREIGN KEY (normas_id) REFERENCES verificacoes_normas(id);

ALTER TABLE veredictos_finais
    ADD CONSTRAINT fk_veredictos_verificacao_id FOREIGN KEY (verificacao_id) REFERENCES verificacoes(id);

ALTER TABLE pesquisas_avulsas
    ADD CONSTRAINT fk_pesquisas_avulsas_utilizador_id FOREIGN KEY (utilizador_id) REFERENCES utilizadores(id);

ALTER TABLE sessoes_pesquisa
    ADD CONSTRAINT fk_sessoes_pesquisa_utilizador_id FOREIGN KEY (utilizador_id) REFERENCES utilizadores(id);

ALTER TABLE resultados_pesquisa
    ADD CONSTRAINT fk_resultados_pesquisa_sessao_id FOREIGN KEY (sessao_id) REFERENCES sessoes_pesquisa(id);
