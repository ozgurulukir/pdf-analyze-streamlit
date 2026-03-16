"""Centralized constants and enums for the application."""
from enum import Enum
from typing import Dict, List


class SessionKeys(str, Enum):
    """Enumeration of all streamlit session state keys to avoid magic strings."""
    # Active state
    ACTIVE_WORKSPACE_ID = "active_workspace_id"
    WORKSPACES = "workspaces"
    CHAT_HISTORY = "chat_history"
    SIDEBAR_OPEN = "sidebar_open"
    CURRENT_PAGE = "current_page"
    PREFERENCES = "preferences"
    
    # LLM Settings
    LLM_MODEL = "llm_model"
    LLM_BASE_URL = "llm_base_url"
    LLM_BASE_URL_INPUT = "llm_base_url_input"
    OLLAMA_API_KEY = "ollama_api_key"
    LLM_TEMPERATURE = "llm_temperature"
    LAST_ENDPOINT_TYPE = "last_endpoint_type"
    
    # Embedding Settings
    USE_HUGGINGFACE = "use_huggingface"
    EMBED_MODEL = "embed_model"
    OLLAMA_URL = "ollama_url"
    HF_EMBED_MODEL = "hf_embed_model"
    OLLAMA_EMBED_MODELS = "ollama_embed_models"
    OLLAMA_LLM_MODELS = "ollama_llm_models"
    
    # Data Settings
    DATA_DIR = "data_dir"
    CHROMA_PATH = "chroma_path"
    CHUNK_SIZE = "chunk_size"
    CHUNK_OVERLAP = "chunk_overlap"
    
    # App State
    THEME = "theme"
    TRIGGER_RESET = "_trigger_reset"
    LAST_PROMPT = "_last_prompt"
    STREAMING_PROMPT = "streaming_prompt"


class ProcessingStatus(str, Enum):
    """Standardized status for files and background jobs."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ERROR = "error"
    PROCESSING = "processing"
    PROCESSED = "processed"


# ===================
# Database Constants
# ===================

class DBTables:
    """Database table names."""
    WORKSPACES = "workspaces"
    FILES = "files"
    CHUNKS = "chunks"
    MESSAGES = "messages"
    QA_PAIRS = "qa_pairs"
    PREFERENCES = "preferences"
    JOBS = "jobs"


class DBColumns:
    """Database column names."""
    # Common
    ID = "id"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    STATUS = "status"
    
    # Workspaces
    WORKSPACE_NAME = "name"
    WORKSPACE_DESCRIPTION = "description"
    WORKSPACE_LAST_MODIFIED = "last_modified"
    WORKSPACE_FILE_COUNT = "file_count"
    WORKSPACE_IS_ACTIVE = "is_active"
    
    # Files
    FILE_WORKSPACE_ID = "workspace_id"
    FILE_FILENAME = "filename"
    FILE_ORIGINAL_NAME = "original_name"
    FILE_TYPE = "file_type"
    FILE_SIZE = "size"
    FILE_CHUNK_COUNT = "chunk_count"
    FILE_CONTENT_HASH = "content_hash"
    FILE_UPLOADED_AT = "uploaded_at"
    FILE_PROCESSED_AT = "processed_at"
    FILE_ERROR_MESSAGE = "error_message"
    FILE_TAGS = "tags"


# ===================
# UI Constants
# ===================

class UIConstants:
    """UI related constants."""
    DEFAULT_CHUNK_SIZE = 1000
    DEFAULT_CHUNK_OVERLAP = 200
    MAX_FILE_SIZE_MB = 50
    POLLING_INTERVAL_MS = 3000
    MAX_MESSAGE_LENGTH = 10000
    MAX_FILE_NAME_LENGTH = 255
    DEFAULT_PAGINATION_LIMIT = 20


class UIPages:
    """Page identifiers."""
    CHAT = "Chat"
    DOCUMENTS = "Belgeler"
    ANALYSIS = "Analiz"
    SETTINGS = "Ayarlar"


class UIPlaceholders:
    """UI placeholder text."""
    CHAT_PLACEHOLDER = "Mesajınızı yazın..."
    SEARCH_PLACEHOLDER = "Dosya ara..."
    UPLOAD_PLACEHOLDER = "Dosya yüklemek için sürükleyin veya tıklayın"


class UIColors:
    """UI color constants."""
    PRIMARY = "#FF4B4B"
    SECONDARY = "#FF8C00"
    SUCCESS = "#28A745"
    WARNING = "#FFC107"
    ERROR = "#DC3545"
    INFO = "#17A2B8"


# ===================
# Provider Constants
# ===================

class ProviderConstants:
    """Provider specific constants."""
    OLLAMA_LOCAL_URL = "http://localhost:11434"
    OLLAMA_CLOUD_URL = "https://ollama.com/v1"
    OPENAI_COMPATIBLE_DEFAULT = "https://api.openai.com/v1"


# ===================
# API Constants
# ===================

class APIEndpoints:
    """API endpoint paths."""
    OLLAMA_TAGS = "/api/tags"
    OLLAMA_GENERATE = "/api/generate"
    OLLAMA_EMBED = "/api/embeddings"
    OPENAI_CHAT = "/chat/completions"
    OPENAI_EMBEDDINGS = "/embeddings"


# ===================
# RAG Constants
# ===================

class RAGDefaults:
    """RAG default settings."""
    DEFAULT_RETRIEVER_K = 4
    DEFAULT_TEMPERATURE = 0.3
    MAX_CONTEXT_LENGTH = 4096
    MAX_CHUNK_LENGTH = 2000
    SIMILARITY_THRESHOLD = 0.5


# ===================
# File Type Constants
# ===================

class FileTypes:
    """Supported file types."""
    ALLOWED_EXTENSIONS: List[str] = ["pdf", "txt", "docx", "html", "md", "pptx", "xlsx"]
    MIME_TYPES: Dict[str, str] = {
        "pdf": "application/pdf",
        "txt": "text/plain",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "html": "text/html",
        "md": "text/markdown",
    }
    
    @classmethod
    def is_allowed(cls, extension: str) -> bool:
        """Check if file extension is allowed."""
        return extension.lower() in cls.ALLOWED_EXTENSIONS


# ===================
# Error Messages
# ===================

class ErrorMessages:
    """Standardized error messages."""
    FILE_TOO_LARGE = "Dosya boyutu çok büyük. Maksimum {} MB."
    INVALID_FILE_TYPE = "Geçersiz dosya tipi. İzin verilen tipler: {}"
    DATABASE_ERROR = "Veritabanı hatası: {}"
    LLM_ERROR = "LLM hatası: {}"
    CHROMA_ERROR = "ChromaDB hatası: {}"
    FILE_NOT_FOUND = "Dosya bulunamadı: {}"
    WORKSPACE_NOT_FOUND = "Çalışma alanı bulunamadı: {}"
    INVALID_INPUT = "Geçersiz giriş: {}"


# ===================
# Success Messages
# ===================

class SuccessMessages:
    """Standardized success messages."""
    FILE_UPLOADED = "Dosya başarıyla yüklendi: {}"
    WORKSPACE_CREATED = "Çalışma alanı oluşturuldu: {}"
    FILE_PROCESSED = "Dosya işlendi: {}"
    MESSAGE_SENT = "Mesaj gönderildi"
