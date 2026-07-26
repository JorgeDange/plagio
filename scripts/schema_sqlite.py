import sqlite3
conn = sqlite3.connect('instance/plagio.db')
cur = conn.cursor()
cur.execute("SELECT sql FROM sqlite_master WHERE type='table' AND sql IS NOT NULL")
for row in cur.fetchall():
    print(row[0])
    print()
conn.close()
