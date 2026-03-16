"""Data models for the application with Pydantic validation."""
import uuid
import json
import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict

from app.core.constants import ProcessingStatus, FileTypes


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
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate workspace name."""
        if not v or not v.strip():
            raise ValueError("Workspace name cannot be empty")
        return v.strip()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return self.model_dump()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkspaceModel':
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
    content_hash: Optional[str] = None
    uploaded_at: datetime = Field(default_factory=now)
    processed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    
    @field_validator('file_type')
    @classmethod
    def validate_file_type(cls, v: str) -> str:
        """Validate file type is allowed."""
        if v and not FileTypes.is_allowed(v):
            raise ValueError(f"File type '{v}' is not allowed")
        return v
    
    @field_validator('size')
    @classmethod
    def validate_size(cls, v: int) -> int:
        """Validate file size is within limits."""
        from app.core.config import AppConfig
        config = AppConfig()
        if v > config.MAX_FILE_SIZE_BYTES:
            raise ValueError(f"File size exceeds maximum of {config.MAX_FILE_SIZE_MB}MB")
        return v
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate processing status."""
        valid_statuses = [s.value for s in ProcessingStatus]
        if v not in valid_statuses:
            raise ValueError(f"Invalid status: {v}. Must be one of {valid_statuses}")
        return v
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return self.model_dump()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FileMetadataModel':
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
    text_snippet: str = Field(default="")
    chroma_id: str = Field(default="")
    created_at: datetime = Field(default_factory=now)
    
    @field_validator('text_snippet')
    @classmethod
    def validate_text_snippet(cls, v: str) -> str:
        """Ensure text snippet is not empty."""
        if not v or not v.strip():
            raise ValueError("Text snippet cannot be empty")
        return v
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return self.model_dump()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChunkMetadataModel':
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
    workspace_id: Optional[str] = None
    sources: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    is_summarized: bool = Field(default=False)
    
    @field_validator('role')
    @classmethod
    def validate_role(cls, v: str) -> str:
        """Validate message role."""
        valid_roles = ['user', 'assistant', 'system']
        if v not in valid_roles:
            raise ValueError(f"Invalid role: {v}. Must be one of {valid_roles}")
        return v
    
    @field_validator('content')
    @classmethod
    def validate_content(cls, v: str) -> str:
        """Validate message content."""
        if len(v) > 50000:
            raise ValueError("Message content exceeds maximum length of 50000 characters")
        return v
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return self.model_dump()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MessageModel':
        """Create model from dictionary."""
        return cls(**data)


class QAPairModel(BaseModel):
    """
    Q&A pair model for extracted questions and answers.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    id: str = Field(default_factory=generate_id)
    workspace_id: Optional[str] = None
    file_ids: List[str] = Field(default_factory=list)
    question: str = Field(min_length=1, max_length=5000)
    answer: str = Field(min_length=1)
    created_at: datetime = Field(default_factory=now)
    likes: int = Field(ge=0, default=0)
    dislikes: int = Field(ge=0, default=0)
    
    @field_validator('question')
    @classmethod
    def validate_question(cls, v: str) -> str:
        """Validate question is not empty."""
        if not v or not v.strip():
            raise ValueError("Question cannot be empty")
        return v.strip()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return self.model_dump()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QAPairModel':
        """Create model from dictionary."""
        return cls(**data)


class UserPreferencesModel(BaseModel):
    """
    User preferences model for response customization.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    id: int = Field(default=1)
    weights: Dict[str, float] = Field(default_factory=lambda: {
        "concise": 0.5,
        "detailed": 0.5,
        "examples": 0.5,
        "step_by_step": 0.5
    })
    config: Optional[Dict[str, Any]] = None
    updated_at: datetime = Field(default_factory=now)
    
    @field_validator('weights')
    @classmethod
    def validate_weights(cls, v: Dict[str, float]) -> Dict[str, float]:
        """Validate preference weights are in valid range."""
        for key, value in v.items():
            if not 0 <= value <= 1:
                raise ValueError(f"Weight '{key}' must be between 0 and 1, got {value}")
        return v
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return self.model_dump()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserPreferencesModel':
        """Create model from dictionary."""
        return cls(**data)


