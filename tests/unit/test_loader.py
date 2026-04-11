"""Tests for core loader module."""

import io
import unittest
from unittest.mock import Mock, patch

from app.core.loader import DocumentLoader


class TestDocumentLoader(unittest.TestCase):
    """Test cases for DocumentLoader class."""

    def test_calculate_hash(self):
        """Test calculating SHA-256 hash."""
        content = b"test content"
        expected = "6ae8a75555209fd6c44157c0aed8016e763ff435a19cf186f76863140143ff72"
        self.assertEqual(DocumentLoader.calculate_hash(content), expected)

    @patch("app.core.loader.asyncio.get_event_loop")
    @patch("kreuzberg.extract_bytes")
    def test_load_file_success(self, mock_extract, mock_get_loop):
        """Test successful file loading via kreuzberg."""
        mock_result = Mock()
        mock_result.content = "Sample text from file"

        mock_loop = Mock()
        mock_loop.run_until_complete.return_value = mock_result
        mock_get_loop.return_value = mock_loop

        file_io = io.BytesIO(b"mock content")
        file_io.name = "test.pdf"

        result = DocumentLoader.load_file(file_io)
        self.assertEqual(result, "Sample text from file")

    def test_validate_file_invalid_type(self):
        """Test validating an unsupported file type."""
        mock_file = Mock()
        mock_file.name = "document.xyz"
        mock_file.size = 1000

        is_valid, error = DocumentLoader.validate_file(mock_file)
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)
        self.assertIn("Desteklenmeyen dosya tipi", error)

    def test_validate_file_size_exceeded(self):
        """Test validating a file that is too large."""
        mock_file = Mock()
        mock_file.name = "document.pdf"
        mock_file.size = 60 * 1024 * 1024  # 60MB

        is_valid, error = DocumentLoader.validate_file(mock_file, max_size_mb=50)
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)
        self.assertIn("Dosya boyutu çok büyük", error)

    def test_validate_file_success(self):
        """Test successful file validation."""
        mock_file = Mock()
        mock_file.name = "document.pdf"
        mock_file.size = 10 * 1024 * 1024  # 10MB

        is_valid, error = DocumentLoader.validate_file(mock_file, max_size_mb=50)
        self.assertTrue(is_valid)
        self.assertIsNone(error)

    @patch("app.core.loader.DocumentLoader.load_file")
    def test_load_documents_multiple_files(self, mock_load_file):
        """Test loading multiple documents into Langchain format."""
        mock_load_file.side_effect = ["PDF text", "TXT text"]

        mock_pdf = Mock()
        mock_pdf.name = "test.pdf"
        mock_pdf.size = 1000

        mock_txt = Mock()
        mock_txt.name = "test.txt"
        mock_txt.size = 500

        documents = DocumentLoader.load_documents([mock_pdf, mock_txt])

        self.assertEqual(len(documents), 2)
        self.assertEqual(documents[0].metadata["source"], "test.pdf")
        self.assertEqual(documents[0].page_content, "PDF text")
        self.assertEqual(documents[1].metadata["source"], "test.txt")
        self.assertEqual(documents[1].page_content, "TXT text")

    @patch("app.core.loader.DocumentLoader.load_file")
    def test_load_documents_empty_text(self, mock_load_file):
        """Test loading documents with empty text content."""
        mock_load_file.return_value = ""

        mock_file = Mock()
        mock_file.name = "empty.pdf"
        mock_file.size = 0

        documents = DocumentLoader.load_documents([mock_file])
        self.assertEqual(len(documents), 0)


if __name__ == "__main__":
    unittest.main()
