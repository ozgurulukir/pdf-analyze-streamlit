"""Data models for the application."""
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
import json


def generate_id() -> str:
    """Generate a unique ID."""
    return str(uuid.uuid4())


def now() -> datetime:
    """Get current timestamp."""
    return datetime.now()


@dataclass
class Workspace:
    """Workspace model - contains multiple files."""
    id: str = field(default_factory=generate_id)
    name: str = ""
    description: str = ""
    created_at: datetime = field(default_factory=now)
    last_modified: datetime = field(default_factory=now)
    file_count: int = 0
    is_active: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "last_modified": self.last_modified.isoformat(),
            "file_count": self.file_count,
            "is_active": self.is_active
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Workspace':
        return cls(
            id=data.get("id", generate_id()),
            name=data.get("name", ""),
            description=data.get("description", ""),
            created_at=datetime.fromisoformat(data.get("created_at", now().isoformat())),
            last_modified=datetime.fromisoformat(data.get("last_modified", now().isoformat())),
            file_count=data.get("file_count", 0),
            is_active=data.get("is_active", False)
        )


@dataclass
class FileMetadata:
    """File metadata model."""
    id: str = field(default_factory=generate_id)
    workspace_id: str = ""
    filename: str = ""
    original_name: str = ""
    file_type: str = ""
    size: int = 0
    status: str = "pending"  # pending, processing, processed, error
    chunk_count: int = 0
    uploaded_at: datetime = field(default_factory=now)
    processed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "filename": self.filename,
            "original_name": self.original_name,
            "file_type": self.file_type,
            "size": self.size,
            "status": self.status,
            "chunk_count": self.chunk_count,
            "uploaded_at": self.uploaded_at.isoformat(),
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "error_message": self.error_message,
            "tags": self.tags
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FileMetadata':
        return cls(
            id=data.get("id", generate_id()),
            workspace_id=data.get("workspace_id", ""),
            filename=data.get("filename", ""),
            original_name=data.get("original_name", ""),
            file_type=data.get("file_type", ""),
            size=data.get("size", 0),
            status=data.get("status", "pending"),
            chunk_count=data.get("chunk_count", 0),
            uploaded_at=datetime.fromisoformat(data.get("uploaded_at", now().isoformat())),
            processed_at=datetime.fromisoformat(data["processed_at"]) if data.get("processed_at") else None,
            error_message=data.get("error_message"),
            tags=data.get("tags", [])
        )


@dataclass
class ChunkMetadata:
    """Chunk/vector metadata model."""
    id: str = field(default_factory=generate_id)
    file_id: str = ""
    workspace_id: str = ""
    chunk_index: int = 0
    text_snippet: str = ""
    chroma_id: str = ""
    created_at: datetime = field(default_factory=now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "file_id": self.file_id,
            "workspace_id": self.workspace_id,
            "chunk_index": self.chunk_index,
            "text_snippet": self.text_snippet[:200],  # Store first 200 chars
            "chroma_id": self.chroma_id,
            "created_at": self.created_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChunkMetadata':
        return cls(
            id=data.get("id", generate_id()),
            file_id=data.get("file_id", ""),
            workspace_id=data.get("workspace_id", ""),
            chunk_index=data.get("chunk_index", 0),
            text_snippet=data.get("text_snippet", ""),
            chroma_id=data.get("chroma_id", ""),
            created_at=datetime.fromisoformat(data.get("created_at", now().isoformat()))
        )


@dataclass
class Message:
    """Chat message model."""
    id: str = field(default_factory=generate_id)
    role: str = "user"  # user, assistant, system
    content: str = ""
    timestamp: datetime = field(default_factory=now)
    workspace_id: Optional[str] = None
    sources: List[str] = field(default_factory=list)
    is_summarized: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "workspace_id": self.workspace_id,
            "sources": self.sources,
            "is_summarized": self.is_summarized
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        return cls(
            id=data.get("id", generate_id()),
            role=data.get("role", "user"),
            content=data.get("content", ""),
            timestamp=datetime.fromisoformat(data.get("timestamp", now().isoformat())),
            workspace_id=data.get("workspace_id"),
            sources=data.get("sources", []),
            is_summarized=data.get("is_summarized", False)
        )


@dataclass
class QAPair:
    """Q&A pair for dashboard."""
    id: str = field(default_factory=generate_id)
    workspace_id: str = ""
    file_ids: List[str] = field(default_factory=list)
    question: str = ""
    answer: str = ""
    created_at: datetime = field(default_factory=now)
    likes: int = 0
    dislikes: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "file_ids": self.file_ids,
            "question": self.question,
            "answer": self.answer,
            "created_at": self.created_at.isoformat(),
            "likes": self.likes,
            "dislikes": self.dislikes
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QAPair':
        return cls(
            id=data.get("id", generate_id()),
            workspace_id=data.get("workspace_id", ""),
            file_ids=data.get("file_ids", []),
            question=data.get("question", ""),
            answer=data.get("answer", ""),
            created_at=datetime.fromisoformat(data.get("created_at", now().isoformat())),
            likes=data.get("likes", 0),
            dislikes=data.get("dislikes", 0)
        )


@dataclass
class UserPreferences:
    """User preference weights for responses."""
    weights: Dict[str, float] = field(default_factory=lambda: {
        "concise": 0.5,
        "detailed": 0.5,
        "examples": 0.5,
        "step_by_step": 0.5
    })
    updated_at: datetime = field(default_factory=now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "weights": self.weights,
            "updated_at": self.updated_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserPreferences':
        return cls(
            weights=data.get("weights", {
                "concise": 0.5,
                "detailed": 0.5,
                "examples": 0.5,
                "step_by_step": 0.5
            }),
            updated_at=datetime.fromisoformat(data.get("updated_at", now().isoformat()))
        )

    def adjust_weight(self, tag: str, delta: float):
        """Adjust a preference weight."""
        if tag in self.weights:
            self.weights[tag] = max(0, min(1, self.weights[tag] + delta))
            self.updated_at = now()


@dataclass
class Job:
    """Background job model."""
    id: str = field(default_factory=generate_id)
    job_type: str = ""  # embed, reindex, delete
    workspace_id: str = ""
    file_ids: List[str] = field(default_factory=list)
    status: str = "pending"  # pending, running, completed, failed
    progress: float = 0.0
    total: int = 0
    current: int = 0
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "job_type": self.job_type,
            "workspace_id": self.workspace_id,
            "file_ids": self.file_ids,
            "status": self.status,
            "progress": self.progress,
            "total": self.total,
            "current": self.current,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }
