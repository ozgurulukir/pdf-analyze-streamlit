import sys

sys.path.insert(0, ".")

try:
    print("AppConfig: OK")
except Exception as e:
    print(f"AppConfig: FAILED - {e}")

try:
    print("Models: OK")
except Exception as e:
    print(f"Models: FAILED - {e}")

try:
    print("Constants: OK")
except Exception as e:
    print(f"Constants: FAILED - {e}")
