"""Repository module initialization."""

from app.core.repositories.interfaces import (
    ChunkRepository,
    FileRepository,
    JobRepository,
    MessageRepository,
    PreferencesRepository,
    QARepository,
    WorkspaceRepository,
)
from app.core.repositories.sqlite_repositories import (
    SQLiteFileRepository,
    SQLiteMessageRepository,
    SQLiteWorkspaceRepository,
)

__all__ = [
    # Interfaces
    "WorkspaceRepository",
    "FileRepository",
    "ChunkRepository",
    "MessageRepository",
    "QARepository",
    "PreferencesRepository",
    "JobRepository",
    # Implementations
    "SQLiteWorkspaceRepository",
    "SQLiteFileRepository",
    "SQLiteMessageRepository",
]
