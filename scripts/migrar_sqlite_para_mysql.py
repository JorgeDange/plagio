"""
Script de Migração: SQLite -> MySQL
Migra todas as tabelas do instance/plagio.db para o MySQL plagio.
"""
import os
import sys
import sqlite3
import mysql.connector
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from dotenv import load_dotenv
load_dotenv()

SQLITE_PATH = os.path.join('instance', 'plagio.db')
MYSQL_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', 'devs'),
    'database': os.getenv('MYSQL_DB', 'plagio'),
    'charset': 'utf8mb4',
}

# Tabelas sem foreign keys (criar primeiro)
TABLES_NO_FK = {
    "cursos": "id INT AUTO_INCREMENT PRIMARY KEY, nome VARCHAR(200) NOT NULL UNIQUE, codigo VARCHAR(20), departamento VARCHAR(200), descricao TEXT, data_criacao TEXT NOT NULL, activo INT DEFAULT 1",
    "orientadores": "id INT AUTO_INCREMENT PRIMARY KEY, nome VARCHAR(200) NOT NULL, email VARCHAR(200), titulacao VARCHAR(100), curso_id INT, activo INT DEFAULT 1",
    "utilizadores": "id INT AUTO_INCREMENT PRIMARY KEY, nome VARCHAR(200) NOT NULL, email VARCHAR(200) NOT NULL UNIQUE, password_hash TEXT NOT NULL, papel VARCHAR(20) NOT NULL, ativo INT NOT NULL DEFAULT 1, criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP, ultimo_login TIMESTAMP NULL",
    "configuracoes": "chave VARCHAR(200) PRIMARY KEY, valor VARCHAR(500)",
    "config_pesquisa_externa": "chave VARCHAR(200) PRIMARY KEY, valor VARCHAR(500) NOT NULL, descricao VARCHAR(500)",
    "tcc_validos": "id INT AUTO_INCREMENT PRIMARY KEY, titulo TEXT NOT NULL, autor VARCHAR(200) NOT NULL, orientador_id INT, orientador_nome VARCHAR(200) DEFAULT '', curso_id INT, curso_nome VARCHAR(200) DEFAULT '', ano_defesa INT, semestre VARCHAR(20) DEFAULT '', palavras_chave TEXT, resumo TEXT, nota_final REAL, data_indexacao TEXT NOT NULL, num_chunks INT DEFAULT 0, caminho_ficheiro TEXT, chroma_id VARCHAR(100) UNIQUE, tem_capa INT DEFAULT 0, tem_folha_rosto INT DEFAULT 0, tem_resumo INT DEFAULT 0, tem_abstract INT DEFAULT 0, tem_sumario INT DEFAULT 0, tem_referencias INT DEFAULT 0, score_abnt REAL DEFAULT 0",
    "tcc_suspeitos": "id INT AUTO_INCREMENT PRIMARY KEY, titulo TEXT, autor VARCHAR(200) NOT NULL, orientador_id INT, orientador_nome VARCHAR(200) DEFAULT '', curso_id INT, curso_nome VARCHAR(200) DEFAULT '', ano_submissao INT, estado VARCHAR(20) DEFAULT 'pendente', data_submissao TEXT NOT NULL, caminho_ficheiro TEXT NOT NULL, ultima_verificacao_id INT, ultima_pct_plagio REAL, ultimo_nivel VARCHAR(20) DEFAULT '', aprovado_por INT, aprovado_em TIMESTAMP NULL, nota_aprovacao VARCHAR(50)",
    "verificacoes": "id INT AUTO_INCREMENT PRIMARY KEY, tcc_suspeito_id INT, curso_id_filtro INT, curso_nome_filtro VARCHAR(200) DEFAULT '', limiar_usado REAL NOT NULL, percentagem_plagio REAL DEFAULT 0.0, nivel VARCHAR(20) DEFAULT 'Baixo', num_chunks_total INT DEFAULT 0, num_chunks_suspeitos INT DEFAULT 0, data TEXT NOT NULL, duracao_segundos REAL DEFAULT 0, caminho_relatorio TEXT, score_abnt REAL DEFAULT 0, observacoes TEXT, score_apa REAL DEFAULT 0, nivel_ia VARCHAR(20) DEFAULT '', analise_ia_ok INT DEFAULT 0, normas_incluidas INT NOT NULL DEFAULT 0, normas_ia_incluida INT NOT NULL DEFAULT 0",
    "pesquisas_avulsas": "id INT AUTO_INCREMENT PRIMARY KEY, utilizador_id INT, tipo_entrada VARCHAR(50) NOT NULL, texto_consulta TEXT NOT NULL, fontes_usadas TEXT, total_resultados INT DEFAULT 0, exportado_csv INT DEFAULT 0, exportado_pdf INT DEFAULT 0, criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
}

