"""Repository interfaces for database operations."""

from abc import ABC, abstractmethod
from typing import Any

from app.core.models import (
    ChunkMetadata,
    FileMetadata,
    Job,
    Message,
    QAPair,
    UserPreferences,
    Workspace,
)


class WorkspaceRepository(ABC):
    """Abstract repository for workspace operations."""

    @abstractmethod
    def create(self, workspace: Workspace) -> Workspace:
        """Create a new workspace."""
        pass

    @abstractmethod
    def get_by_id(self, workspace_id: str) -> Workspace | None:
        """Get workspace by ID."""
        pass

    @abstractmethod
    def get_all(self) -> list[Workspace]:
        """Get all workspaces."""
        pass

    @abstractmethod
    def get_active(self) -> Workspace | None:
        """Get the currently active workspace."""
        pass

    @abstractmethod
    def update(self, workspace: Workspace) -> Workspace:
        """Update workspace."""
        pass

    @abstractmethod
    def delete(self, workspace_id: str) -> bool:
        """Delete workspace by ID."""
        pass

    @abstractmethod
    def set_active(self, workspace_id: str) -> bool:
        """Set workspace as active."""
        pass


class FileRepository(ABC):
    """Abstract repository for file operations."""

    @abstractmethod
    def create(self, file: FileMetadata) -> FileMetadata:
        """Create a new file record."""
        pass

    @abstractmethod
    def get_by_id(self, file_id: str) -> FileMetadata | None:
        """Get file by ID."""
        pass

    @abstractmethod
    def get_by_workspace(self, workspace_id: str) -> list[FileMetadata]:
        """Get all files in a workspace."""
        pass

    @abstractmethod
    def get_by_status(self, workspace_id: str, status: str) -> list[FileMetadata]:
        """Get files by status."""
        pass

    @abstractmethod
    def update(self, file: FileMetadata) -> FileMetadata:
        """Update file record."""
        pass

    @abstractmethod
    def delete(self, file_id: str) -> bool:
        """Delete file by ID."""
        pass

    @abstractmethod
    def count_by_workspace(self, workspace_id: str) -> int:
        """Count files in workspace."""
        pass


class ChunkRepository(ABC):
    """Abstract repository for chunk operations."""

    @abstractmethod
    def create(self, chunk: ChunkMetadata) -> ChunkMetadata:
        """Create a new chunk record."""
        pass

    @abstractmethod
    def get_by_id(self, chunk_id: str) -> ChunkMetadata | None:
        """Get chunk by ID."""
        pass

    @abstractmethod
    def get_by_file(self, file_id: str) -> list[ChunkMetadata]:
        """Get all chunks for a file."""
        pass

    @abstractmethod
    def get_by_workspace(self, workspace_id: str) -> list[ChunkMetadata]:
        """Get all chunks in a workspace."""
        pass

    @abstractmethod
    def delete_by_file(self, file_id: str) -> bool:
        """Delete all chunks for a file."""
        pass

    @abstractmethod
    def delete_by_workspace(self, workspace_id: str) -> bool:
        """Delete all chunks in a workspace."""
        pass

    @abstractmethod
    def count_by_workspace(self, workspace_id: str) -> int:
        """Count chunks in workspace."""
        pass


class MessageRepository(ABC):
    """Abstract repository for message operations."""

    @abstractmethod
    def create(self, message: Message) -> Message:
        """Create a new message."""
        pass

    @abstractmethod
    def get_by_id(self, message_id: str) -> Message | None:
        """Get message by ID."""
        pass

    @abstractmethod
    def get_by_workspace(
        self, workspace_id: str, limit: int = 100, offset: int = 0
    ) -> list[Message]:
        """Get messages for a workspace with pagination."""
        pass

    @abstractmethod
    def get_recent(self, workspace_id: str, limit: int = 50) -> list[Message]:
        """Get recent messages."""
        pass

    @abstractmethod
    def update(self, message: Message) -> Message:
        """Update message."""
        pass

    @abstractmethod
    def delete(self, message_id: str) -> bool:
        """Delete message by ID."""
        pass

    @abstractmethod
    def clear_by_workspace(self, workspace_id: str) -> bool:
        """Clear all messages in workspace."""
        pass

    @abstractmethod
    def count_by_workspace(self, workspace_id: str) -> int:
        """Count messages in workspace."""
        pass


class QARepository(ABC):
    """Abstract repository for Q&A pair operations."""

    @abstractmethod
    def create(self, qa: QAPair) -> QAPair:
        """Create a new Q&A pair."""
        pass

    @abstractmethod
    def get_by_id(self, qa_id: str) -> QAPair | None:
        """Get Q&A pair by ID."""
        pass

    @abstractmethod
    def get_by_workspace(self, workspace_id: str) -> list[QAPair]:
        """Get all Q&A pairs in workspace."""
        pass

    @abstractmethod
    def get_by_file(self, file_id: str) -> list[QAPair]:
        """Get all Q&A pairs for a file."""
        pass

    @abstractmethod
    def update(self, qa: QAPair) -> QAPair:
        """Update Q&A pair."""
        pass

    @abstractmethod
    def update_votes(self, qa_id: str, likes: int, dislikes: int) -> bool:
        """Update vote counts."""
        pass

    @abstractmethod
    def delete(self, qa_id: str) -> bool:
        """Delete Q&A pair."""
        pass


class PreferencesRepository(ABC):
    """Abstract repository for user preferences."""

    @abstractmethod
    def get(self) -> UserPreferences:
        """Get user preferences."""
        pass

    @abstractmethod
    def save(self, preferences: UserPreferences) -> UserPreferences:
        """Save user preferences."""
        pass

    @abstractmethod
    def update_weights(self, weights: dict[str, float]) -> UserPreferences:
        """Update preference weights."""
        pass

    @abstractmethod
    def update_config(self, config: dict[str, Any]) -> UserPreferences:
        """Update configuration."""
        pass


class JobRepository(ABC):
    """Abstract repository for job operations."""

    @abstractmethod
    def create(self, job: Job) -> Job:
        """Create a new job."""
        pass

    @abstractmethod
    def get_by_id(self, job_id: str) -> Job | None:
        """Get job by ID."""
        pass

    @abstractmethod
    def get_by_workspace(self, workspace_id: str) -> list[Job]:
        """Get all jobs in workspace."""
        pass

    @abstractmethod
    def get_by_status(self, status: str) -> list[Job]:
        """Get jobs by status."""
        pass

    @abstractmethod
    def get_pending(self, limit: int = 10) -> list[Job]:
        """Get pending jobs."""
        pass

    @abstractmethod
    def update(self, job: Job) -> Job:
        """Update job."""
        pass

    @abstractmethod
    def update_progress(self, job_id: str, progress: float, current: int) -> bool:
        """Update job progress."""
        pass

    @abstractmethod
    def delete(self, job_id: str) -> bool:
        """Delete job."""
        pass

    @abstractmethod
    def delete_completed(self, older_than_days: int = 7) -> int:
        """Delete completed jobs older than specified days."""
        pass
