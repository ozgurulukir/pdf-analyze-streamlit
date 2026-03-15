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

    def test_load_pdf_success(self):
        """Test successful PDF loading."""
        # Create mock PDF reader
        mock_page = Mock()
        mock_page.extract_text.return_value = "Sample PDF text"

        mock_reader = Mock()
        mock_reader.pages = [mock_page]

        with patch('app.core.loader.PdfReader', return_value=mock_reader):
            file_io = io.BytesIO(b"mock pdf")
            result = DocumentLoader.load_pdf(file_io)

            self.assertEqual(result, "Sample PDF text\n")

    def test_load_pdf_error(self):
        """Test PDF loading error handling."""
        with patch('app.core.loader.PdfReader', side_effect=Exception("PDF Error")):
            file_io = io.BytesIO(b"mock pdf")

            # Should not raise, should return empty string
            result = DocumentLoader.load_pdf(file_io)
            self.assertEqual(result, "")

    def test_load_txt_success(self):
        """Test successful text file loading."""
        file_io = io.BytesIO(b"Hello, World!")
        file_io.seek(0)

        result = DocumentLoader.load_txt(file_io)
        self.assertEqual(result, "Hello, World!")

    def test_load_txt_multiple_encodings(self):
        """Test text file loading with different encodings."""
        # Test with latin-1 encoding
        file_io = io.BytesIO("Héllo".encode('latin-1'))

        result = DocumentLoader.load_txt(file_io)
        self.assertEqual(result, "Héllo")

    def test_load_file_unsupported_type(self):
        """Test loading unsupported file type."""
        mock_file = Mock()
        mock_file.name = "document.docx"

        with self.assertRaises(ValueError) as context:
            DocumentLoader.load_file(mock_file)

        self.assertIn("Desteklenmeyen dosya tipi", str(context.exception))

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

        with patch('app.core.loader.DocumentLoader.load_pdf', return_value="PDF text"):
            with patch('app.core.loader.DocumentLoader.load_txt', return_value="TXT text"):
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


if __name__ == '__main__':
    unittest.main()
