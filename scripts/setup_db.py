import os
from dotenv import load_dotenv
load_dotenv()
import psycopg2
from flask_bcrypt import generate_password_hash

db = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = db.cursor()

# Executar schema
with open('db/schema_postgresql.sql', 'r', encoding='utf-8') as f:
    sql = f.read()
for statement in sql.split(';'):
    statement = statement.strip()
    if statement:
        try:
            cur.execute(statement)
        except Exception as e:
            if 'already exists' not in str(e).lower():
                print(f'Aviso: {e}')
db.commit()
print('Schema executado!')

# Verificar tabelas
cur.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename")
tabelas = [r[0] for r in cur.fetchall()]
print(f'Tabelas: {len(tabelas)}')
for t in tabelas:
    print(f'  - {t}')

# Criar administrador
cur.execute("SELECT COUNT(*) FROM utilizadores WHERE papel = 'administrador'")
count = cur.fetchone()[0]
if count == 0:
    pw = generate_password_hash('Develop/28').decode('utf-8')
    cur.execute(
        "INSERT INTO utilizadores (nome, email, password_hash, papel) VALUES (%s, %s, %s, %s)",
        ('Administrador', 'jorgedange@gmail.com', pw, 'administrador')
    )
    db.commit()
    print('Admin criado: jorgedange@gmail.com')
else:
    print(f'Admin ja existe: {count}')

cur.close()
db.close()
print('Tudo pronto!')
