import sys

sys.path.insert(0, ".")

# Check job status directly in database
import sqlite3

from app.core.config import AppConfig

config = AppConfig()
db_path = config.DB_PATH

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

cursor = conn.cursor()
cursor.execute("SELECT * FROM jobs ORDER BY created_at DESC LIMIT 5")
rows = cursor.fetchall()

print("Jobs in database:")
for row in rows:
    print(f"  ID: {row['id']}")
    print(f"  Type: {row['job_type']}")
    print(f"  Status: '{row['status']}'")
    print(f"  Progress: {row['progress']}")
    print(f"  Error: {row['error_message']}")
    print()

conn.close()
