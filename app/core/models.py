"""Data models for the application with Pydantic validation."""

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.constants import FileTypes, ProcessingStatus


def generate_id() -> str:
    """Generate a unique UUID v4 string."""
    return str(uuid.uuid4())


def now() -> datetime:
    """Get current UTC-aware timestamp."""
    return datetime.now()


# ===================
# Pydantic Models (Primary)
# ===================


class WorkspaceModel(BaseModel):
    """
    Workspace model - logical container for a collection of files.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: str = Field(default_factory=generate_id)
    name: str = Field(min_length=1, max_length=255, description="Workspace name")
    description: str = Field(default="", max_length=1000)
    created_at: datetime = Field(default_factory=now)
    last_modified: datetime = Field(default_factory=now)
    file_count: int = Field(ge=0, default=0)
    is_active: bool = Field(default=False)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate workspace name."""
        if not v or not v.strip():
            raise ValueError("Workspace name cannot be empty")
        return v.strip()

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary."""
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorkspaceModel":
        """Create model from dictionary."""
        return cls(**data)


class FileMetadataModel(BaseModel):
    """
    File metadata model - tracks processing status and properties.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: str = Field(default_factory=generate_id)
    workspace_id: str = Field(min_length=1)
    filename: str = Field(max_length=255)
    original_name: str = Field(max_length=255)
    file_type: str = Field(default="")
    size: int = Field(ge=0, default=0)
    status: str = Field(default="pending")
    chunk_count: int = Field(ge=0, default=0)
    content_hash: str | None = None
    uploaded_at: datetime = Field(default_factory=now)
    processed_at: datetime | None = None
    error_message: str | None = None
    tags: list[str] = Field(default_factory=list)

    @field_validator("file_type")
    @classmethod
    def validate_file_type(cls, v: str) -> str:
        """Validate file type is allowed."""
        if v and not FileTypes.is_allowed(v):
            raise ValueError(f"File type '{v}' is not allowed")
        return v

    @field_validator("size")
    @classmethod
    def validate_size(cls, v: int) -> int:
        """Validate file size is within limits."""
        from app.core.config import AppConfig

        config = AppConfig()
        if v > config.MAX_FILE_SIZE_BYTES:
            raise ValueError(
                f"File size exceeds maximum of {config.MAX_FILE_SIZE_MB}MB"
            )
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate processing status."""
        valid_statuses = [s.value for s in ProcessingStatus]
        if v not in valid_statuses:
            raise ValueError(f"Invalid status: {v}. Must be one of {valid_statuses}")
        return v

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary."""
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FileMetadataModel":
        """Create model from dictionary."""
        return cls(**data)

    def compute_hash(self, content: bytes) -> str:
        """Compute SHA256 hash of file content."""
        return hashlib.sha256(content).hexdigest()


class ChunkMetadataModel(BaseModel):
    """
    Chunk metadata model - tracks text fragments and vector associations.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: str = Field(default_factory=generate_id)
    file_id: str = Field(min_length=1)
    workspace_id: str = Field(min_length=1)
    chunk_index: int = Field(ge=0)
    content: str = Field(default="")
    chroma_id: str = Field(default="")
    page_number: int | None = Field(default=None)
    token_count: int | None = Field(default=None)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=now)

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        """Ensure content is not empty."""
        if not v or not v.strip():
            raise ValueError("Content cannot be empty")
        return v

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary."""
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ChunkMetadataModel":
        """Create model from dictionary."""
        return cls(**data)


class MessageModel(BaseModel):
    """
    Chat message model.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: str = Field(default_factory=generate_id)
    role: str = Field(description="Message role: user, assistant, or system")
    content: str = Field(min_length=0, max_length=50000)
    timestamp: datetime = Field(default_factory=now)
    workspace_id: str | None = None
    session_id: str | None = None
    sources: list[dict[str, Any]] | None = Field(default_factory=list)
    is_summarized: bool = Field(default=False)

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        """Validate message role."""
        valid_roles = ["user", "assistant", "system"]
        if v not in valid_roles:
            raise ValueError(f"Invalid role: {v}. Must be one of {valid_roles}")
        return v

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        """Validate message content."""
        if len(v) > 50000:
            raise ValueError(
                "Message content exceeds maximum length of 50000 characters"
            )
        return v

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary."""
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MessageModel":
        """Create model from dictionary."""
        return cls(**data)


class ChatSessionModel(BaseModel):
    """
    Model for a chat session/thread within a workspace.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: str = Field(default_factory=generate_id)
    workspace_id: str = Field(min_length=1)
    title: str = Field(default="Yeni Sohbet", max_length=255)
    created_at: datetime = Field(default_factory=now)
    last_message_at: datetime = Field(default_factory=now)

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary."""
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ChatSessionModel":
        """Create model from dictionary."""
        return cls(**data)


