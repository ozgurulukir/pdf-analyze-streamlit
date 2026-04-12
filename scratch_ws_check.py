import sqlite3

db_path = "data/app.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT id, name, file_count FROM workspaces")
for row in cursor.fetchall():
    print(row)
conn.close()
