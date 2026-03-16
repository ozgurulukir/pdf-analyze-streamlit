import sqlite3
import datetime

db_path = "C:/Users/ozgur/Github/pdf-analyze-streamlit/data/sqlite/pdf_analyzer.db"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()
cur.execute("SELECT id, status, started_at, completed_at, error_message FROM jobs ORDER BY started_at DESC, created_at DESC LIMIT 5")
rows = cur.fetchall()
for r in rows:
    print(dict(r))