class QAPairModel(BaseModel):
    """
    Q&A pair model for extracted questions and answers.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: str = Field(default_factory=generate_id)
    workspace_id: str | None = None
    file_ids: list[str] = Field(default_factory=list)
    question: str = Field(min_length=1, max_length=5000)
    answer: str = Field(min_length=1)
    created_at: datetime = Field(default_factory=now)
    likes: int = Field(ge=0, default=0)
    dislikes: int = Field(ge=0, default=0)
    tags: list[str] = Field(default_factory=list)

    @field_validator("question")
    @classmethod
    def validate_question(cls, v: str) -> str:
        """Validate question is not empty."""
        if not v or not v.strip():
            raise ValueError("Question cannot be empty")
        return v.strip()

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary."""
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "QAPairModel":
        """Create model from dictionary."""
        return cls(**data)


class UserPreferencesModel(BaseModel):
    """
    User preferences model for response customization.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: int = Field(default=1)
    weights: dict[str, float] = Field(
        default_factory=lambda: {
            "concise": 0.5,
            "detailed": 0.5,
            "examples": 0.5,
            "step_by_step": 0.5,
        }
    )
    config: dict[str, Any] = Field(default_factory=dict)
    updated_at: datetime = Field(default_factory=now)

    @field_validator("weights")
    @classmethod
    def validate_weights(cls, v: dict[str, float]) -> dict[str, float]:
        """Validate preference weights are in valid range."""
        for key, value in v.items():
            if not 0 <= value <= 1:
                raise ValueError(f"Weight '{key}' must be between 0 and 1, got {value}")
        return v

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary."""
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UserPreferencesModel":
        """Create model from dictionary."""
        return cls(**data)


