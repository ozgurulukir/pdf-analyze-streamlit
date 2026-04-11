"""Document loader using Kreuzberg for unified extraction."""

import asyncio
import os

import streamlit as st

try:
    from langchain_core.documents import Document
except ImportError:
    from langchain.schema import Document


class DocumentLoader:
    """Handles loading various document formats via Kreuzberg."""

    SUPPORTED_TYPES = {
        "pdf": "PDF Document",
        "txt": "Text File",
        "md": "Markdown File",
        "docx": "Word Document",
        "html": "HTML File",
        "pptx": "PowerPoint",
        "png": "Image (OCR)",
        "jpg": "Image (OCR)",
        "jpeg": "Image (OCR)",
    }

    @staticmethod
    def calculate_hash(content: bytes) -> str:
        """Calculate SHA-256 hash of content."""
        import hashlib

        return hashlib.sha256(content).hexdigest()

    @staticmethod
    def load_file(file) -> str:
        """Load and extract text from file using Kreuzberg."""
        import mimetypes

        from kreuzberg import extract_bytes, extract_file

        def get_or_create_event_loop():
            try:
                return asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                return loop

        try:
            loop = get_or_create_event_loop()

            # Handle both BytesIO (Streamlit UploadedFile) and file paths
            if hasattr(file, "read"):
                file.seek(0)
                content = file.read()
                file_name = getattr(file, "name", "file")

                # Kreuzberg requires mime_type for extract_bytes
                mime_type, _ = mimetypes.guess_type(file_name)
                if not mime_type:
                    # Fallback for common types if guess_type fails
                    ext = file_name.split(".")[-1].lower()
                    mime_map = {
                        "pdf": "application/pdf",
                        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        "txt": "text/plain",
                        "md": "text/markdown",
                        "html": "text/html",
                    }
                    mime_type = mime_map.get(ext, "application/octet-stream")

                # Use extract_bytes (async) and run in loop
                # Result is a ParseResult object with content attribute
                result = loop.run_until_complete(extract_bytes(content, mime_type))
                return result.content if hasattr(result, "content") else str(result)
            else:
                # Direct file path
                result = loop.run_until_complete(extract_file(file))
                return result.content if hasattr(result, "content") else str(result)

        except Exception as e:
            st.error(f"Kreuzberg okuma hatası: {str(e)}")
            return ""

    @classmethod
    def load_documents(cls, uploaded_files) -> list[Document]:
        """Load multiple documents and return as LangChain Documents."""
        documents = []

        for uploaded_file in uploaded_files:
            try:
                text = cls.load_file(uploaded_file)
                if text and text.strip():
                    doc = Document(
                        page_content=text,
                        metadata={
                            "source": uploaded_file.name,
                            "type": uploaded_file.name.split(".")[-1].lower(),
                            "size": uploaded_file.size,
                        },
                    )
                    documents.append(doc)
                else:
                    st.warning(
                        f"⚠️ {uploaded_file.name}: Metin çıkarılamadı veya dosya boş."
                    )
            except Exception as e:
                st.warning(f"⚠️ {uploaded_file.name} yüklenemedi: {str(e)}")

        return documents

    @classmethod
    def load_directory(
        cls, directory_path: str, glob_pattern: str = "**/*.*"
    ) -> list[Document]:
        """Load documents from a directory using Kreuzberg for each file."""
        import glob

        path = os.path.abspath(directory_path)
        if not os.path.exists(path):
            st.error(f"Dizin bulunamadı: {path}")
            return []

        search_pattern = os.path.join(path, glob_pattern)
        file_paths = glob.glob(search_pattern, recursive=True)

        documents = []
        for file_path in file_paths:
            if os.path.isdir(file_path):
                continue

            file_ext = file_path.split(".")[-1].lower()
            if file_ext in cls.SUPPORTED_TYPES:
                try:
                    text = cls.load_file(file_path)
                    if text and text.strip():
                        doc = Document(
                            page_content=text,
                            metadata={
                                "source": file_path,
                                "type": file_ext,
                                "size": os.path.getsize(file_path),
                            },
                        )
                        documents.append(doc)
                except Exception as e:
                    st.warning(f"⚠️ {os.path.basename(file_path)} okunamadı: {str(e)}")

        return documents

    @staticmethod
    def validate_file(uploaded_file, max_size_mb: int = 50) -> tuple[bool, str | None]:
        """Validate file before processing."""
        file_ext = uploaded_file.name.split(".")[-1].lower()

        if file_ext not in DocumentLoader.SUPPORTED_TYPES:
            return False, f"Desteklenmeyen dosya tipi: {file_ext}"

        if uploaded_file.size > max_size_mb * 1024 * 1024:
            return False, f"Dosya boyutu çok büyük (max {max_size_mb}MB)"

        return True, None
