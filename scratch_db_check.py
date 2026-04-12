import os
import sqlite3

db_path = "data/app.db"
if not os.path.exists(db_path):
    print(f"DB not found at {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("--- Workspaces ---")
cursor.execute("SELECT id, name FROM workspaces")
for row in cursor.fetchall():
    print(row)

print("\n--- Files ---")
cursor.execute("SELECT id, filename, workspace_id, status FROM files")
for row in cursor.fetchall():
    print(row)

conn.close()
