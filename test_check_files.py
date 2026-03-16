import sys
sys.path.insert(0, ".")

# Check file status and chunks
import sqlite3
from app.core.config import AppConfig

config = AppConfig()
db_path = config.DB_PATH

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

cursor = conn.cursor()

# Check recent files
print("Recent files:")
cursor.execute("SELECT * FROM files ORDER BY uploaded_at DESC LIMIT 5")
rows = cursor.fetchall()
for row in rows:
    print(f"  File: {row['filename']}")
    print(f"  Status: '{row['status']}'")
    print(f"  Chunk count: {row['chunk_count']}")
    print(f"  Error: {row['error_message']}")
    print()

# Check chunks
print("\nRecent chunks:")
cursor.execute("SELECT COUNT(*) as count FROM chunks")
total_chunks = cursor.fetchone()
print(f"  Total chunks: {total_chunks['count']}")

cursor.execute("SELECT * FROM chunks ORDER BY created_at DESC LIMIT 3")
rows = cursor.fetchall()
for row in rows:
    print(f"  File ID: {row['file_id']}")
    print(f"  Chroma ID: {row['chroma_id'][:30] if row['chroma_id'] else 'None'}...")
    print()

# Check ChromaDB
print("\nChromaDB collections:")
from app.core.chroma import ChromaManager
chroma = ChromaManager()
collections = chroma.get_collections()
for coll in collections:
    print(f"  - {coll.name}: {coll.count()} documents")

conn.close()
