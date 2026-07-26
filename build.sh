#!/usr/bin/env bash
# build.sh - Script de build para Render.com (PostgreSQL)

set -e

echo "🔨 A instalar dependências..."
pip install -r requirements.txt

echo "🗄️ A executar schema da base de dados PostgreSQL..."
python -c "
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

database_url = os.getenv('DATABASE_URL')
if database_url:
    db = psycopg2.connect(database_url)
else:
    db = psycopg2.connect(
        host=os.getenv('PGHOST', 'localhost'),
        user=os.getenv('PGUSER', 'postgres'),
        password=os.getenv('PGPASSWORD', ''),
        dbname=os.getenv('PGDATABASE', 'plagio'),
        port=os.getenv('PGPORT', '5432')
    )

try:
    cur = db.cursor()
    
    # Ler e executar schema PostgreSQL
    schema_path = os.path.join(os.path.dirname(__file__), 'db', 'schema_postgresql.sql')
    if os.path.exists(schema_path):
        print('  ▶ A executar schema_postgresql.sql...')
        with open(schema_path, 'r', encoding='utf-8') as sql_file:
            sql = sql_file.read()
            for statement in sql.split(';'):
                statement = statement.strip()
                if statement:
                    try:
                        cur.execute(statement)
                    except Exception as e:
                        # Ignorar erros de tabelas já existentes
                        if 'already exists' not in str(e).lower():
                            print(f'    ⚠ Aviso: {e}')
        db.commit()
        print('✅ Schema executado com sucesso!')
    else:
        print('⚠ schema_postgresql.sql não encontrado')

    cur.close()
    db.close()
except Exception as e:
    print(f'⚠ Aviso na migração: {e}')
"

echo "👤 A verificar/criar administrador..."
python -c "
import os
import psycopg2
from dotenv import load_dotenv
from flask_bcrypt import generate_password_hash

load_dotenv()

database_url = os.getenv('DATABASE_URL')
if database_url:
    db = psycopg2.connect(database_url)
else:
    db = psycopg2.connect(
        host=os.getenv('PGHOST', 'localhost'),
        user=os.getenv('PGUSER', 'postgres'),
        password=os.getenv('PGPASSWORD', ''),
        dbname=os.getenv('PGDATABASE', 'plagio'),
        port=os.getenv('PGPORT', '5432')
    )

ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'jorgedange@gmail.com')
ADMIN_PASS  = os.getenv('ADMIN_PASS', 'Develop/28')

try:
    cur = db.cursor()
    cur.execute(\"SELECT COUNT(*) FROM utilizadores WHERE papel = 'admin'\")
    count = cur.fetchone()[0]
    if count == 0:
        pw_hash = generate_password_hash(ADMIN_PASS).decode('utf-8')
        cur.execute(
            \"INSERT INTO utilizadores (nome, email, password_hash, papel) VALUES (%s, %s, %s, %s)\",
            ('Administrador', ADMIN_EMAIL, pw_hash, 'admin')
        )
        db.commit()
        print(f'  ✅ Administrador criado: {ADMIN_EMAIL}')
    else:
        print(f'  ✅ {count} administrador(es) encontrado(s)')
    cur.close()
    db.close()
except Exception as e:
    print(f'  ⚠ Aviso: {e}')
"

echo "✅ Build concluído!"
