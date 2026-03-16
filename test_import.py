import sys
sys.path.insert(0, ".")

try:
    from app.core.config import AppConfig
    print("AppConfig: OK")
except Exception as e:
    print(f"AppConfig: FAILED - {e}")

try:
    from app.core.models import Workspace
    print("Models: OK")
except Exception as e:
    print(f"Models: FAILED - {e}")

try:
    from app.core.constants import SessionKeys
    print("Constants: OK")
except Exception as e:
    print(f"Constants: FAILED - {e}")
