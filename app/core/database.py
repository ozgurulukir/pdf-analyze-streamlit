"""Database manager for SQLite storage using Repository Pattern."""

import sqlite3
from pathlib import Path

from app.core.config import AppConfig
from app.core.exceptions import DatabaseError
from app.core.logger import logger
from app.core.repositories.sqlite_repositories import (
    SQLiteChatSessionRepository,
    SQLiteChunkRepository,
    SQLiteFileRepository,
    SQLiteJobRepository,
    SQLiteMessageRepository,
    SQLitePreferencesRepository,
    SQLiteQARepository,
    SQLiteWorkspaceRepository,
)


class DatabaseManager:
    """
    SQLite database manager acting as a Unit of Work container.

    Provides access to specialized repositories for workspaces, files,
    messages, chunks, Q&A pairs, preferences, and background jobs.
    """

    def __init__(self, db_path: str | None = None):
        """
        Initialize the database manager and its repositories.

        Args:
            db_path: Path to the SQLite database file
        """
        if db_path is None:
            try:
                from app.core.container import get_config

                db_path = get_config().DB_PATH
            except Exception:
                # Fallback during container initialization
                db_path = AppConfig().DB_PATH
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        # Initialize specialized repositories
        self.workspaces = SQLiteWorkspaceRepository(self.db_path)
        self.files = SQLiteFileRepository(self.db_path)
        self.messages = SQLiteMessageRepository(self.db_path)
        self.chunks = SQLiteChunkRepository(self.db_path)
        self.qa = SQLiteQARepository(self.db_path)
        self.preferences = SQLitePreferencesRepository(self.db_path)
        self.jobs = SQLiteJobRepository(self.db_path)
        self.chat_sessions = SQLiteChatSessionRepository(self.db_path)

        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """
        Create and return a database connection.

        Returns:
            sqlite3.Connection: A connection object with row_factory set to sqlite3.Row
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
                        workspace_id TEXT,
                        filename TEXT NOT NULL,
                        original_name TEXT NOT NULL,
                        file_type TEXT,
                        size INTEGER,
                        status TEXT,
                        chunk_count INTEGER DEFAULT 0,
                        content_hash TEXT,
                        uploaded_at TEXT NOT NULL,
                        processed_at TEXT,
                        error_message TEXT,
                        tags TEXT,
                        FOREIGN KEY (workspace_id) REFERENCES workspaces (id) ON DELETE CASCADE
                    )
                """)

                # Chunks table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS chunks (
                        id TEXT PRIMARY KEY,
                        file_id TEXT,
                        workspace_id TEXT,
                        content TEXT NOT NULL,
                        page_number INTEGER,
                        chunk_index INTEGER,
                        token_count INTEGER,
                        metadata TEXT,
                        chroma_id TEXT,
                        created_at TEXT,
                        FOREIGN KEY (file_id) REFERENCES files (id) ON DELETE CASCADE,
                        FOREIGN KEY (workspace_id) REFERENCES workspaces (id) ON DELETE CASCADE
                    )
                """)

                # Chat Sessions table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS chat_sessions (
                        id TEXT PRIMARY KEY,
                        workspace_id TEXT,
                        title TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        last_message_at TEXT NOT NULL,
                        FOREIGN KEY (workspace_id) REFERENCES workspaces (id) ON DELETE CASCADE
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
                        session_id TEXT,
                        sources TEXT,
                        is_summarized INTEGER DEFAULT 0,
                        FOREIGN KEY (workspace_id) REFERENCES workspaces (id) ON DELETE CASCADE,
                        FOREIGN KEY (session_id) REFERENCES chat_sessions (id) ON DELETE CASCADE
                    )
                """)

                # Migration: Add session_id to messages if it doesn't exist
                try:
                    cursor.execute("ALTER TABLE messages ADD COLUMN session_id TEXT")
                except sqlite3.OperationalError:
                    pass # Already exists

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
                        dislikes INTEGER DEFAULT 0,
                        tags TEXT,
                        FOREIGN KEY (workspace_id) REFERENCES workspaces (id) ON DELETE CASCADE
                    )
                """)

                # Migration: Add tags to qa_pairs if it doesn't exist
                try:
                    cursor.execute("ALTER TABLE qa_pairs ADD COLUMN tags TEXT")
                except sqlite3.OperationalError:
                    pass # Already exists

                # Preferences table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS preferences (
                        id INTEGER PRIMARY KEY,
                        weights TEXT,
                        config TEXT,
                        updated_at TEXT NOT NULL
                    )
                """)

                # Background jobs table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS jobs (
                        id TEXT PRIMARY KEY,
                        job_type TEXT NOT NULL,
                        workspace_id TEXT,
                        file_ids TEXT,
                        status TEXT NOT NULL,
                        progress REAL DEFAULT 0.0,
                        total INTEGER DEFAULT 0,
                        current INTEGER DEFAULT 0,
                        error_message TEXT,
                        created_at TEXT NOT NULL,
                        started_at TEXT,
                        completed_at TEXT,
                        FOREIGN KEY (workspace_id) REFERENCES workspaces (id) ON DELETE CASCADE
                    )
                """)

                conn.commit()
                logger.debug("Database initialized successfully")
        except sqlite3.Error as e:
            logger.error(f"Database initialization failed: {e}")
            raise DatabaseError(f"Failed to initialize database: {e}")

    def reset_system(self) -> None:
        """
        Permanently clear all application data tables.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                tables = [
                    "chunks",
                    "files",
                    "messages",
                    "qa_pairs",
                    "jobs",
                    "chat_sessions",
                    "workspaces",
                    "preferences",
                ]
                for table in tables:
                    cursor.execute(f"DELETE FROM {table}")
                conn.commit()
                logger.warning("System database successfully reset")
        except sqlite3.Error as e:
            logger.error(f"System reset failed: {e}")
            raise DatabaseError(f"Failed to reset system: {e}")
