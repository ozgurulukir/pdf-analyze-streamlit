import os
import unittest

from app.core.config import AppConfig


class TestConfig(unittest.TestCase):
    def test_ollama_api_key_default(self):
        from unittest.mock import patch
        with patch.dict(os.environ, clear=False):
            os.environ.pop("OLLAMA_API_KEY", None)
            config = AppConfig()
            self.assertEqual(config.OLLAMA_API_KEY, "")


if __name__ == "__main__":
    unittest.main()
