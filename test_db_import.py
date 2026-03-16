import sys
sys.path.insert(0, ".")

try:
    from app.core import DatabaseManager
    print("DatabaseManager import: OK")
except Exception as e:
    print(f"DatabaseManager import: FAILED - {e}")
    import traceback
    traceback.print_exc()
