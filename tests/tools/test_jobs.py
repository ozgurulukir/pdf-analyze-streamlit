import sys

sys.path.insert(0, ".")

try:
    print("create_embedding_job import: OK")
except Exception as e:
    print(f"create_embedding_job import: FAILED - {e}")
    import traceback

    traceback.print_exc()
