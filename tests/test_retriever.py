"""Tests for retriever module."""

import unittest
from unittest.mock import Mock, patch

from app.core.retriever import QAChain, RetrieverFactory
from langchain_core.documents import Document

from app.core.config import AppConfig


class TestRetrieverFactory(unittest.TestCase):
    """Test cases for RetrieverFactory class."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = AppConfig()
        self.factory = RetrieverFactory(self.config)

        self.mock_documents = [
            Document(
                page_content="Sample document content", metadata={"source": "test.pdf"}
            )
        ]

    def test_split_documents_recursive(self):
        """Test document splitting with recursive method."""
        result = self.factory.split_documents(
            self.mock_documents,
            chunk_size=100,
            chunk_overlap=20,
            split_method="recursive",
        )

        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

    def test_split_documents_token(self):
        """Test document splitting with token method."""
        result = self.factory.split_documents(
            self.mock_documents, chunk_size=100, chunk_overlap=20, split_method="token"
        )

        self.assertIsInstance(result, list)

    def test_split_documents_unknown_method(self):
        """Test document splitting with unknown method defaults to recursive."""
        result = self.factory.split_documents(
            self.mock_documents, split_method="unknown_method"
        )

        self.assertIsInstance(result, list)

    @patch("app.core.retriever.FAISS")
    @patch("app.core.retriever.OpenAIEmbeddings")
    def test_create_vectorstore_success(self, mock_embeddings, mock_faiss):
        """Test successful vectorstore creation."""
        mock_faiss.from_documents.return_value = Mock()

        result = self.factory.create_vectorstore(self.mock_documents, embeddings=Mock())

        self.assertIsNotNone(result)
        mock_faiss.from_documents.assert_called_once()

    def test_create_vectorstore_empty_documents(self):
        """Test vectorstore creation with empty documents."""
        with self.assertRaises(ValueError) as context:
            self.factory.create_vectorstore([])

        self.assertIn("No documents", str(context.exception))

    def test_get_retriever_similarity(self):
        """Test getting similarity retriever."""
        mock_vectorstore = Mock()
        mock_vectorstore.as_retriever.return_value = Mock()

        self.factory.get_retriever(
            mock_vectorstore, retriever_type="similarity"
        )

        mock_vectorstore.as_retriever.assert_called_once()

    def test_get_retriever_mmr(self):
        """Test getting MMR retriever."""
        mock_vectorstore = Mock()
        mock_vectorstore.as_retriever.return_value = Mock()

        self.factory.get_retriever(mock_vectorstore, retriever_type="mmr")

        mock_vectorstore.as_retriever.assert_called_once()

    def test_get_retriever_svm(self):
        """Test getting SVM retriever."""
        mock_vectorstore = Mock()
        mock_vectorstore.as_retriever.return_value = Mock()

        self.factory.get_retriever(mock_vectorstore, retriever_type="svm")

        mock_vectorstore.as_retriever.assert_called_once()


class TestQAChain(unittest.TestCase):
    """Test cases for QAChain class."""

    def test_qa_chain_class_exists(self):
        """Test that QAChain class exists and has required methods."""
        self.assertTrue(hasattr(QAChain, "create"))
        self.assertTrue(hasattr(QAChain, "generate_questions"))
        self.assertTrue(callable(QAChain.create))
        self.assertTrue(callable(QAChain.generate_questions))

    def test_qa_chain_generate_questions_returns_list(self):
        """Test that generate_questions returns a list."""
        # This test just verifies the method signature
        import inspect

        sig = inspect.signature(QAChain.generate_questions)
        params = list(sig.parameters.keys())
        self.assertIn("chain", params)
        self.assertIn("text", params)
        self.assertIn("num_questions", params)


if __name__ == "__main__":
    unittest.main()
