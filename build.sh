#!/usr/bin/env bash
# build.sh - Script de build para Render.com (PostgreSQL)

set -e

echo "🔨 A instalar dependências..."
pip install -r requirements.txt

echo "🗄️ A executar migrações da base de dados..."
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

    # Ler e executar ficheiros de migração
    migrations_dir = os.path.join(os.path.dirname(__file__), 'db', 'migrations')
    if os.path.exists(migrations_dir):
        for f in sorted(os.listdir(migrations_dir)):
            if f.endswith('.sql'):
                filepath = os.path.join(migrations_dir, f)
                print(f'  ▶ A executar {f}...')
                with open(filepath, 'r', encoding='utf-8') as sql_file:
                    sql = sql_file.read()
                    for statement in sql.split(';'):
                        statement = statement.strip()
                        if statement:
                            try:
                                cur.execute(statement)
                            except Exception as e:
                                print(f'    ⚠ Aviso: {e}')
                db.commit()
        print('✅ Migrações concluídas!')
    else:
        print('⚠ Directorio de migrações não encontrado')

    cur.close()
    db.close()
except Exception as e:
    print(f'⚠ Aviso na migração: {e}')
"

echo "👤 A verificar administrador..."
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
    cur.execute(\"SELECT COUNT(*) FROM utilizadores WHERE papel = 'admin'\")
    count = cur.fetchone()[0]
    if count == 0:
        print('  ℹ Nenhum administrador encontrado. Execute scripts/criar_admin.py após o deploy.')
    else:
        print(f'  ✅ {count} administrador(es) encontrado(s)')
    cur.close()
    db.close()
except Exception as e:
    print(f'  ⚠ Aviso: {e}')
"

echo "✅ Build concluído!"
