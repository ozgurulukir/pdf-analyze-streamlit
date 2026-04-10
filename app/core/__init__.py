"""Core module initialization."""

from app.core.config import (
    AppConfig,
    LLM_MODEL_OPTIONS,
    EMBED_MODEL_OPTIONS,
    HF_EMBED_OPTIONS,
    QUICK_PROMPTS,
    TILTED_T_CSS,
)
from app.core.models import (
    Workspace,
    FileMetadata,
    ChunkMetadata,
    Message,
    QAPair,
    UserPreferences,
    Job,
)
from app.core.database import DatabaseManager
from app.core.chroma import ChromaManager, EmbeddingManager, ChunkManager
from app.core.loader import DocumentLoader
from app.core.jobs import JobQueue, get_job_queue, create_embedding_job, EmbeddingWorker
from app.core.rag import RAGChain, MessageCache, QAManager, PromptTemplates, create_llm
from app.core.health import HealthChecker, HealthCheckResult, get_health_checker
from app.core.router import PageRouter, resolve_page
from app.core.exceptions import (
    # Base
    AppError,
    # Database
    DatabaseError,
    DatabaseConnectionError,
    DatabaseQueryError,
    MigrationError,
    # Chroma
    ChromaError,
    ChromaConnectionError,
    ChromaCollectionError,
    EmbeddingError,
    # LLM
    LLMError,
    LLMConnectionError,
    LLMTimeoutError,
    LLMResponseError,
    RateLimitError,
    # File
    FileProcessingError,
    FileNotFoundError,
    InvalidFileTypeError,
    FileTooLargeError,
    FileCorruptedError,
    # Workspace
    WorkspaceError,
    WorkspaceNotFoundError,
    WorkspaceExistsError,
    # Config
    ConfigurationError,
    EnvironmentVariableError,
    ValidationError,
    # Decorators
    retry,
    retry_llm_call,
)
from app.core.constants import (
    SessionKeys,
    ProcessingStatus,
    DBTables,
    DBColumns,
    UIPages,
    UIConstants,
    UIPlaceholders,
    UIColors,
    ProviderConstants,
    APIEndpoints,
    RAGDefaults,
    FileTypes,
    ErrorMessages,
    SuccessMessages,
)
