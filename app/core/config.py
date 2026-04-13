"""Application configuration and settings."""

from dataclasses import dataclass
from pathlib import Path

import requests
from dotenv import load_dotenv

# Load .env
load_dotenv()

from app.core.logger import get_logger

logger = get_logger(__name__)


from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


@dataclass
class OllamaModel:
    label: str
    value: str

def get_ollama_models(base_url: str = "http://localhost:11434") -> list[dict[str, str]]:
    """Fetch available models from Ollama API."""
    default_models = [
        {"label": "nomic-embed-text (varsayılan)", "value": "nomic-embed-text"},
        {"label": "mxbai-embed-large", "value": "mxbai-embed-large"},
        {"label": "all-minilm", "value": "all-minilm"},
        {"label": "bge-m3", "value": "bge-m3"},
    ]
    try:
        response = requests.get(f"{base_url}/api/tags", timeout=5)
        if response.status_code == 200:
            data = response.json()
            models = data.get("models", [])
            if models:
                model_options = []
                for m in models:
                    name = m.get("name", "")
                    model_options.append({"label": f"{name} (indirilmiş)", "value": name})
                return model_options
    except Exception as e:
        logger.warning(f"Ollama API hatası: {e}")
    return default_models

def get_ollama_llm_models(base_url: str = "http://localhost:11434") -> list[dict[str, str]]:
    """Fetch available LLM models from Ollama API."""
    default_models = [
        {"label": "DeepSeek V2 (varsayılan)", "value": "deepseek-v2:671b"},
        {"label": "Qwen 2.5", "value": "qwen2.5:7b"},
        {"label": "Llama 3.1", "value": "llama3.1:8b"},
        {"label": "Mistral", "value": "mistral:7b"},
    ]
    try:
        response = requests.get(f"{base_url}/api/tags", timeout=5)
        if response.status_code == 200:
            data = response.json()
            models = data.get("models", [])
            if models:
                embed_keywords = ["embed", "embedding", "nomic-embed"]
                llm_models = []
                for m in models:
                    name = m.get("name", "")
                    if any(kw in name.lower() for kw in embed_keywords):
                        continue
                    size_gb = m.get("size", 0) / (1024**3)
                    llm_models.append({"label": f"{name} ({size_gb:.1f} GB)", "value": name})
                if llm_models:
                    return llm_models
    except Exception as e:
        logger.warning(f"Ollama API hatası: {e}")
    return default_models


