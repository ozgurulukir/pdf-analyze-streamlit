import time
try:
    from langchain.embeddings import HuggingFaceEmbeddings
except ImportError:
    from langchain_huggingface import HuggingFaceEmbeddings

print("Starting benchmark...", flush=True)
start_time = time.time()
embeddings = HuggingFaceEmbeddings()
end_time = time.time()

print(f"HuggingFaceEmbeddings init time without cache: {end_time - start_time:.4f} seconds", flush=True)
