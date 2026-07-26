-- V10: Adicionar evidência de similaridade à tabela matches
-- Cada match agora carrega: fonte, título, URL, trechos comparados

ALTER TABLE matches
  ADD COLUMN fonte_origem VARCHAR(50) NOT NULL DEFAULT 'desconhecida' AFTER fonte_externa_id,
  ADD COLUMN titulo_fonte VARCHAR(500) NULL AFTER fonte_origem,
  ADD COLUMN url_fonte VARCHAR(1000) NULL AFTER titulo_fonte,
  ADD COLUMN trecho_similar TEXT NULL AFTER url_fonte,
  ADD COLUMN trecho_original TEXT NULL AFTER trecho_similar;

-- Atualizar matches existentes com dados de fontes_externas_resultados
UPDATE matches m
JOIN fontes_externas_resultados fer ON fer.id = m.fonte_externa_id
SET m.fonte_origem = fer.fonte,
    m.titulo_fonte = fer.titulo_externo,
    m.url_fonte = fer.url_fonte,
    m.trecho_similar = fer.resumo_externo
WHERE m.fonte_externa_id IS NOT NULL;

-- Para matches internos (tcc_validos), preencher titulo_fonte
UPDATE matches m
JOIN tcc_validos tv ON tv.id = m.tcc_valido_id
SET m.titulo_fonte = tv.titulo,
    m.fonte_origem = 'local'
WHERE m.fonte_tipo = 'interno' AND m.tcc_valido_id IS NOT NULL;
