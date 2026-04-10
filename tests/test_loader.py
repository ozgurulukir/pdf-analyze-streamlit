"""Tests for core loader module."""
import unittest
from unittest.mock import Mock, patch, MagicMock
import io

from app.core.loader import DocumentLoader


class TestDocumentLoader(unittest.TestCase):
    """Test cases for DocumentLoader class."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_pdf_content = b"%PDF-1.4 mock content"

    @patch('asyncio.get_event_loop')
    def test_load_file_success(self, mock_get_event_loop):
        """Test successful file loading via Kreuzberg (BytesIO)."""
        mock_loop = Mock()
        mock_result = Mock()
        mock_result.content = "Sample text content"
        mock_loop.run_until_complete.return_value = mock_result
        mock_get_event_loop.return_value = mock_loop

        import sys
        mock_kreuzberg = MagicMock()
        with patch.dict('sys.modules', {'kreuzberg': mock_kreuzberg}):
            file_io = io.BytesIO(b"mock content")
            file_io.name = "test.pdf"
            result = DocumentLoader.load_file(file_io)
            self.assertEqual(result, "Sample text content")

    @patch('asyncio.get_event_loop')
    def test_load_file_error(self, mock_get_event_loop):
        """Test file loading error handling."""
        mock_loop = Mock()
        mock_loop.run_until_complete.side_effect = Exception("Load Error")
        mock_get_event_loop.return_value = mock_loop

        import sys
        mock_kreuzberg = MagicMock()
        with patch.dict('sys.modules', {'kreuzberg': mock_kreuzberg}):
            file_io = io.BytesIO(b"mock content")
            file_io.name = "test.pdf"

            # Should not raise, should return empty string
            result = DocumentLoader.load_file(file_io)
            self.assertEqual(result, "")

    @patch('asyncio.get_event_loop')
    def test_load_file_path_success(self, mock_get_event_loop):
        """Test successful file loading via Kreuzberg (File Path)."""
        mock_loop = Mock()
        mock_result = Mock()
        mock_result.content = "File path content"
        mock_loop.run_until_complete.return_value = mock_result
        mock_get_event_loop.return_value = mock_loop

        import sys
        mock_kreuzberg = MagicMock()
        with patch.dict('sys.modules', {'kreuzberg': mock_kreuzberg}):
            result = DocumentLoader.load_file("dummy/path.pdf")
            self.assertEqual(result, "File path content")

    def test_load_documents_multiple_files(self):
        """Test loading multiple documents."""
        mock_pdf = Mock()
        mock_pdf.name = "test.pdf"
        mock_pdf.getvalue.return_value = b"pdf content"
        mock_pdf.size = 1000

        mock_txt = Mock()
        mock_txt.name = "test.txt"
        mock_txt.getvalue.return_value = b"text content"
        mock_txt.size = 500

        with patch('app.core.loader.DocumentLoader.load_file') as mock_load_file:
            mock_load_file.side_effect = ["PDF text", "TXT text"]
            documents = DocumentLoader.load_documents([mock_pdf, mock_txt])

            self.assertEqual(len(documents), 2)
            self.assertEqual(documents[0].metadata["source"], "test.pdf")
            self.assertEqual(documents[1].metadata["source"], "test.txt")

    def test_load_documents_empty_text(self):
        """Test loading documents with empty text content."""
        mock_file = Mock()
        mock_file.name = "empty.pdf"
        mock_file.getvalue.return_value = b""
        mock_file.size = 0

        with patch('app.core.loader.DocumentLoader.load_file', return_value=""):
            documents = DocumentLoader.load_documents([mock_file])
            self.assertEqual(len(documents), 0)

    def test_validate_file_success(self):
        """Test file validation with supported type and valid size."""
        mock_file = Mock()
        mock_file.name = "document.pdf"
        mock_file.size = 10 * 1024 * 1024  # 10 MB

        is_valid, error_msg = DocumentLoader.validate_file(mock_file)
        self.assertTrue(is_valid)
        self.assertIsNone(error_msg)

    def test_validate_file_unsupported_type(self):
        """Test file validation with unsupported type."""
        mock_file = Mock()
        mock_file.name = "program.exe"
        mock_file.size = 1 * 1024 * 1024

        is_valid, error_msg = DocumentLoader.validate_file(mock_file)
        self.assertFalse(is_valid)
        self.assertEqual(error_msg, "Desteklenmeyen dosya tipi: exe")

    def test_validate_file_too_large(self):
        """Test file validation when file exceeds default size limit."""
        mock_file = Mock()
        mock_file.name = "large_doc.pdf"
        mock_file.size = 51 * 1024 * 1024  # 51 MB (default max is 50MB)

        is_valid, error_msg = DocumentLoader.validate_file(mock_file)
        self.assertFalse(is_valid)
        self.assertEqual(error_msg, "Dosya boyutu çok büyük (max 50MB)")

    def test_validate_file_custom_size_too_large(self):
        """Test file validation when file exceeds custom size limit."""
        mock_file = Mock()
        mock_file.name = "custom_doc.pdf"
        mock_file.size = 15 * 1024 * 1024  # 15 MB

        is_valid, error_msg = DocumentLoader.validate_file(mock_file, max_size_mb=10)
        self.assertFalse(is_valid)
        self.assertEqual(error_msg, "Dosya boyutu çok büyük (max 10MB)")


if __name__ == '__main__':
    unittest.main()
