import sys
sys.path.insert(0, ".")

# Check ChromaDB collections
from app.core.chroma import ChromaManager

chroma = ChromaManager()

# Get all collections
try:
    # Try different methods
    collections = chroma.client.list_collections()
    print("ChromaDB Collections:")
    for coll in collections:
        print(f"  - {coll.name}: {coll.count()} documents")
except Exception as e:
    print(f"Error: {e}")

# Check a specific collection
try:
    # Get by workspace name
    import chromadb
    client = chromadb.PersistentClient(path="data/chroma")
    collections = client.list_collections()
    print("\nCollections in ChromaDB:")
    for coll in collections:
        print(f"  - {coll.name}: {coll.count()} documents")
except Exception as e:
    print(f"Error: {e}")
