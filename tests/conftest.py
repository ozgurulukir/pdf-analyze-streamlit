"""Pytest configuration and fixtures."""

import os
from unittest.mock import Mock

import pytest

# Set environment variables for testing
os.environ["OPENAI_API_KEY"] = "sk-test-key"


@pytest.fixture
def mock_openai_api_key(monkeypatch):
    """Mock OpenAI API key."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")


@pytest.fixture
def sample_pdf_bytes():
    """Sample PDF file bytes."""
    return b"%PDF-1.4\n1 0 obj\n<<\n>>\nendobj\nxref\n0 1\ntrailer\n<<\n/Root 1 0 R\n>>\n%%EOF"


@pytest.fixture
def sample_text_content():
    """Sample text content."""
    return """This is a sample document for testing purposes.

It contains multiple paragraphs of text that can be used to test
the document processing functionality.

The document includes various topics that can be queried."""


@pytest.fixture
def mock_document():
    """Create a mock document."""
    from langchain.schema import Document

    return Document(
        page_content="Sample document content for testing",
        metadata={"source": "test.pdf", "type": "pdf", "size": 1024},
    )


@pytest.fixture
def mock_documents(mock_document):
    """Create a list of mock documents."""
    from langchain.schema import Document

    return [
        Document(
            page_content="First document content",
            metadata={"source": "doc1.pdf", "type": "pdf", "size": 1024},
        ),
        Document(
            page_content="Second document content",
            metadata={"source": "doc2.pdf", "type": "pdf", "size": 2048},
        ),
        Document(
            page_content="Third document content",
            metadata={"source": "doc3.txt", "type": "txt", "size": 512},
        ),
    ]


@pytest.fixture
def mock_vectorstore():
    """Create a mock vectorstore."""
    mock_vs = Mock()
    mock_vs.as_retriever.return_value = Mock()
    return mock_vs


@pytest.fixture
def app_config():
    """Create app config for testing."""
    from app.core.config import AppConfig

    return AppConfig(
        CHUNK_SIZE=500, CHUNK_OVERLAP=100, EMBEDDING_MODEL="text-embedding-3-small"
    )