class AppConfig(BaseSettings):
    """Application configuration with Pydantic v2 and environment variable support."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # --- App Settings ---
    APP_TITLE: str = Field(default="Doc Analyzer Pro", alias="APP_NAME")
    APP_ICON: str = "📄"
    APP_DESCRIPTION: str = "AI-Powered Document Analysis"
    APP_ENV: str = Field(default="development", alias="APP_ENV")
    DEBUG: bool = Field(default=True, alias="DEBUG")

    # --- LLM Settings ---
    LLM_BASE_URL: str = Field(default="https://ollama.com/v1")
    OLLAMA_API_KEY: str = Field(default="ollama")
    LLM_MODEL: str = Field(default="deepseek-v3.1:671b-cloud")
    LLM_TEMPERATURE: float = Field(default=0.3)
    DEFAULT_LLM_PROVIDER: str = Field(default="ollama")
    CHAT_CACHE_TTL: int = Field(default=1800, description="Chat response cache TTL in seconds")

    # --- Embedding Settings ---
    OLLAMA_BASE_URL: str = Field(default="http://localhost:11434")
    EMBED_MODEL: str = Field(default="nomic-embed-text")
    USE_HUGGINGFACE: bool = Field(default=False)
    HF_EMBED_MODEL: str = Field(default="sentence-transformers/all-MiniLM-L6-v2")

    # --- RAG & Chunking Settings ---
    CHUNK_SIZE: int = Field(default=1000)
    CHUNK_OVERLAP: int = Field(default=200)
    DEFAULT_RETRIEVER_K: int = Field(default=4)
    SIMILARITY_THRESHOLD: float = Field(default=0.5)

    # --- File settings ---
    ALLOWED_FILE_TYPES: list[str] = ["pdf", "txt", "docx", "html", "md", "pptx", "xlsx"]
    MAX_FILE_SIZE_MB: int = Field(default=50)
    MAX_FILE_NAME_LENGTH: int = Field(default=255)

    # --- Chat & History Settings ---
    MAX_MESSAGES_IN_MEMORY: int = Field(default=100)
    MESSAGE_SUMMARY_THRESHOLD: int = Field(default=50)
    DEFAULT_CHAT_LIMIT: int = Field(default=50)
    MAX_HISTORY_LIMIT: int = Field(default=1000)
    MAX_MESSAGE_LENGTH: int = Field(default=10000)

    # --- Database Settings ---
    DATA_DIR: str = Field(default="data")
    DB_PATH: str = Field(default="data/app.db")
    CHROMA_PERSIST_DIR: str = Field(default="data/chroma")
    JOB_RETENTION_DAYS: int = Field(default=7)

    # --- UI & UX Settings ---
    SIDEBAR_DEFAULT_OPEN: bool = Field(default=True)
    DEFAULT_PAGE: str = Field(default="💬 Chat")
    THEME: str = Field(default="dark")
    POLLING_INTERVAL_MS: int = Field(default=3000)

    # --- Security Settings ---
    RATE_LIMIT_ENABLED: bool = Field(default=False)
    RATE_LIMIT_RPM: int = Field(default=60)
    RATE_LIMIT_RPH: int = Field(default=1000)
    BURST_LIMIT: int = Field(default=10)

    # Preference weights
    DEFAULT_PREFERENCE_WEIGHTS: dict[str, float] = {
        "concise": 0.5,
        "detailed": 0.5,
        "examples": 0.5,
        "step_by_step": 0.5,
    }

    # --- UI & UX Constants (Moved from constants.py) ---
    DEFAULT_PAGINATION_LIMIT: int = Field(default=20)
    UI_COLORS: dict[str, str] = Field(default={
        "PRIMARY": "#FF4B4B",
        "SECONDARY": "#FF8C00",
        "SUCCESS": "#28A745",
        "WARNING": "#FFC107",
        "ERROR": "#DC3545",
        "INFO": "#17A2B8",
    })
    UI_PLACEHOLDERS: dict[str, str] = Field(default={
        "CHAT": "Mesajınızı yazın...",
        "SEARCH": "Dosya ara...",
        "UPLOAD": "Dosya yüklemek için sürükleyin veya tıklayın",
    })

    # --- Provider & RAG Constants (Moved from constants.py) ---
    OLLAMA_CLOUD_URL: str = Field(default="https://ollama.com/v1")
    OPENAI_COMPATIBLE_DEFAULT: str = Field(default="https://api.openai.com/v1")
    MAX_CONTEXT_LENGTH: int = Field(default=4096)
    
    # --- File Types & Mime (Moved from constants.py) ---
    ALLOWED_FILE_TYPES: list[str] = ["pdf", "txt", "docx", "html", "md", "pptx", "xlsx"]
    FILE_MIME_TYPES: dict[str, str] = Field(default={
        "pdf": "application/pdf",
        "txt": "text/plain",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "html": "text/html",
        "md": "text/markdown",
    })

    # --- L10n Messages (Moved from constants.py) ---
    ERROR_MESSAGES: dict[str, str] = Field(default={
        "FILE_TOO_LARGE": "Dosya boyutu çok büyük. Maksimum {} MB.",
        "INVALID_FILE_TYPE": "Geçersiz dosya tipi. İzin verilen tipler: {}",
        "DATABASE_ERROR": "Veritabanı hatası: {}",
        "LLM_ERROR": "LLM hatası: {}",
        "CHROMA_ERROR": "ChromaDB hatası: {}",
        "FILE_NOT_FOUND": "Dosya bulunamadı: {}",
        "WORKSPACE_NOT_FOUND": "Çalışma alanı bulunamadı: {}",
        "INVALID_INPUT": "Geçersiz giriş: {}",
    })
    SUCCESS_MESSAGES: dict[str, str] = Field(default={
        "FILE_UPLOADED": "Dosya başarıyla yüklendi: {}",
        "WORKSPACE_CREATED": "Çalışma alanı oluşturuldu: {}",
        "FILE_PROCESSED": "Dosya işlendi: {}",
        "MESSAGE_SENT": "Mesaj gönderildi",
    })

    @model_validator(mode="after")
    def _validate_model(self) -> "AppConfig":
        """Pydantic validator wrapper."""
        return self._perform_validation()

    def _perform_validation(self) -> "AppConfig":
        """Initialize paths and validate configuration. Can be called manually."""
        # Force absolute paths relative to project root (parent of app/ folder)
        project_root = Path(__file__).parent.parent.parent.absolute()

        # Ensure DATA_DIR is absolute
        if not Path(self.DATA_DIR).is_absolute():
            data_path = project_root / self.DATA_DIR
            self.DATA_DIR = str(data_path)
        else:
            data_path = Path(self.DATA_DIR)

        data_path.mkdir(parents=True, exist_ok=True)

        # Resolve DB_PATH if relative
        if not Path(self.DB_PATH).is_absolute():
            self.DB_PATH = str(data_path / Path(self.DB_PATH).name)

        # Resolve CHROMA_PERSIST_DIR if relative
        if not Path(self.CHROMA_PERSIST_DIR).is_absolute():
            self.CHROMA_PERSIST_DIR = str(data_path / "chroma")

        # Create directories
        Path(self.DB_PATH).parent.mkdir(parents=True, exist_ok=True)
        Path(self.CHROMA_PERSIST_DIR).mkdir(parents=True, exist_ok=True)

        # Validations
        if self.CHUNK_SIZE <= 0:
            raise ValueError("CHUNK_SIZE must be positive")
        if self.CHUNK_OVERLAP >= self.CHUNK_SIZE:
            raise ValueError("CHUNK_OVERLAP must be less than CHUNK_SIZE")
        if self.RATE_LIMIT_RPM <= 0:
            raise ValueError("RATE_LIMIT_RPM must be positive")
        return self

    def sync_with_db(self, config_dict: dict) -> None:
        """
        Merge configuration from database preferences.

        Args:
            config_dict: Key-value pairs from UserPreferences.config
        """
        from app.core.constants import SessionKeys

        key_map = {
            SessionKeys.LLM_MODEL.value: "LLM_MODEL",
            SessionKeys.LLM_BASE_URL.value: "LLM_BASE_URL",
            SessionKeys.OLLAMA_API_KEY.value: "OLLAMA_API_KEY",
            SessionKeys.LLM_TEMPERATURE.value: "LLM_TEMPERATURE",
            SessionKeys.USE_HUGGINGFACE.value: "USE_HUGGINGFACE",
            SessionKeys.EMBED_MODEL.value: "EMBED_MODEL",
            SessionKeys.OLLAMA_URL.value: "OLLAMA_BASE_URL",
            SessionKeys.HF_EMBED_MODEL.value: "HF_EMBED_MODEL",
            SessionKeys.DATA_DIR.value: "DATA_DIR",
            SessionKeys.CHROMA_PATH.value: "CHROMA_PERSIST_DIR",
            SessionKeys.CHUNK_SIZE.value: "CHUNK_SIZE",
            SessionKeys.CHUNK_OVERLAP.value: "CHUNK_OVERLAP",
        }

        # Update attributes directly
        for session_key, attr_name in key_map.items():
            if session_key in config_dict and config_dict[session_key] is not None:
                val = config_dict[session_key]
                # Type conversion for numeric fields
                if attr_name in ["LLM_TEMPERATURE", "CHUNK_SIZE", "CHUNK_OVERLAP"]:
                    try:
                        val = float(val) if "TEMPERATURE" in attr_name else int(val)
                    except (ValueError, TypeError):
                        continue
                setattr(self, attr_name, val)

        # Re-resolve paths
        self._perform_validation()

    def is_production(self) -> bool:
        return self.APP_ENV.lower() == "production"

    def is_development(self) -> bool:
        return self.APP_ENV.lower() == "development"

    def is_allowed_file_type(self, extension: str) -> bool:
        """Check if file extension is allowed."""
        return extension.lower().strip(".") in [ext.lower().strip(".") for ext in self.ALLOWED_FILE_TYPES]

    @property
    def MAX_FILE_SIZE_BYTES(self) -> int:
        return self.MAX_FILE_SIZE_MB * 1024 * 1024



# LLM Model seçenekleri
LLM_MODEL_OPTIONS = [
    {"label": "DeepSeek V2", "value": "deepseek-v2:671b"},
    {"label": "Qwen 2.5", "value": "qwen2.5:7b"},
    {"label": "Llama 3.1", "value": "llama3.1:8b"},
    {"label": "Mistral", "value": "mistral:7b"},
    {"label": "Gemma 2", "value": "gemma2:9b"},
    {"label": "Phi 3", "value": "phi3:14b"},
    {"label": "Aya", "value": "aya:8b"},
    {"label": "Command R", "value": "command-r7b-enterprise"},
]

# Embedding Model seçenekleri
EMBED_MODEL_OPTIONS = [
    {"label": "nomic-embed-text", "value": "nomic-embed-text", "desc": "Önerilen"},
    {
        "label": "mxbai-embed-large",
        "value": "mxbai-embed-large",
        "desc": "Yüksek kalite",
    },
    {"label": "all-minilm", "value": "all-minilm", "desc": "Hızlı"},
    {"label": "bge-m3", "value": "bge-m3", "desc": "Çok dilli"},
]

# HuggingFace Embedding seçenekleri
HF_EMBED_OPTIONS = [
    {"label": "all-MiniLM-L6-v2", "value": "sentence-transformers/all-MiniLM-L6-v2"},
    {
        "label": "multi-qa-mpnet-base",
        "value": "sentence-transformers/multi-qa-mpnet-base-cos-v1",
    },
    {"label": "bge-small-en-v1.5", "value": "BAAI/bge-small-en-v1.5"},
]

# Quick prompt suggestions
QUICK_PROMPTS = [
    "Bu belgede ne hakkında bilgi var?",
    "Özet çıkarır mısın?",
    "Ana noktaları listeler misin?",
    "Detaylı açıklama yapabilir misin?",
]

# CSS for tilted-T layout
TILTED_T_CSS = """
<style>
    .stApp { background: linear-gradient(to bottom right, #f8f9fa, #e9ecef); }
    .stButton > button { border-radius: 0.5rem; font-weight: 600; transition: all 0.3s ease; }
    .stButton > button:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
    .stChatMessage { border-radius: 16px; }
    div[data-testid="stMetricValue"] { font-size: 1.5rem; }
    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-track { background: #f1f1f1; }
    ::-webkit-scrollbar-thumb { background: #888; border-radius: 4px; }
</style>
"""