class JobModel(BaseModel):
    """
    Background job model for tracking async operations.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    id: str = Field(default_factory=generate_id)
    job_type: str = Field(min_length=1)
    workspace_id: Optional[str] = None
    file_ids: List[str] = Field(default_factory=list)
    status: str = Field(default="pending")
    progress: float = Field(ge=0, le=1, default=0)
    total: int = Field(ge=0, default=0)
    current: int = Field(ge=0, default=0)
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate job status."""
        valid_statuses = [s.value for s in ProcessingStatus]
        if v not in valid_statuses:
            raise ValueError(f"Invalid status: {v}")
        return v
    
    @field_validator('progress')
    @classmethod
    def validate_progress(cls, v: float) -> float:
        """Ensure progress is between 0 and 1."""
        return max(0.0, min(1.0, v))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return self.model_dump()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'JobModel':
        """Create model from dictionary."""
        return cls(**data)
    
    def is_complete(self) -> bool:
        """Check if job is complete."""
        return self.status in [ProcessingStatus.COMPLETED.value, ProcessingStatus.FAILED.value]


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

    def to_dict(self) -> Dict[str, Any]:
        return WorkspaceModel.model_validate(self).to_dict()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Workspace':
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
    processed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    content_hash: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return FileMetadataModel.model_validate(self).to_dict()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FileMetadata':
        """Create model from dictionary, handling JSON string fields."""
        processed_data = data.copy()
        
        # Handle tags field (stored as string in DB)
        if 'tags' in processed_data and isinstance(processed_data['tags'], str):
            try:
                processed_data['tags'] = json.loads(processed_data['tags'])
            except (json.JSONDecodeError, TypeError):
                processed_data['tags'] = []
        
        return cls(**FileMetadataModel(**processed_data).model_dump())


@dataclass
class ChunkMetadata:
    """Legacy chunk metadata model - use ChunkMetadataModel instead."""
    id: str = field(default_factory=generate_id)
    file_id: str = ""
    workspace_id: str = ""
    chunk_index: int = 0
    text_snippet: str = ""
    chroma_id: str = ""
    created_at: datetime = field(default_factory=now)

    def to_dict(self) -> Dict[str, Any]:
        return ChunkMetadataModel.model_validate(self).to_dict()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChunkMetadata':
        return cls(**ChunkMetadataModel(**data).model_dump())


@dataclass
class Message:
    """Legacy message model - use MessageModel instead."""
    id: str = field(default_factory=generate_id)
    role: str = "user"
    content: str = ""
    timestamp: datetime = field(default_factory=now)
    workspace_id: Optional[str] = None
    sources: Optional[List[Dict[str, Any]]] = field(default_factory=list)
    is_summarized: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return MessageModel.model_validate(self).to_dict()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create model from dictionary, handling JSON string fields."""
        processed_data = data.copy()
        
        # Handle sources field (stored as string in DB)
        if 'sources' in processed_data and processed_data['sources']:
            if isinstance(processed_data['sources'], str):
                try:
                    processed_data['sources'] = json.loads(processed_data['sources'])
                except (json.JSONDecodeError, TypeError):
                    processed_data['sources'] = []
        
        return cls(**MessageModel(**processed_data).model_dump())


@dataclass
class QAPair:
    """Legacy Q&A pair model - use QAPairModel instead."""
    id: str = field(default_factory=generate_id)
    workspace_id: Optional[str] = None
    file_ids: List[str] = field(default_factory=list)
    question: str = ""
    answer: str = ""
    created_at: datetime = field(default_factory=now)
    likes: int = 0
    dislikes: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return QAPairModel.model_validate(self).to_dict()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QAPair':
        return cls(**QAPairModel(**data).model_dump())


@dataclass
class UserPreferences:
    """Legacy user preferences model - use UserPreferencesModel instead."""
    id: int = 1
    weights: Dict[str, float] = field(default_factory=lambda: {
        "concise": 0.5,
        "detailed": 0.5,
        "examples": 0.5,
        "step_by_step": 0.5
    })
    config: Optional[Dict[str, Any]] = None
    updated_at: datetime = field(default_factory=now)

    def to_dict(self) -> Dict[str, Any]:
        return UserPreferencesModel.model_validate(self).to_dict()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserPreferences':
        """Create model from dictionary, handling JSON string fields."""
        # Handle JSON string fields from database
        processed_data = data.copy()
        
        if 'weights' in processed_data and isinstance(processed_data['weights'], str):
            try:
                processed_data['weights'] = json.loads(processed_data['weights'])
            except (json.JSONDecodeError, TypeError):
                processed_data['weights'] = {"concise": 0.5, "detailed": 0.5, "examples": 0.5, "step_by_step": 0.5}
        
        if 'config' in processed_data and processed_data['config']:
            if isinstance(processed_data['config'], str):
                try:
                    processed_data['config'] = json.loads(processed_data['config'])
                except (json.JSONDecodeError, TypeError):
                    processed_data['config'] = None
        
        return cls(**UserPreferencesModel(**processed_data).model_dump())


@dataclass
class Job:
    """Legacy job model - use JobModel instead."""
    id: str = field(default_factory=generate_id)
    job_type: str = ""
    workspace_id: Optional[str] = None
    file_ids: List[str] = field(default_factory=list)
    status: str = "pending"
    progress: float = 0.0
    total: int = 0
    current: int = 0
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return JobModel.model_validate(self).to_dict()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Job':
        return cls(**JobModel(**data).model_dump())
