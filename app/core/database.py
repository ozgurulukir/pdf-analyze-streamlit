"""Database manager for SQLite storage."""
import sqlite3
import json
from pathlib import Path
from typing import List, Optional, Dict, Any, Union
from app.core.models import (
    Workspace, FileMetadata, Message, QAPair, UserPreferences, Job
)
from app.core.exceptions import DatabaseError
from app.core.logger import logger
from app.core.config import AppConfig


class DatabaseManager:
    """
    SQLite database manager for metadata storage.
    
    Handles persistence for workspaces, files, chat messages, Q&A pairs,
    user preferences, and background jobs.
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the database manager.
        
        Args:
            db_path: Path to the SQLite database file
        """
        if db_path is None:
            db_path = AppConfig().DB_PATH
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """
        Create and return a database connection.
        
        Returns:
            sqlite3.Connection: A connection object with row_factory set to sqlite3.Row
            
        Raises:
            DatabaseError: If connection fails
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            return conn
        except sqlite3.Error as e:
            logger.error(f"Database connection failed: {e}")
            raise DatabaseError(f"Failed to connect to database at {self.db_path}: {e}")

    def _init_db(self) -> None:
        """
        Initialize database tables if they do not exist.
        
        Raises:
            DatabaseError: If table creation fails
        """
        try:
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
                        content_hash TEXT,
                        uploaded_at TEXT NOT NULL,
                        processed_at TEXT,
                        error_message TEXT,
                        tags TEXT,
                        FOREIGN KEY (workspace_id) REFERENCES workspaces(id)
                    )
                """)
                
                # Auto-migration for older databases missing content_hash
                try:
                    cursor.execute("SELECT content_hash FROM files LIMIT 1")
                except sqlite3.OperationalError:
                    cursor.execute("ALTER TABLE files ADD COLUMN content_hash TEXT")
                
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
                        config TEXT,
                        updated_at TEXT NOT NULL
                    )
                """)
                
                # Auto-migration for older databases missing preference config
                try:
                    cursor.execute("SELECT config FROM preferences LIMIT 1")
                except sqlite3.OperationalError:
                    cursor.execute("ALTER TABLE preferences ADD COLUMN config TEXT")
                
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
                logger.debug("Database initialized successfully")
        except sqlite3.Error as e:
            logger.error(f"Database initialization failed: {e}")
            raise DatabaseError(f"Failed to initialize database: {e}")

    # ============= Workspace Methods =============

    def create_workspace(self, workspace: Workspace) -> Workspace:
        """
        Create a new workspace entry.
        
        Args:
            workspace: The workspace model to persist
            
        Returns:
            Workspace: The persisted workspace model
            
        Raises:
            DatabaseError: If insertion fails
        """
        try:
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
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to create workspace: {e}")

    def get_workspaces(self) -> List[Workspace]:
        """
        Get all workspaces with synchronized file counts.
        
        Returns:
            List[Workspace]: List of all workspace models
            
        Raises:
            DatabaseError: If query fails
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Auto-sync file counts before fetching
                cursor.execute("""
                    UPDATE workspaces
                    SET file_count = (
                        SELECT COUNT(*) 
                        FROM files 
                        WHERE files.workspace_id = workspaces.id
                    )
                """)
                conn.commit()
                
                cursor.execute("SELECT * FROM workspaces ORDER BY last_modified DESC")
                rows = cursor.fetchall()
                return [Workspace.from_dict(dict(row)) for row in rows]
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to fetch workspaces: {e}")

    def get_workspace(self, workspace_id: str) -> Optional[Workspace]:
        """
        Retrieve a specific workspace by its ID.
        
        Args:
            workspace_id: The unique identifier of the workspace
            
        Returns:
            Optional[Workspace]: The workspace model if found, else None
            
        Raises:
            DatabaseError: If query fails
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM workspaces WHERE id = ?", (workspace_id,))
                row = cursor.fetchone()
                return Workspace.from_dict(dict(row)) if row else None
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to fetch workspace {workspace_id}: {e}")

    def update_workspace(self, workspace: Workspace) -> Workspace:
        """
        Update an existing workspace's metadata.
        
        Args:
            workspace: The workspace model with updated values
            
        Returns:
            Workspace: The updated workspace model
            
        Raises:
            DatabaseError: If update fails
        """
        try:
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
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to update workspace {workspace.id}: {e}")

    def delete_workspace(self, workspace_id: str) -> None:
        """
        Delete a workspace and all its associated metadata (cascades manually).
        
        Args:
            workspace_id: ID of the workspace to delete
            
        Raises:
            DatabaseError: If deletion fails
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM chunks WHERE workspace_id = ?", (workspace_id,))
                cursor.execute("DELETE FROM files WHERE workspace_id = ?", (workspace_id,))
                cursor.execute("DELETE FROM workspaces WHERE id = ?", (workspace_id,))
                conn.commit()
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to delete workspace {workspace_id}: {e}")

    def set_active_workspace(self, workspace_id: str) -> None:
        """
        Set a specific workspace as active and mark all others as inactive.
        
        Args:
            workspace_id: ID of the workspace to activate
            
        Raises:
            DatabaseError: If update fails
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE workspaces SET is_active = 0")
                cursor.execute("UPDATE workspaces SET is_active = 1 WHERE id = ?", (workspace_id,))
                conn.commit()
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to set active workspace {workspace_id}: {e}")

    # ============= File Methods =============

    def create_file(self, file_meta: FileMetadata) -> FileMetadata:
        """
        Persist metadata for a newly uploaded file.
        
        Args:
            file_meta: Metadata model for the file
            
        Returns:
            FileMetadata: The persisted metadata model
            
        Raises:
            DatabaseError: If creation fails
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO files (id, workspace_id, filename, original_name, file_type, size, status, 
                                     chunk_count, content_hash, uploaded_at, processed_at, error_message, tags)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (file_meta.id, file_meta.workspace_id, file_meta.filename, file_meta.original_name,
                      file_meta.file_type, file_meta.size, file_meta.status, file_meta.chunk_count,
                      file_meta.content_hash, file_meta.uploaded_at.isoformat(), 
                      file_meta.processed_at.isoformat() if file_meta.processed_at else None,
                      file_meta.error_message, json.dumps(file_meta.tags)))
                
                # Auto-increment workspace file count
                cursor.execute("""
                    UPDATE workspaces 
                    SET file_count = file_count + 1 
                    WHERE id = ?
                """, (file_meta.workspace_id,))
                
                conn.commit()
            return file_meta
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to create file record: {e}")

    def get_files(self, workspace_id: str) -> List[FileMetadata]:
        """
        Fetch all files associated with a workspace.
        
        Args:
            workspace_id: ID of the workspace
            
        Returns:
            List[FileMetadata]: List of file metadata models
            
        Raises:
            DatabaseError: If query fails
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM files WHERE workspace_id = ? ORDER BY uploaded_at DESC", (workspace_id,))
                rows = cursor.fetchall()
                return [FileMetadata.from_dict(dict(row)) for row in rows]
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to fetch files for workspace {workspace_id}: {e}")

    def update_file(self, file_meta: FileMetadata) -> FileMetadata:
        """
        Update file processing status and metadata.
        
        Args:
            file_meta: File model with updated values
            
        Returns:
            FileMetadata: The updated model
            
        Raises:
            DatabaseError: If update fails
        """
        try:
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
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to update file {file_meta.id}: {e}")

    def delete_file(self, file_id: str) -> None:
        """
        Remove a file record and decrement the parent workspace's file count.
        
        Args:
            file_id: ID of the file to delete
            
        Raises:
            DatabaseError: If deletion fails
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Get workspace_id for consistency
                cursor.execute("SELECT workspace_id FROM files WHERE id = ?", (file_id,))
                row = cursor.fetchone()
                
                cursor.execute("DELETE FROM chunks WHERE file_id = ?", (file_id,))
                cursor.execute("DELETE FROM files WHERE id = ?", (file_id,))
                
                if row:
                    workspace_id = row['workspace_id']
                    cursor.execute("""
                        UPDATE workspaces 
                        SET file_count = MAX(0, file_count - 1) 
                        WHERE id = ?
                    """, (workspace_id,))
                    
                conn.commit()
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to delete file {file_id}: {e}")

    # ============= Message Methods =============

    def add_message(self, message: Message) -> Message:
        """
        Save a chat message to the history.
        
        Args:
            message: Message model to persist
            
        Returns:
            Message: The persisted message model
            
        Raises:
            DatabaseError: If insertion fails
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO messages (id, role, content, timestamp, workspace_id, sources, is_summarized)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (message.id, message.role, message.content, message.timestamp.isoformat(),
                      message.workspace_id, json.dumps(message.sources), 1 if message.is_summarized else 0))
                conn.commit()
            return message
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to add message: {e}")

    def get_messages(self, workspace_id: Optional[str] = None, limit: int = 100) -> List[Message]:
        """
        Fetch chat history, optionally filtered by workspace.
        
        Args:
            workspace_id: Optional workspace ID filter
            limit: Maximum number of messages to return
            
        Returns:
            List[Message]: List of message models
            
        Raises:
            DatabaseError: If query fails
        """
        try:
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
                # Return in chronological order
                return [Message.from_dict(dict(row)) for row in reversed(rows)]
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to fetch messages: {e}")

    def clear_messages(self, workspace_id: Optional[str] = None) -> None:
        """
        Delete chat history.
        
        Args:
            workspace_id: Optional workspace ID filter
            
        Raises:
            DatabaseError: If deletion fails
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                if workspace_id:
                    cursor.execute("DELETE FROM messages WHERE workspace_id = ?", (workspace_id,))
                else:
                    cursor.execute("DELETE FROM messages")
                conn.commit()
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to clear messages: {e}")

    # ============= Q&A Methods =============

    def create_qa_pair(self, qa: QAPair) -> QAPair:
        """
        Persist a validated Q&A pair.
        
        Args:
            qa: Q&A model to persist
            
        Returns:
            QAPair: The persisted model
            
        Raises:
            DatabaseError: If creation fails
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO qa_pairs (id, workspace_id, file_ids, question, answer, created_at, likes, dislikes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (qa.id, qa.workspace_id, json.dumps(qa.file_ids), qa.question, qa.answer,
                      qa.created_at.isoformat(), qa.likes, qa.dislikes))
                conn.commit()
            return qa
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to create Q&A pair: {e}")

    def get_qa_pairs(self, workspace_id: Optional[str] = None) -> List[QAPair]:
        """
        Retrieve Q&A pairs.
        
        Args:
            workspace_id: Optional filter for workspace
            
        Returns:
            List[QAPair]: List of Q&A models
            
        Raises:
            DatabaseError: If query fails
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                if workspace_id:
                    cursor.execute("SELECT * FROM qa_pairs WHERE workspace_id = ? ORDER BY created_at DESC", (workspace_id,))
                else:
                    cursor.execute("SELECT * FROM qa_pairs ORDER BY created_at DESC")
                rows = cursor.fetchall()
                return [QAPair.from_dict(dict(row)) for row in rows]
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to fetch Q&A pairs: {e}")

    def update_qa_votes(self, qa_id: str, likes: int, dislikes: int) -> None:
        """
        Update the vote counts for a Q&A pair.
        
        Args:
            qa_id: Unique identifier for the pair
            likes: New like count
            dislikes: New dislike count
            
        Raises:
            DatabaseError: If update fails
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE qa_pairs SET likes = ?, dislikes = ? WHERE id = ?", (likes, dislikes, qa_id))
                conn.commit()
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to update votes for {qa_id}: {e}")

    # ============= Preferences Methods =============

    def get_preferences(self) -> UserPreferences:
        """
        Retrieve global user preferences.
        
        Returns:
            UserPreferences: The current preferences or default values if none exist
            
        Raises:
            DatabaseError: If query fails
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM preferences WHERE id = 1")
                row = cursor.fetchone()
                if row:
                    return UserPreferences.from_dict(dict(row))
                return UserPreferences()
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to fetch preferences: {e}")

    def save_preferences(self, prefs: UserPreferences) -> None:
        """
        Save or update global user preferences.
        
        Args:
            prefs: Preferences model to save
            
        Raises:
            DatabaseError: If save fails
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO preferences (id, weights, config, updated_at)
                    VALUES (1, ?, ?, ?)
                """, (json.dumps(prefs.weights), json.dumps(prefs.config), prefs.updated_at.isoformat()))
                conn.commit()
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to save preferences: {e}")

    # ============= Job Methods =============

    def create_job(self, job: Job) -> Job:
        """
        Register a new background job.
        
        Args:
            job: Job model to persist
            
        Returns:
            Job: The persisted job model
            
        Raises:
            DatabaseError: If creation fails
        """
        try:
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
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to create job {job.id}: {e}")

    def update_job(self, job: Job) -> Job:
        """
        Update an existing job's status and progress.
        
        Args:
            job: Job model with updated values
            
        Returns:
            Job: The updated model
            
        Raises:
            DatabaseError: If update fails
        """
        try:
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
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to update job {job.id}: {e}")

    def get_jobs(self, workspace_id: Optional[str] = None) -> List[Job]:
        """
        Fetch active jobs (pending or running).
        
        Args:
            workspace_id: Optional workspace ID filter
            
        Returns:
            List[Job]: List of active job models
            
        Raises:
            DatabaseError: If query fails
        """
        try:
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
                return [Job.from_dict(dict(row)) for row in rows]
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to fetch jobs: {e}")

    def reset_system(self) -> None:
        """
        Permanently clear all application data tables.
        
        Raises:
            DatabaseError: If reset fails
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                tables = ["chunks", "files", "messages", "qa_pairs", "jobs", "workspaces"]
                for table in tables:
                    cursor.execute(f"DELETE FROM {table}")
                conn.commit()
                logger.warning("System database successfully reset")
        except sqlite3.Error as e:
            logger.error(f"System reset failed: {e}")
            raise DatabaseError(f"Failed to reset system: {e}")
