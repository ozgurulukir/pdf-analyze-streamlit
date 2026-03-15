"""Database manager for SQLite storage."""
import sqlite3
import json
import os
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path

from app.core.models import (
    Workspace, FileMetadata, ChunkMetadata, 
    Message, QAPair, UserPreferences, Job
)


class DatabaseManager:
    """SQLite database manager for metadata storage."""

    def __init__(self, db_path: str = "data/app.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self):
        """Get database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Initialize database tables."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Workspaces table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS workspaces (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    created_at TEXT NOT NULL,
                    last_modified TEXT NOT NULL,
                    file_count INTEGER DEFAULT 0,
                    is_active INTEGER DEFAULT 0
                )
            """)
            
            # Files table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS files (
                    id TEXT PRIMARY KEY,
                    workspace_id TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    original_name TEXT NOT NULL,
                    file_type TEXT,
                    size INTEGER,
                    status TEXT DEFAULT 'pending',
                    chunk_count INTEGER DEFAULT 0,
                    uploaded_at TEXT NOT NULL,
                    processed_at TEXT,
                    error_message TEXT,
                    tags TEXT,
                    FOREIGN KEY (workspace_id) REFERENCES workspaces(id)
                )
            """)
            
            # Chunks table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chunks (
                    id TEXT PRIMARY KEY,
                    file_id TEXT NOT NULL,
                    workspace_id TEXT NOT NULL,
                    chunk_index INTEGER,
                    text_snippet TEXT,
                    chroma_id TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (file_id) REFERENCES files(id),
                    FOREIGN KEY (workspace_id) REFERENCES workspaces(id)
                )
            """)
            
            # Messages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    workspace_id TEXT,
                    sources TEXT,
                    is_summarized INTEGER DEFAULT 0
                )
            """)
            
            # Q&A pairs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS qa_pairs (
                    id TEXT PRIMARY KEY,
                    workspace_id TEXT,
                    file_ids TEXT,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    likes INTEGER DEFAULT 0,
                    dislikes INTEGER DEFAULT 0
                )
            """)
            
            # Preferences table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS preferences (
                    id INTEGER PRIMARY KEY,
                    weights TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            
            # Jobs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    job_type TEXT NOT NULL,
                    workspace_id TEXT,
                    file_ids TEXT,
                    status TEXT DEFAULT 'pending',
                    progress REAL DEFAULT 0,
                    total INTEGER DEFAULT 0,
                    current INTEGER DEFAULT 0,
                    error_message TEXT,
                    created_at TEXT NOT NULL,
                    started_at TEXT,
                    completed_at TEXT
                )
            """)
            
            conn.commit()

    # ============= Workspace Methods =============

    def create_workspace(self, workspace: Workspace) -> Workspace:
        """Create a new workspace."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO workspaces (id, name, description, created_at, last_modified, file_count, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (workspace.id, workspace.name, workspace.description, 
                  workspace.created_at.isoformat(), workspace.last_modified.isoformat(),
                  workspace.file_count, 1 if workspace.is_active else 0))
            conn.commit()
        return workspace

    def get_workspaces(self) -> List[Workspace]:
        """Get all workspaces."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM workspaces ORDER BY last_modified DESC")
            rows = cursor.fetchall()
            return [Workspace.from_dict(dict(row)) for row in rows]

    def get_workspace(self, workspace_id: str) -> Optional[Workspace]:
        """Get a workspace by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM workspaces WHERE id = ?", (workspace_id,))
            row = cursor.fetchone()
            return Workspace.from_dict(dict(row)) if row else None

    def update_workspace(self, workspace: Workspace) -> Workspace:
        """Update a workspace."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE workspaces 
                SET name = ?, description = ?, last_modified = ?, file_count = ?, is_active = ?
                WHERE id = ?
            """, (workspace.name, workspace.description, workspace.last_modified.isoformat(),
                  workspace.file_count, 1 if workspace.is_active else 0, workspace.id))
            conn.commit()
        return workspace

    def delete_workspace(self, workspace_id: str):
        """Delete a workspace."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM chunks WHERE workspace_id = ?", (workspace_id,))
            cursor.execute("DELETE FROM files WHERE workspace_id = ?", (workspace_id,))
            cursor.execute("DELETE FROM workspaces WHERE id = ?", (workspace_id,))
            conn.commit()

    def set_active_workspace(self, workspace_id: str):
        """Set active workspace."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE workspaces SET is_active = 0")
            cursor.execute("UPDATE workspaces SET is_active = 1 WHERE id = ?", (workspace_id,))
            conn.commit()

    # ============= File Methods =============

    def create_file(self, file_meta: FileMetadata) -> FileMetadata:
        """Create a new file record."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO files (id, workspace_id, filename, original_name, file_type, size, status, 
                                 chunk_count, uploaded_at, processed_at, error_message, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (file_meta.id, file_meta.workspace_id, file_meta.filename, file_meta.original_name,
                  file_meta.file_type, file_meta.size, file_meta.status, file_meta.chunk_count,
                  file_meta.uploaded_at.isoformat(), 
                  file_meta.processed_at.isoformat() if file_meta.processed_at else None,
                  file_meta.error_message, json.dumps(file_meta.tags)))
            conn.commit()
        return file_meta

    def get_files(self, workspace_id: str) -> List[FileMetadata]:
        """Get all files in a workspace."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM files WHERE workspace_id = ? ORDER BY uploaded_at DESC", (workspace_id,))
            rows = cursor.fetchall()
            return [FileMetadata.from_dict(dict(row)) for row in rows]

    def update_file(self, file_meta: FileMetadata) -> FileMetadata:
        """Update a file record."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE files 
                SET status = ?, chunk_count = ?, processed_at = ?, error_message = ?, tags = ?
                WHERE id = ?
            """, (file_meta.status, file_meta.chunk_count,
                  file_meta.processed_at.isoformat() if file_meta.processed_at else None,
                  file_meta.error_message, json.dumps(file_meta.tags), file_meta.id))
            conn.commit()
        return file_meta

    def delete_file(self, file_id: str):
        """Delete a file record."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM chunks WHERE file_id = ?", (file_id,))
            cursor.execute("DELETE FROM files WHERE id = ?", (file_id,))
            conn.commit()

    # ============= Message Methods =============

    def add_message(self, message: Message) -> Message:
        """Add a message."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO messages (id, role, content, timestamp, workspace_id, sources, is_summarized)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (message.id, message.role, message.content, message.timestamp.isoformat(),
                  message.workspace_id, json.dumps(message.sources), 1 if message.is_summarized else 0))
            conn.commit()
        return message

    def get_messages(self, workspace_id: Optional[str] = None, limit: int = 100) -> List[Message]:
        """Get messages, optionally filtered by workspace."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if workspace_id:
                cursor.execute("""
                    SELECT * FROM messages 
                    WHERE workspace_id = ? 
                    ORDER BY timestamp DESC LIMIT ?
                """, (workspace_id, limit))
            else:
                cursor.execute("SELECT * FROM messages ORDER BY timestamp DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            return [Message.from_dict(dict(row)) for row in rows]

    def clear_messages(self, workspace_id: Optional[str] = None):
        """Clear messages."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if workspace_id:
                cursor.execute("DELETE FROM messages WHERE workspace_id = ?", (workspace_id,))
            else:
                cursor.execute("DELETE FROM messages")
            conn.commit()

    # ============= Q&A Methods =============

    def create_qa_pair(self, qa: QAPair) -> QAPair:
        """Create a Q&A pair."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO qa_pairs (id, workspace_id, file_ids, question, answer, created_at, likes, dislikes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (qa.id, qa.workspace_id, json.dumps(qa.file_ids), qa.question, qa.answer,
                  qa.created_at.isoformat(), qa.likes, qa.dislikes))
            conn.commit()
        return qa

    def get_qa_pairs(self, workspace_id: Optional[str] = None) -> List[QAPair]:
        """Get Q&A pairs."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if workspace_id:
                cursor.execute("SELECT * FROM qa_pairs WHERE workspace_id = ? ORDER BY created_at DESC", (workspace_id,))
            else:
                cursor.execute("SELECT * FROM qa_pairs ORDER BY created_at DESC")
            rows = cursor.fetchall()
            return [QAPair.from_dict(dict(row)) for row in rows]

    def update_qa_votes(self, qa_id: str, likes: int, dislikes: int):
        """Update Q&A votes."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE qa_pairs SET likes = ?, dislikes = ? WHERE id = ?", (likes, dislikes, qa_id))
            conn.commit()

    # ============= Preferences Methods =============

    def get_preferences(self) -> UserPreferences:
        """Get user preferences."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM preferences WHERE id = 1")
            row = cursor.fetchone()
            if row:
                return UserPreferences.from_dict(dict(row))
            return UserPreferences()

    def save_preferences(self, prefs: UserPreferences):
        """Save user preferences."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO preferences (id, weights, updated_at)
                VALUES (1, ?, ?)
            """, (json.dumps(prefs.weights), prefs.updated_at.isoformat()))
            conn.commit()

    # ============= Job Methods =============

    def create_job(self, job: Job) -> Job:
        """Create a new job."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO jobs (id, job_type, workspace_id, file_ids, status, progress, total, current, 
                                error_message, created_at, started_at, completed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (job.id, job.job_type, job.workspace_id, json.dumps(job.file_ids), job.status,
                  job.progress, job.total, job.current, job.error_message,
                  job.created_at.isoformat(), 
                  job.started_at.isoformat() if job.started_at else None,
                  job.completed_at.isoformat() if job.completed_at else None))
            conn.commit()
        return job

    def update_job(self, job: Job) -> Job:
        """Update a job."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE jobs 
                SET status = ?, progress = ?, total = ?, current = ?, error_message = ?,
                    started_at = ?, completed_at = ?
                WHERE id = ?
            """, (job.status, job.progress, job.total, job.current, job.error_message,
                  job.started_at.isoformat() if job.started_at else None,
                  job.completed_at.isoformat() if job.completed_at else None,
                  job.id))
            conn.commit()
        return job

    def get_jobs(self, workspace_id: Optional[str] = None) -> List[Job]:
        """Get pending/running jobs."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if workspace_id:
                cursor.execute("""
                    SELECT * FROM jobs 
                    WHERE workspace_id = ? AND status IN ('pending', 'running')
                    ORDER BY created_at DESC
                """, (workspace_id,))
            else:
                cursor.execute("""
                    SELECT * FROM jobs 
                    WHERE status IN ('pending', 'running')
                    ORDER BY created_at DESC
                """)
            rows = cursor.fetchall()
            return [Job(**dict(row)) for row in rows]