# Tabelas com foreign keys
TABLES_FK = {
    "chunks_suspeitos": "id INT AUTO_INCREMENT PRIMARY KEY, verificacao_id INT, match_id INT, posicao_chunk INT, texto_suspeito TEXT, texto_origem TEXT, similaridade REAL DEFAULT 0, secao_estimada VARCHAR(50) DEFAULT ''",
    "fontes_externas": "id INT AUTO_INCREMENT PRIMARY KEY, verificacao_id INT NOT NULL, chunk_suspeito_id INT, api_fonte VARCHAR(50) NOT NULL, titulo_externo TEXT, autores TEXT, ano INT, resumo_externo TEXT, url_externo TEXT, score_similaridade REAL, chunk_texto TEXT, criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
    "matches": "id INT AUTO_INCREMENT PRIMARY KEY, verificacao_id INT, tcc_valido_id INT, tcc_valido_titulo TEXT, tcc_valido_autor TEXT, num_chunks_comuns INT DEFAULT 0, similaridade_max REAL DEFAULT 0, similaridade_media REAL DEFAULT 0, contribuicao_pct REAL DEFAULT 0, fonte_tipo VARCHAR(20) DEFAULT 'interno', fonte_externa_id INT",
    "fontes_externas_resultados": "id INT AUTO_INCREMENT PRIMARY KEY, verificacao_id INT, chunk_id INT, fonte VARCHAR(50) NOT NULL, titulo_externo TEXT NOT NULL, autores TEXT, ano_publicacao INT, doi VARCHAR(200), url_fonte TEXT, resumo_externo TEXT, score_semantico REAL NOT NULL, pesquisa_id INT, criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
    "analises_ia": "id INT AUTO_INCREMENT PRIMARY KEY, verificacao_id INT NOT NULL, chunk_id INT NOT NULL, plagio INT NOT NULL DEFAULT 0, nivel VARCHAR(20) DEFAULT '', tipo VARCHAR(20) DEFAULT '', similaridade_llm INT DEFAULT 0, score_labse REAL DEFAULT 0, justificativa TEXT, modelo_usado VARCHAR(100) DEFAULT '', tempo_ms INT DEFAULT 0, erro TEXT, criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP, UNIQUE KEY uq_analise (verificacao_id, chunk_id)",
    "verificacoes_normas": "id INT AUTO_INCREMENT PRIMARY KEY, verificacao_id INT NOT NULL UNIQUE, local_executada INT NOT NULL DEFAULT 0, local_total_regras INT DEFAULT 0, local_regras_ok INT DEFAULT 0, local_regras_falhou INT DEFAULT 0, local_percentagem REAL DEFAULT 0.0, local_resultado_json TEXT, ia_executada INT NOT NULL DEFAULT 0, ia_pontuacao_total INT DEFAULT NULL, ia_classificacao VARCHAR(50) DEFAULT NULL, ia_num_infracoes INT DEFAULT 0, ia_tem_bloqueante INT DEFAULT 0, ia_resultado_json TEXT, classificacao_final VARCHAR(30) NOT NULL DEFAULT 'PENDENTE', requer_correcao INT NOT NULL DEFAULT 0, resumo_problemas TEXT, criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP, atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP",
    "verificacoes_normas_infracoes": "id INT AUTO_INCREMENT PRIMARY KEY, normas_id INT NOT NULL, codigo VARCHAR(50) NOT NULL, origem VARCHAR(10) NOT NULL, gravidade VARCHAR(20) NOT NULL, elemento VARCHAR(100) NOT NULL, descricao TEXT NOT NULL, recomendacao TEXT, norma_violada TEXT",
    "veredictos_finais": "id INT AUTO_INCREMENT PRIMARY KEY, verificacao_id INT NOT NULL UNIQUE, data_geracao TEXT NOT NULL, score_global REAL NOT NULL DEFAULT 0, classificacao VARCHAR(50) NOT NULL DEFAULT 'Sem plagio', tipo_predominante VARCHAR(50), gravidade VARCHAR(20), conclusao_ia TEXT, modelo_ia_usado VARCHAR(100), chunks_analisados INT NOT NULL DEFAULT 0, gerado_por_ia INT NOT NULL DEFAULT 0",
    "sessoes_pesquisa": "id VARCHAR(100) PRIMARY KEY, utilizador_id INT, modo_entrada VARCHAR(50) NOT NULL, texto_original TEXT, nome_ficheiro VARCHAR(500), filtros_json TEXT, estado VARCHAR(20) DEFAULT 'a_processar', total_resultados INT DEFAULT 0, tempo_segundos REAL, criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
    "resultados_pesquisa": "id INT AUTO_INCREMENT PRIMARY KEY, sessao_id VARCHAR(100), api_fonte VARCHAR(50) NOT NULL, titulo TEXT NOT NULL, autores TEXT, ano INT, resumo TEXT, url TEXT, score_labse REAL, chunk_origem TEXT, posicao_ranking INT, criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
}

