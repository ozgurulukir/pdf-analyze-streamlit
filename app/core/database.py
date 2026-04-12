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

    def __init__(self, db_path: str):
        """
        Initialize the database manager and its repositories.

        Args:
            db_path: Path to the SQLite database file
        """
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
        Now managed exclusively via Alembic migrations.
        """
        from pathlib import Path
        try:
            import alembic.command
            import alembic.config

            project_root = Path(__file__).resolve().parent.parent.parent
            alembic_cfg_path = project_root / "alembic.ini"

            if alembic_cfg_path.exists():
                alembic_cfg = alembic.config.Config(str(alembic_cfg_path))
                # Explicitly set the path to migrations folder
                alembic_cfg.set_main_option("script_location", str(project_root / "db_migrations"))
                alembic.command.upgrade(alembic_cfg, "head")
                logger.debug("Database migrations applied successfully via Alembic")
            else:
                logger.warning(f"Alembic configuration not found at {alembic_cfg_path}")
        except Exception as e:
            logger.error(f"Database migration failed: {e}")
            raise DatabaseError(f"Failed to apply database migrations: {e}")

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
