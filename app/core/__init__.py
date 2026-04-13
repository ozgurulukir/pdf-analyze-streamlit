"""Core module initialization."""

from app.core.chroma import ChromaManager, ChunkManager, EmbeddingManager
from app.core.config import (
    EMBED_MODEL_OPTIONS,
    HF_EMBED_OPTIONS,
    LLM_MODEL_OPTIONS,
    QUICK_PROMPTS,
    TILTED_T_CSS,
    AppConfig,
)
from app.core.constants import (
    APIEndpoints,
    DBColumns,
    DBTables,
    ProcessingStatus,
    SessionKeys,
    UIPages,
)
from app.core.database import DatabaseManager
from app.core.exceptions import (
    # Base
    AppError,
    ChromaCollectionError,
    ChromaConnectionError,
    # Chroma
    ChromaError,
    # Config
    ConfigurationError,
    DatabaseConnectionError,
    # Database
    DatabaseError,
    DatabaseQueryError,
    EmbeddingError,
    EnvironmentVariableError,
    FileCorruptedError,
    FileNotFoundError,
    # File
    FileProcessingError,
    FileTooLargeError,
    InvalidFileTypeError,
    LLMConnectionError,
    # LLM
    LLMError,
    LLMResponseError,
    LLMTimeoutError,
    MigrationError,
    RateLimitError,
    ValidationError,
    # Workspace
    WorkspaceError,
    WorkspaceExistsError,
    WorkspaceNotFoundError,
    # Decorators
    retry,
    retry_llm_call,
)
from app.core.health import HealthChecker, HealthCheckResult, get_health_checker
from app.core.jobs import EmbeddingWorker, JobQueue, create_embedding_job, get_job_queue
from app.core.loader import DocumentLoader
from app.core.models import (
    ChatSession,
    ChunkMetadata,
    FileMetadata,
    Job,
    Message,
    QAPair,
    UserPreferences,
    Workspace,
)
from app.core.rag import MessageCache, PromptTemplates, QAManager, RAGChain, create_llm
from app.core.router import PageRouter, resolve_page

__all__ = [
    # Chroma
    "ChromaManager",
    "ChunkManager",
    "EmbeddingManager",
    # Config
    "AppConfig",
    "EMBED_MODEL_OPTIONS",
    "HF_EMBED_OPTIONS",
    "LLM_MODEL_OPTIONS",
    "QUICK_PROMPTS",
    "TILTED_T_CSS",
    # Constants
    "APIEndpoints",
    "DBColumns",
    "DBTables",
    "ProcessingStatus",
    "SessionKeys",
    "UIPages",
    # Database
    "DatabaseManager",
    # Exceptions
    "AppError",
    "ChromaError",
    "ChromaConnectionError",
    "ChromaCollectionError",
    "ConfigurationError",
    "DatabaseError",
    "DatabaseConnectionError",
    "DatabaseQueryError",
    "EmbeddingError",
    "EnvironmentVariableError",
    "FileProcessingError",
    "FileCorruptedError",
    "FileNotFoundError",
    "FileTooLargeError",
    "InvalidFileTypeError",
    "LLMError",
    "LLMConnectionError",
    "LLMResponseError",
    "LLMTimeoutError",
    "MigrationError",
    "RateLimitError",
    "ValidationError",
    "WorkspaceError",
    "WorkspaceExistsError",
    "WorkspaceNotFoundError",
    "retry",
    "retry_llm_call",
    # Health
    "HealthChecker",
    "HealthCheckResult",
    "get_health_checker",
    # Jobs
    "EmbeddingWorker",
    "JobQueue",
    "create_embedding_job",
    "get_job_queue",
    # Loader
    "DocumentLoader",
    # Models
    "ChunkMetadata",
    "FileMetadata",
    "Job",
    "Message",
    "QAPair",
    "UserPreferences",
    "Workspace",
    "ChatSession",
    # RAG
    "MessageCache",
    "PromptTemplates",
    "QAManager",
    "RAGChain",
    "create_llm",
    # Router
    "PageRouter",
    "resolve_page",
]