# Foreign keys a adicionar
FKS = [
    ("orientadores", "curso_id", "cursos", "id"),
    ("tcc_validos", "orientador_id", "orientadores", "id"),
    ("tcc_validos", "curso_id", "cursos", "id"),
    ("tcc_suspeitos", "orientador_id", "orientadores", "id"),
    ("tcc_suspeitos", "curso_id", "cursos", "id"),
    ("tcc_suspeitos", "aprovado_por", "utilizadores", "id"),
    ("verificacoes", "tcc_suspeito_id", "tcc_suspeitos", "id"),
    ("verificacoes", "curso_id_filtro", "cursos", "id"),
    ("chunks_suspeitos", "verificacao_id", "verificacoes", "id"),
    ("chunks_suspeitos", "match_id", "matches", "id"),
    ("fontes_externas", "verificacao_id", "verificacoes", "id"),
    ("fontes_externas", "chunk_suspeito_id", "chunks_suspeitos", "id"),
    ("matches", "verificacao_id", "verificacoes", "id"),
    ("matches", "tcc_valido_id", "tcc_validos", "id"),
    ("matches", "fonte_externa_id", "fontes_externas", "id"),
    ("fontes_externas_resultados", "verificacao_id", "verificacoes", "id"),
    ("fontes_externas_resultados", "chunk_id", "chunks_suspeitos", "id"),
    ("fontes_externas_resultados", "pesquisa_id", "pesquisas_avulsas", "id"),
    ("analises_ia", "verificacao_id", "verificacoes", "id"),
    ("analises_ia", "chunk_id", "chunks_suspeitos", "id"),
    ("verificacoes_normas", "verificacao_id", "verificacoes", "id"),
    ("verificacoes_normas_infracoes", "normas_id", "verificacoes_normas", "id"),
    ("veredictos_finais", "verificacao_id", "verificacoes", "id"),
    ("pesquisas_avulsas", "utilizador_id", "utilizadores", "id"),
    ("sessoes_pesquisa", "utilizador_id", "utilizadores", "id"),
    ("resultados_pesquisa", "sessao_id", "sessoes_pesquisa", "id"),
]

SKIP_TABLES = {'sqlite_sequence', 'verificacoes_v2', 'matches_v2', 'chunks_suspeitos_v2', 'analises_ia_v2', 'tcc_validos_err', 'tcc_suspeitos_err'}


