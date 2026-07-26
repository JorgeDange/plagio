-- ============================================================
-- IMETRO TFC v3 — Schema Completo do Banco de Dados
-- MySQL / InnoDB / utf8mb4
-- Gerado: 2026-07-25
-- ============================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ============================================================
-- 1. TABELAS SEM FOREIGN KEYS
-- ============================================================

CREATE TABLE IF NOT EXISTS `cursos` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `nome` VARCHAR(200) NOT NULL UNIQUE,
    `codigo` VARCHAR(20),
    `departamento` VARCHAR(200),
    `descricao` TEXT,
    `data_criacao` TEXT NOT NULL,
    `activo` INT DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `orientadores` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `nome` VARCHAR(200) NOT NULL,
    `email` VARCHAR(200),
    `titulacao` VARCHAR(100),
    `curso_id` INT,
    `activo` INT DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `utilizadores` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `nome` VARCHAR(200) NOT NULL,
    `email` VARCHAR(200) NOT NULL UNIQUE,
    `password_hash` TEXT NOT NULL,
    `papel` VARCHAR(20) NOT NULL,
    `ativo` INT NOT NULL DEFAULT 1,
    `criado_em` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `ultimo_login` TIMESTAMP NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `configuracoes` (
    `chave` VARCHAR(200) PRIMARY KEY,
    `valor` VARCHAR(500)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `config_pesquisa_externa` (
    `chave` VARCHAR(200) PRIMARY KEY,
    `valor` VARCHAR(500) NOT NULL,
    `descricao` VARCHAR(500)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `tcc_validos` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `titulo` TEXT NOT NULL,
    `autor` VARCHAR(200) NOT NULL,
    `orientador_id` INT,
    `orientador_nome` VARCHAR(200) DEFAULT '',
    `curso_id` INT,
    `curso_nome` VARCHAR(200) DEFAULT '',
    `ano_defesa` INT,
    `semestre` VARCHAR(20) DEFAULT '',
    `palavras_chave` TEXT,
    `resumo` TEXT,
    `nota_final` REAL,
    `data_indexacao` TEXT NOT NULL,
    `num_chunks` INT DEFAULT 0,
    `caminho_ficheiro` TEXT,
    `chroma_id` VARCHAR(100) UNIQUE,
    `tem_capa` INT DEFAULT 0,
    `tem_folha_rosto` INT DEFAULT 0,
    `tem_resumo` INT DEFAULT 0,
    `tem_abstract` INT DEFAULT 0,
    `tem_sumario` INT DEFAULT 0,
    `tem_referencias` INT DEFAULT 0,
    `score_abnt` REAL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `tcc_suspeitos` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `titulo` TEXT,
    `autor` VARCHAR(200) NOT NULL,
    `orientador_id` INT,
    `orientador_nome` VARCHAR(200) DEFAULT '',
    `curso_id` INT,
    `curso_nome` VARCHAR(200) DEFAULT '',
    `ano_submissao` INT,
    `estado` VARCHAR(20) DEFAULT 'pendente',
    `data_submissao` TEXT NOT NULL,
    `caminho_ficheiro` TEXT NOT NULL,
    `ultima_verificacao_id` INT,
    `ultima_pct_plagio` REAL,
    `ultimo_nivel` VARCHAR(20) DEFAULT '',
    `aprovado_por` INT,
    `aprovado_em` TIMESTAMP NULL,
    `nota_aprovacao` VARCHAR(50)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `verificacoes` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `tcc_suspeito_id` INT,
    `curso_id_filtro` INT,
    `curso_nome_filtro` VARCHAR(200) DEFAULT '',
    `limiar_usado` REAL NOT NULL,
    `percentagem_plagio` REAL DEFAULT 0.0,
    `nivel` VARCHAR(20) DEFAULT 'Baixo',
    `num_chunks_total` INT DEFAULT 0,
    `num_chunks_suspeitos` INT DEFAULT 0,
    `data` TEXT NOT NULL,
    `duracao_segundos` REAL DEFAULT 0,
    `caminho_relatorio` TEXT,
    `score_abnt` REAL DEFAULT 0,
    `observacoes` TEXT,
    `score_apa` REAL DEFAULT 0,
    `nivel_ia` VARCHAR(20) DEFAULT '',
    `analise_ia_ok` INT DEFAULT 0,
    `normas_incluidas` INT NOT NULL DEFAULT 0,
    `normas_ia_incluida` INT NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `pesquisas_avulsas` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `utilizador_id` INT,
    `tipo_entrada` VARCHAR(50) NOT NULL,
    `texto_consulta` TEXT NOT NULL,
    `fontes_usadas` TEXT,
    `total_resultados` INT DEFAULT 0,
    `exportado_csv` INT DEFAULT 0,
    `exportado_pdf` INT DEFAULT 0,
    `criado_em` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================
-- 2. TABELAS COM FOREIGN KEYS
-- ============================================================

CREATE TABLE IF NOT EXISTS `matches` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `verificacao_id` INT,
    `tcc_valido_id` INT,
    `tcc_valido_titulo` TEXT,
    `tcc_valido_autor` TEXT,
    `num_chunks_comuns` INT DEFAULT 0,
    `similaridade_max` REAL DEFAULT 0,
    `similaridade_media` REAL DEFAULT 0,
    `contribuicao_pct` REAL DEFAULT 0,
    `fonte_tipo` VARCHAR(20) DEFAULT 'interno',
    `fonte_externa_id` INT,
    `fonte_origem` VARCHAR(50) NOT NULL DEFAULT 'desconhecida',
    `titulo_fonte` VARCHAR(500) NULL,
    `url_fonte` VARCHAR(1000) NULL,
    `trecho_similar` TEXT NULL,
    `trecho_original` TEXT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `chunks_suspeitos` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `verificacao_id` INT,
    `match_id` INT,
    `posicao_chunk` INT,
    `texto_suspeito` TEXT,
    `texto_origem` TEXT,
    `similaridade` REAL DEFAULT 0,
    `secao_estimada` VARCHAR(50) DEFAULT ''
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `fontes_externas` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `verificacao_id` INT NOT NULL,
    `chunk_suspeito_id` INT,
    `api_fonte` VARCHAR(50) NOT NULL,
    `titulo_externo` TEXT,
    `autores` TEXT,
    `ano` INT,
    `resumo_externo` TEXT,
    `url_externo` TEXT,
    `score_similaridade` REAL,
    `chunk_texto` TEXT,
    `criado_em` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `fontes_externas_resultados` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `verificacao_id` INT,
    `chunk_id` INT,
    `fonte` VARCHAR(50) NOT NULL,
    `titulo_externo` TEXT NOT NULL,
    `autores` TEXT,
    `ano_publicacao` INT,
    `doi` VARCHAR(200),
    `url_fonte` TEXT,
    `resumo_externo` TEXT,
    `score_semantico` REAL NOT NULL,
    `pesquisa_id` INT,
    `criado_em` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `analises_ia` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `verificacao_id` INT NOT NULL,
    `chunk_id` INT NOT NULL,
    `plagio` INT NOT NULL DEFAULT 0,
    `nivel` VARCHAR(20) DEFAULT '',
    `tipo` VARCHAR(20) DEFAULT '',
    `similaridade_llm` INT DEFAULT 0,
    `score_labse` REAL DEFAULT 0,
    `justificativa` TEXT,
    `modelo_usado` VARCHAR(100) DEFAULT '',
    `tempo_ms` INT DEFAULT 0,
    `erro` TEXT,
    `criado_em` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY `uq_analise` (`verificacao_id`, `chunk_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `verificacoes_normas` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `verificacao_id` INT NOT NULL UNIQUE,
    `local_executada` INT NOT NULL DEFAULT 0,
    `local_total_regras` INT DEFAULT 0,
    `local_regras_ok` INT DEFAULT 0,
    `local_regras_falhou` INT DEFAULT 0,
    `local_percentagem` REAL DEFAULT 0.0,
    `local_resultado_json` TEXT,
    `ia_executada` INT NOT NULL DEFAULT 0,
    `ia_pontuacao_total` INT DEFAULT NULL,
    `ia_classificacao` VARCHAR(50) DEFAULT NULL,
    `ia_num_infracoes` INT DEFAULT 0,
    `ia_tem_bloqueante` INT DEFAULT 0,
    `ia_resultado_json` TEXT,
    `classificacao_final` VARCHAR(30) NOT NULL DEFAULT 'PENDENTE',
    `requer_correcao` INT NOT NULL DEFAULT 0,
    `resumo_problemas` TEXT,
    `criado_em` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `atualizado_em` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `verificacoes_normas_infracoes` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `normas_id` INT NOT NULL,
    `codigo` VARCHAR(50) NOT NULL,
    `origem` VARCHAR(10) NOT NULL,
    `gravidade` VARCHAR(20) NOT NULL,
    `elemento` VARCHAR(100) NOT NULL,
    `descricao` TEXT NOT NULL,
    `recomendacao` TEXT,
    `norma_violada` TEXT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `veredictos_finais` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `verificacao_id` INT NOT NULL UNIQUE,
    `data_geracao` TEXT NOT NULL,
    `score_global` REAL NOT NULL DEFAULT 0,
    `classificacao` VARCHAR(50) NOT NULL DEFAULT 'Sem plagio',
    `tipo_predominante` VARCHAR(50),
    `gravidade` VARCHAR(20),
    `conclusao_ia` TEXT,
    `modelo_ia_usado` VARCHAR(100),
    `chunks_analisados` INT NOT NULL DEFAULT 0,
    `gerado_por_ia` INT NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `embeddings_chunks` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `tcc_id` INT NOT NULL,
    `tipo` ENUM('valido','suspeito') NOT NULL,
    `chunk_texto` TEXT NOT NULL,
    `vector` JSON NOT NULL,
    `criado_em` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `sessoes_pesquisa` (
    `id` VARCHAR(100) PRIMARY KEY,
    `utilizador_id` INT,
    `modo_entrada` VARCHAR(50) NOT NULL,
    `texto_original` TEXT,
    `nome_ficheiro` VARCHAR(500),
    `filtros_json` TEXT,
    `estado` VARCHAR(20) DEFAULT 'a_processar',
    `total_resultados` INT DEFAULT 0,
    `tempo_segundos` REAL,
    `criado_em` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `resultados_pesquisa` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `sessao_id` VARCHAR(100),
    `api_fonte` VARCHAR(50) NOT NULL,
    `titulo` TEXT NOT NULL,
    `autores` TEXT,
    `ano` INT,
    `resumo` TEXT,
    `url` TEXT,
    `score_labse` REAL,
    `chunk_origem` TEXT,
    `posicao_ranking` INT,
    `criado_em` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================
-- 3. INDEXES
-- ============================================================

-- fontes_externas_resultados
CREATE INDEX IF NOT EXISTS `idx_fontes_ext_verificacao` ON `fontes_externas_resultados`(`verificacao_id`);
CREATE INDEX IF NOT EXISTS `idx_fontes_ext_score` ON `fontes_externas_resultados`(`score_semantico` DESC);
CREATE INDEX IF NOT EXISTS `idx_fontes_ext_pesquisa` ON `fontes_externas_resultados`(`pesquisa_id`);

-- pesquisas_avulsas
CREATE INDEX IF NOT EXISTS `idx_pesquisas_avulsas_user` ON `pesquisas_avulsas`(`utilizador_id`);

-- verificacoes_normas
CREATE INDEX IF NOT EXISTS `idx_vn_verificacao` ON `verificacoes_normas`(`verificacao_id`);

-- verificacoes_normas_infracoes
CREATE INDEX IF NOT EXISTS `idx_vni_normas` ON `verificacoes_normas_infracoes`(`normas_id`);
CREATE INDEX IF NOT EXISTS `idx_vni_gravidade` ON `verificacoes_normas_infracoes`(`gravidade`);
CREATE INDEX IF NOT EXISTS `idx_vni_origem` ON `verificacoes_normas_infracoes`(`origem`);

-- veredictos_finais
CREATE INDEX IF NOT EXISTS `idx_veredictos_verificacao` ON `veredictos_finais`(`verificacao_id`);

-- embeddings_chunks
CREATE INDEX IF NOT EXISTS `idx_tcc` ON `embeddings_chunks`(`tcc_id`, `tipo`);

-- ============================================================
-- 4. FOREIGN KEYS
-- ============================================================

ALTER TABLE `orientadores`
    ADD CONSTRAINT `fk_orientadores_curso_id` FOREIGN KEY (`curso_id`) REFERENCES `cursos`(`id`);

ALTER TABLE `tcc_validos`
    ADD CONSTRAINT `fk_tcc_validos_orientador_id` FOREIGN KEY (`orientador_id`) REFERENCES `orientadores`(`id`),
    ADD CONSTRAINT `fk_tcc_validos_curso_id` FOREIGN KEY (`curso_id`) REFERENCES `cursos`(`id`);

ALTER TABLE `tcc_suspeitos`
    ADD CONSTRAINT `fk_tcc_suspeitos_orientador_id` FOREIGN KEY (`orientador_id`) REFERENCES `orientadores`(`id`),
    ADD CONSTRAINT `fk_tcc_suspeitos_curso_id` FOREIGN KEY (`curso_id`) REFERENCES `cursos`(`id`),
    ADD CONSTRAINT `fk_tcc_suspeitos_aprovado_por` FOREIGN KEY (`aprovado_por`) REFERENCES `utilizadores`(`id`);

ALTER TABLE `verificacoes`
    ADD CONSTRAINT `fk_verificacoes_tcc_suspeito_id` FOREIGN KEY (`tcc_suspeito_id`) REFERENCES `tcc_suspeitos`(`id`),
    ADD CONSTRAINT `fk_verificacoes_curso_id_filtro` FOREIGN KEY (`curso_id_filtro`) REFERENCES `cursos`(`id`);

ALTER TABLE `chunks_suspeitos`
    ADD CONSTRAINT `fk_chunks_suspeitos_verificacao_id` FOREIGN KEY (`verificacao_id`) REFERENCES `verificacoes`(`id`),
    ADD CONSTRAINT `fk_chunks_suspeitos_match_id` FOREIGN KEY (`match_id`) REFERENCES `matches`(`id`);

ALTER TABLE `fontes_externas`
    ADD CONSTRAINT `fk_fontes_externas_verificacao_id` FOREIGN KEY (`verificacao_id`) REFERENCES `verificacoes`(`id`),
    ADD CONSTRAINT `fk_fontes_externas_chunk_suspeito_id` FOREIGN KEY (`chunk_suspeito_id`) REFERENCES `chunks_suspeitos`(`id`);

ALTER TABLE `matches`
    ADD CONSTRAINT `fk_matches_verificacao_id` FOREIGN KEY (`verificacao_id`) REFERENCES `verificacoes`(`id`),
    ADD CONSTRAINT `fk_matches_tcc_valido_id` FOREIGN KEY (`tcc_valido_id`) REFERENCES `tcc_validos`(`id`),
    ADD CONSTRAINT `fk_matches_fonte_externa_id` FOREIGN KEY (`fonte_externa_id`) REFERENCES `fontes_externas`(`id`);

ALTER TABLE `fontes_externas_resultados`
    ADD CONSTRAINT `fk_fer_verificacao_id` FOREIGN KEY (`verificacao_id`) REFERENCES `verificacoes`(`id`),
    ADD CONSTRAINT `fk_fer_chunk_id` FOREIGN KEY (`chunk_id`) REFERENCES `chunks_suspeitos`(`id`),
    ADD CONSTRAINT `fk_fer_pesquisa_id` FOREIGN KEY (`pesquisa_id`) REFERENCES `pesquisas_avulsas`(`id`);

ALTER TABLE `analises_ia`
    ADD CONSTRAINT `fk_analises_ia_verificacao_id` FOREIGN KEY (`verificacao_id`) REFERENCES `verificacoes`(`id`),
    ADD CONSTRAINT `fk_analises_ia_chunk_id` FOREIGN KEY (`chunk_id`) REFERENCES `chunks_suspeitos`(`id`);

ALTER TABLE `verificacoes_normas`
    ADD CONSTRAINT `fk_vn_verificacao_id` FOREIGN KEY (`verificacao_id`) REFERENCES `verificacoes`(`id`);

ALTER TABLE `verificacoes_normas_infracoes`
    ADD CONSTRAINT `fk_vni_normas_id` FOREIGN KEY (`normas_id`) REFERENCES `verificacoes_normas`(`id`);

ALTER TABLE `veredictos_finais`
    ADD CONSTRAINT `fk_veredictos_verificacao_id` FOREIGN KEY (`verificacao_id`) REFERENCES `verificacoes`(`id`);

ALTER TABLE `pesquisas_avulsas`
    ADD CONSTRAINT `fk_pesquisas_avulsas_utilizador_id` FOREIGN KEY (`utilizador_id`) REFERENCES `utilizadores`(`id`);

ALTER TABLE `sessoes_pesquisa`
    ADD CONSTRAINT `fk_sessoes_pesquisa_utilizador_id` FOREIGN KEY (`utilizador_id`) REFERENCES `utilizadores`(`id`);

ALTER TABLE `resultados_pesquisa`
    ADD CONSTRAINT `fk_resultados_pesquisa_sessao_id` FOREIGN KEY (`sessao_id`) REFERENCES `sessoes_pesquisa`(`id`);

SET FOREIGN_KEY_CHECKS = 1;