class JobModel(BaseModel):
    """
    Background job model for tracking async operations.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: str = Field(default_factory=generate_id)
    job_type: str = Field(min_length=1)
    workspace_id: str | None = None
    file_ids: list[str] = Field(default_factory=list)
    status: str = Field(default="pending")
    progress: float = Field(ge=0, le=100, default=0)
    total: int = Field(ge=0, default=0)
    current: int = Field(ge=0, default=0)
    error_message: str | None = None
    created_at: datetime = Field(default_factory=now)
    started_at: datetime | None = None
    completed_at: datetime | None = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate job status."""
        valid_statuses = [s.value for s in ProcessingStatus]
        if v not in valid_statuses:
            raise ValueError(f"Invalid status: {v}")
        return v

    @field_validator("progress", mode="before")
    @classmethod
    def validate_progress(cls, v: Any) -> float:
        """Ensure progress is between 0 and 1."""
        try:
            return max(0.0, min(100.0, float(v)))
        except (ValueError, TypeError):
            return 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary."""
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "JobModel":
        """Create model from dictionary."""
        return cls(**data)

    def is_complete(self) -> bool:
        """Check if job is complete."""
        return self.status in [
            ProcessingStatus.COMPLETED.value,
            ProcessingStatus.FAILED.value,
        ]


# ===================
# Dataclass Models (Legacy - for backward compatibility)
# ===================


@dataclass
class Workspace:
    """Legacy workspace model - use WorkspaceModel instead."""

    id: str = field(default_factory=generate_id)
    name: str = ""
    description: str = ""
    created_at: datetime = field(default_factory=now)
    last_modified: datetime = field(default_factory=now)
    file_count: int = 0
    is_active: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_modified": self.last_modified.isoformat()
            if self.last_modified
            else None,
            "file_count": self.file_count,
            "is_active": self.is_active,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Workspace":
        return cls(**WorkspaceModel(**data).model_dump())


@dataclass
class FileMetadata:
    """Legacy file metadata model - use FileMetadataModel instead."""

    id: str = field(default_factory=generate_id)
    workspace_id: str = ""
    filename: str = ""
    original_name: str = ""
    file_type: str = ""
    size: int = 0
    status: str = "pending"
    chunk_count: int = 0
    uploaded_at: datetime = field(default_factory=now)
    processed_at: datetime | None = None
    error_message: str | None = None
    content_hash: str | None = None
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "filename": self.filename,
            "original_name": self.original_name,
            "file_type": self.file_type,
            "size": self.size,
            "status": self.status,
            "chunk_count": self.chunk_count,
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None,
            "processed_at": self.processed_at.isoformat()
            if self.processed_at
            else None,
            "error_message": self.error_message,
            "content_hash": self.content_hash,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FileMetadata":
        """Create model from dictionary, handling JSON string fields."""
        processed_data = data.copy()

        # Handle tags field (stored as string in DB)
        if "tags" in processed_data and isinstance(processed_data["tags"], str):
            try:
                processed_data["tags"] = json.loads(processed_data["tags"])
            except (json.JSONDecodeError, TypeError):
                processed_data["tags"] = []

        return cls(**FileMetadataModel(**processed_data).model_dump())


@dataclass
class ChunkMetadata:
    """Legacy chunk metadata model - use ChunkMetadataModel instead."""

    id: str = field(default_factory=generate_id)
    file_id: str = ""
    workspace_id: str = ""
    chunk_index: int = 0
    content: str = ""
    chroma_id: str = ""
    page_number: int | None = None
    token_count: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=now)

    def to_dict(self) -> dict[str, Any]:
        return ChunkMetadataModel.model_validate(self).to_dict()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ChunkMetadata":
        return cls(**ChunkMetadataModel(**data).model_dump())


@dataclass
class Message:
    """Legacy message model - use MessageModel instead."""

    id: str = field(default_factory=generate_id)
    role: str = "user"
    content: str = ""
    timestamp: datetime = field(default_factory=now)
    workspace_id: str | None = None
    session_id: str | None = None
    sources: list[dict[str, Any]] | None = field(default_factory=list)
    is_summarized: bool = False

    def to_dict(self) -> dict[str, Any]:
        return MessageModel.model_validate(self).to_dict()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Message":
        processed_data = data.copy()
        return cls(**MessageModel(**processed_data).model_dump())


@dataclass
class ChatSession:
    """Legacy chat session model."""

    id: str = field(default_factory=generate_id)
    workspace_id: str = ""
    title: str = "Yeni Sohbet"
    created_at: datetime = field(default_factory=now)
    last_message_at: datetime = field(default_factory=now)

    def to_dict(self) -> dict[str, Any]:
        return ChatSessionModel.model_validate(self).to_dict()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ChatSession":
        return cls(**ChatSessionModel(**data).model_dump())


@dataclass
class QAPair:
    """Legacy Q&A pair model - use QAPairModel instead."""

    id: str = field(default_factory=generate_id)
    workspace_id: str | None = None
    file_ids: list[str] = field(default_factory=list)
    question: str = ""
    answer: str = ""
    created_at: datetime = field(default_factory=now)
    likes: int = 0
    dislikes: int = 0
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return QAPairModel.model_validate(self).to_dict()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "QAPair":
        return cls(**QAPairModel(**data).model_dump())


@dataclass
class UserPreferences:
    """Legacy user preferences model - use UserPreferencesModel instead."""

    id: int = 1
    weights: dict[str, float] = field(
        default_factory=lambda: {
            "concise": 0.5,
            "detailed": 0.5,
            "examples": 0.5,
            "step_by_step": 0.5,
        }
    )
    config: dict[str, Any] = field(default_factory=dict)
    updated_at: datetime = field(default_factory=now)

    def to_dict(self) -> dict[str, Any]:
        return UserPreferencesModel.model_validate(self).to_dict()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UserPreferences":
        """Create model from dictionary, handling JSON string fields."""
        # Handle JSON string fields from database
        processed_data = data.copy()

        if "weights" in processed_data and isinstance(processed_data["weights"], str):
            try:
                processed_data["weights"] = json.loads(processed_data["weights"])
            except (json.JSONDecodeError, TypeError):
                processed_data["weights"] = {
                    "concise": 0.5,
                    "detailed": 0.5,
                    "examples": 0.5,
                    "step_by_step": 0.5,
                }

        if "config" in processed_data and processed_data["config"]:
            if isinstance(processed_data["config"], str):
                try:
                    processed_data["config"] = json.loads(processed_data["config"])
                except (json.JSONDecodeError, TypeError):
                    processed_data["config"] = None

        return cls(**UserPreferencesModel(**processed_data).model_dump())


@dataclass
class Job:
    """Legacy job model - use JobModel instead."""

    id: str = field(default_factory=generate_id)
    job_type: str = ""
    workspace_id: str | None = None
    file_ids: list[str] = field(default_factory=list)
    status: str = "pending"
    progress: float = 0.0
    total: int = 0
    current: int = 0
    error_message: str | None = None
    created_at: datetime = field(default_factory=now)
    started_at: datetime | None = None
    completed_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        return JobModel.model_validate(self).to_dict()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Job":
        processed_data = data.copy()

        # Handle file_ids field (stored as string in DB)
        if "file_ids" in processed_data and isinstance(processed_data["file_ids"], str):
            try:
                processed_data["file_ids"] = json.loads(processed_data["file_ids"])
            except (json.JSONDecodeError, TypeError):
                processed_data["file_ids"] = []

        return cls(**JobModel(**processed_data).model_dump())