def criar_tabelas(mysql_conn):
    cur = mysql_conn.cursor()
    print("  [sem FK]")
    for nome, cols in TABLES_NO_FK.items():
        cur.execute(f"CREATE TABLE IF NOT EXISTS `{nome}` ({cols}) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4")
    print("  [com FK]")
    for nome, cols in TABLES_FK.items():
        cur.execute(f"CREATE TABLE IF NOT EXISTS `{nome}` ({cols}) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4")
    mysql_conn.commit()
    cur.close()


def adicionar_fks(mysql_conn):
    cur = mysql_conn.cursor()
    for tabela, col, ref_tabela, ref_col in FKS:
        nome_fk = f"fk_{tabela}_{col}"
        try:
            cur.execute(f"ALTER TABLE `{tabela}` ADD CONSTRAINT `{nome_fk}` FOREIGN KEY (`{col}`) REFERENCES `{ref_tabela}`(`{ref_col}`)")
        except mysql.connector.Error as e:
            if 'Duplicate' not in str(e) and 'already exists' not in str(e):
                print(f"    FK {nome_fk}: {e}")
    mysql_conn.commit()
    cur.close()


def migrar_tabela(sqlite_conn, mysql_conn, tabela):
    try:
        rows = sqlite_conn.execute(f"SELECT * FROM [{tabela}]").fetchall()
        if not rows:
            print(f"  {tabela}: vazia")
            return 0
        cols = [desc[0] for desc in sqlite_conn.execute(f"SELECT * FROM [{tabela}]").description]
        cur = mysql_conn.cursor()
        placeholders = ', '.join(['%s'] * len(cols))
        col_names = ', '.join([f'`{c}`' for c in cols])
        sql = f"INSERT IGNORE INTO `{tabela}` ({col_names}) VALUES ({placeholders})"
        inserted = 0
        for row in rows:
            try:
                cur.execute(sql, list(row))
                inserted += 1
            except mysql.connector.Error as e:
                if 'Duplicate' not in str(e):
                    pass
        mysql_conn.commit()
        cur.close()
        print(f"  {tabela}: {inserted}/{len(rows)}")
        return inserted
    except Exception as e:
        print(f"  {tabela}: ERRO - {e}")
        return 0


def main():
    if not os.path.exists(SQLITE_PATH):
        print(f"ERRO: {SQLITE_PATH} nao encontrado")
        sys.exit(1)

    print("=" * 60)
    print("MIGRACAO: SQLite -> MySQL")
    print("=" * 60)

    sqlite_conn = sqlite3.connect(SQLITE_PATH)
    try:
        mysql_conn = mysql.connector.connect(**MYSQL_CONFIG)
    except mysql.connector.Error as e:
        print(f"ERRO MySQL: {e}")
        sys.exit(1)

    print("\n[1] Criar tabelas...")
    criar_tabelas(mysql_conn)

    print("\n[2] Migrar dados...")
    all_tables = list(TABLES_NO_FK.keys()) + list(TABLES_FK.keys())
    total = 0
    for t in all_tables:
        total += migrar_tabela(sqlite_conn, mysql_conn, t)

    # Migrar embeddings_chunks (já existe mas pode ter dados)
    migrar_tabela(sqlite_conn, mysql_conn, 'embeddings_chunks')

    print("\n[3] Adicionar foreign keys...")
    adicionar_fks(mysql_conn)

    print("\n[4] Verificar...")
    cur = mysql_conn.cursor()
    cur.execute("SHOW TABLES")
    tabelas = sorted([r[0] for r in cur.fetchall()])
    for t in tabelas:
        cur.execute(f"SELECT COUNT(*) FROM `{t}`")
        count = cur.fetchone()[0]
        print(f"  {t:40s} {count:>6d}")
    cur.close()

    sqlite_conn.close()
    mysql_conn.close()
    print(f"\nMIGRACAO CONCLUIDA! Total: {total} registos")


if __name__ == "__main__":
    main()
