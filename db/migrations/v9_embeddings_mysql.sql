CREATE TABLE embeddings_chunks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tcc_id INT NOT NULL,
    tipo ENUM('valido','suspeito') NOT NULL,
    chunk_texto TEXT NOT NULL,
    vector JSON NOT NULL,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_tcc (tcc_id, tipo)
) ENGINE=InnoDB;