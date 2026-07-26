import sqlite3
conn = sqlite3.connect('instance/plagio.db')
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cur.fetchall()
for t in tables:
    count = conn.execute(f"SELECT COUNT(*) FROM [{t[0]}]").fetchone()[0]
    print(f'{t[0]:30s} {count:>6d} registos')
conn.close()
