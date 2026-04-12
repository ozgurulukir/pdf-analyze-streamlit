import os

import chromadb

persist_dir = "data/chroma"
if not os.path.exists(persist_dir):
    print(f"Chroma dir not found at {persist_dir}")
    # try root chroma_db
    persist_dir = "chroma_db"
    print(f"Trying {persist_dir}...")

client = chromadb.PersistentClient(path=persist_dir)
collections = client.list_collections()

print(f"--- Collections in {persist_dir} ---")
for col in collections:
    print(f"Name: {col.name}, Count: {col.count()}")
