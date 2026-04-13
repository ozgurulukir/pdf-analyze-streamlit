"""Centralized constants and enums for the application."""

from enum import StrEnum


class SessionKeys(StrEnum):
    """Enumeration of all streamlit session state keys to avoid magic strings."""

    # Active state
    ACTIVE_WORKSPACE_ID = "active_workspace_id"
    WORKSPACES = "workspaces"
    CHAT_HISTORY = "chat_history"
    ACTIVE_SESSION_ID = "active_session_id"
    SIDEBAR_OPEN = "sidebar_open"
    CURRENT_PAGE = "current_page"
    PREFERENCES = "preferences"
    PROMPT_TEXTS = "prompt_texts"

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


class ProcessingStatus(StrEnum):
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
    CHAT_SESSIONS = "chat_sessions"


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


class UIPages:
    """Page identifiers."""

    CHAT = "Chat"
    DOCUMENTS = "Belgeler"
    ANALYSIS = "Analiz"
    KNOWLEDGE = "Bilgi Bankası"
    SETTINGS = "Ayarlar"


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
# Default Prompts
# ===================


class DefaultPrompts:
    """Default prompt fragments for response styles."""

    CONCISE = "Lütfen cevabı mümkün olduğunca kısa ve öz tut. Gereksiz detaylardan kaçın."
    DETAILED = "Lütfen cevabı detaylı, kapsamlı ve açıklayıcı bir şekilde sun. Önemli tüm noktaları ele al."
    EXAMPLES = "Cevabı pekiştirmek için somut örnekler ver."
    STEP_BY_STEP = "İşlemi veya açıklamayı adım adım, sıralı bir şekilde açıkla."

    @classmethod
    def get_defaults(cls) -> dict[str, str]:
        return {
            "concise": cls.CONCISE,
            "detailed": cls.DETAILED,
            "examples": cls.EXAMPLES,
            "step_by_step": cls.STEP_BY_STEP,
        }
