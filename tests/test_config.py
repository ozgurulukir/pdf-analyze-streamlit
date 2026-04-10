import os
import unittest
from app.core.config import AppConfig

class TestConfig(unittest.TestCase):
    def test_ollama_api_key_default(self):
        # Temporarily remove OLLAMA_API_KEY from environment if it exists
        original_val = os.environ.get("OLLAMA_API_KEY")
        if "OLLAMA_API_KEY" in os.environ:
            del os.environ["OLLAMA_API_KEY"]

        config = AppConfig()
        self.assertEqual(config.OLLAMA_API_KEY, "")

        # Restore environment variable
        if original_val is not None:
            os.environ["OLLAMA_API_KEY"] = original_val

if __name__ == "__main__":
    unittest.main()
