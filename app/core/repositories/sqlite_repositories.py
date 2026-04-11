"""SQLite implementation of repositories."""

import sqlite3
from datetime import datetime

from app.core.exceptions import DatabaseQueryError
from app.core.logger import get_logger
from app.core.models import (
    FileMetadata,
    Message,
    Workspace,
)
from app.core.repositories.interfaces import (
    FileRepository,
    MessageRepository,
    WorkspaceRepository,
)

logger = get_logger(__name__)


class SQLiteConnection:
    """Context manager for SQLite connections."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._conn: sqlite3.Connection | None = None

    def __enter__(self) -> sqlite3.Connection:
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
        return self._conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._conn:
            if exc_type is None:
                self._conn.commit()
            else:
                self._conn.rollback()
            self._conn.close()


class SQLiteWorkspaceRepository(WorkspaceRepository):
    """SQLite implementation of WorkspaceRepository."""

    def __init__(self, db_path: str):
        self.db_path = db_path

    def _execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        with SQLiteConnection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor

    def create(self, workspace: Workspace) -> Workspace:
        try:
            with SQLiteConnection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO workspaces (id, name, description, created_at, last_modified, file_count, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        workspace.id,
                        workspace.name,
                        workspace.description,
                        workspace.created_at.isoformat(),
                        workspace.last_modified.isoformat(),
                        workspace.file_count,
                        1 if workspace.is_active else 0,
                    ),
                )
                logger.debug(f"Created workspace: {workspace.id}")
                return workspace
        except sqlite3.Error as e:
            raise DatabaseQueryError(f"Failed to create workspace: {e}")

    def get_by_id(self, workspace_id: str) -> Workspace | None:
        try:
            with SQLiteConnection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM workspaces WHERE id = ?", (workspace_id,))
                row = cursor.fetchone()
                if row:
                    return self._row_to_workspace(row)
                return None
        except sqlite3.Error as e:
            raise DatabaseQueryError(f"Failed to get workspace: {e}")

    def get_all(self) -> list[Workspace]:
        try:
            with SQLiteConnection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM workspaces ORDER BY last_modified DESC")
                return [self._row_to_workspace(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            raise DatabaseQueryError(f"Failed to get workspaces: {e}")

    def get_active(self) -> Workspace | None:
        try:
            with SQLiteConnection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM workspaces WHERE is_active = 1 LIMIT 1")
                row = cursor.fetchone()
                if row:
                    return self._row_to_workspace(row)
                return None
        except sqlite3.Error as e:
            raise DatabaseQueryError(f"Failed to get active workspace: {e}")

    def update(self, workspace: Workspace) -> Workspace:
        try:
            with SQLiteConnection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE workspaces
                    SET name = ?, description = ?, last_modified = ?, file_count = ?, is_active = ?
                    WHERE id = ?
                """,
                    (
                        workspace.name,
                        workspace.description,
                        datetime.now().isoformat(),
                        workspace.file_count,
                        1 if workspace.is_active else 0,
                        workspace.id,
                    ),
                )
                logger.debug(f"Updated workspace: {workspace.id}")
                return workspace
        except sqlite3.Error as e:
            raise DatabaseQueryError(f"Failed to update workspace: {e}")

    def delete(self, workspace_id: str) -> bool:
        try:
            with SQLiteConnection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM workspaces WHERE id = ?", (workspace_id,))
                logger.debug(f"Deleted workspace: {workspace_id}")
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            raise DatabaseQueryError(f"Failed to delete workspace: {e}")

    def set_active(self, workspace_id: str) -> bool:
        try:
            with SQLiteConnection(self.db_path) as conn:
                cursor = conn.cursor()
                # Deactivate all
                cursor.execute("UPDATE workspaces SET is_active = 0")
                # Activate target
                cursor.execute(
                    "UPDATE workspaces SET is_active = 1 WHERE id = ?", (workspace_id,)
                )
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            raise DatabaseQueryError(f"Failed to set active workspace: {e}")

    @staticmethod
    def _row_to_workspace(row: sqlite3.Row) -> Workspace:
        return Workspace(
            id=row["id"],
            name=row["name"],
            description=row["description"] or "",
            created_at=datetime.fromisoformat(row["created_at"]),
            last_modified=datetime.fromisoformat(row["last_modified"]),
            file_count=row["file_count"] or 0,
            is_active=bool(row["is_active"]),
        )


class SQLiteFileRepository(FileRepository):
    """SQLite implementation of FileRepository."""

    def __init__(self, db_path: str):
        self.db_path = db_path

    def create(self, file: FileMetadata) -> FileMetadata:
        try:
            with SQLiteConnection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO files (id, workspace_id, filename, original_name, file_type, size,
                                     status, chunk_count, content_hash, uploaded_at, processed_at,
                                     error_message, tags)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        file.id,
                        file.workspace_id,
                        file.filename,
                        file.original_name,
                        file.file_type,
                        file.size,
                        file.status,
                        file.chunk_count,
                        file.content_hash,
                        file.uploaded_at.isoformat(),
                        file.processed_at.isoformat() if file.processed_at else None,
                        file.error_message,
                        ",".join(file.tags) if file.tags else "",
                    ),
                )
                logger.debug(f"Created file record: {file.id}")
                return file
        except sqlite3.Error as e:
            raise DatabaseQueryError(f"Failed to create file: {e}")

    def get_by_id(self, file_id: str) -> FileMetadata | None:
        try:
            with SQLiteConnection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM files WHERE id = ?", (file_id,))
                row = cursor.fetchone()
                if row:
                    return self._row_to_file(row)
                return None
        except sqlite3.Error as e:
            raise DatabaseQueryError(f"Failed to get file: {e}")

    def get_by_workspace(self, workspace_id: str) -> list[FileMetadata]:
        try:
            with SQLiteConnection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM files WHERE workspace_id = ? ORDER BY uploaded_at DESC",
                    (workspace_id,),
                )
                return [self._row_to_file(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            raise DatabaseQueryError(f"Failed to get files: {e}")

    def get_by_status(self, workspace_id: str, status: str) -> list[FileMetadata]:
        try:
            with SQLiteConnection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM files WHERE workspace_id = ? AND status = ?",
                    (workspace_id, status),
                )
                return [self._row_to_file(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            raise DatabaseQueryError(f"Failed to get files by status: {e}")

    def update(self, file: FileMetadata) -> FileMetadata:
        try:
            with SQLiteConnection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE files
                    SET filename = ?, file_type = ?, size = ?, status = ?, chunk_count = ?,
                        processed_at = ?, error_message = ?, tags = ?
                    WHERE id = ?
                """,
                    (
                        file.filename,
                        file.file_type,
                        file.size,
                        file.status,
                        file.chunk_count,
                        file.processed_at.isoformat() if file.processed_at else None,
                        file.error_message,
                        ",".join(file.tags) if file.tags else "",
                        file.id,
                    ),
                )
                logger.debug(f"Updated file: {file.id}")
                return file
        except sqlite3.Error as e:
            raise DatabaseQueryError(f"Failed to update file: {e}")

    def delete(self, file_id: str) -> bool:
        try:
            with SQLiteConnection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM files WHERE id = ?", (file_id,))
                logger.debug(f"Deleted file: {file_id}")
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            raise DatabaseQueryError(f"Failed to delete file: {e}")

    def count_by_workspace(self, workspace_id: str) -> int:
        try:
            with SQLiteConnection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT COUNT(*) FROM files WHERE workspace_id = ?", (workspace_id,)
                )
                return cursor.fetchone()[0]
        except sqlite3.Error as e:
            raise DatabaseQueryError(f"Failed to count files: {e}")

    @staticmethod
    def _row_to_file(row: sqlite3.Row) -> FileMetadata:
        tags = row["tags"]
        return FileMetadata(
            id=row["id"],
            workspace_id=row["workspace_id"],
            filename=row["filename"],
            original_name=row["original_name"],
            file_type=row["file_type"] or "",
            size=row["size"] or 0,
            status=row["status"] or "pending",
            chunk_count=row["chunk_count"] or 0,
            content_hash=row["content_hash"],
            uploaded_at=datetime.fromisoformat(row["uploaded_at"]),
            processed_at=(
                datetime.fromisoformat(row["processed_at"])
                if row["processed_at"]
                else None
            ),
            error_message=row["error_message"],
            tags=tags.split(",") if tags else [],
        )


class SQLiteMessageRepository(MessageRepository):
    """SQLite implementation of MessageRepository."""

    def __init__(self, db_path: str):
        self.db_path = db_path

    def create(self, message: Message) -> Message:
        try:
            with SQLiteConnection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO messages (id, role, content, timestamp, workspace_id, sources, is_summarized)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        message.id,
                        message.role,
                        message.content,
                        message.timestamp.isoformat(),
                        message.workspace_id,
                        ",".join(message.sources) if message.sources else "",
                        1 if message.is_summarized else 0,
                    ),
                )
                return message
        except sqlite3.Error as e:
            raise DatabaseQueryError(f"Failed to create message: {e}")

    def get_by_id(self, message_id: str) -> Message | None:
        try:
            with SQLiteConnection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM messages WHERE id = ?", (message_id,))
                row = cursor.fetchone()
                if row:
                    return self._row_to_message(row)
                return None
        except sqlite3.Error as e:
            raise DatabaseQueryError(f"Failed to get message: {e}")

    def get_by_workspace(
        self, workspace_id: str, limit: int = 100, offset: int = 0
    ) -> list[Message]:
        try:
            with SQLiteConnection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT * FROM messages
                    WHERE workspace_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ? OFFSET ?
                """,
                    (workspace_id, limit, offset),
                )
                return [self._row_to_message(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            raise DatabaseQueryError(f"Failed to get messages: {e}")

    def get_recent(self, workspace_id: str, limit: int = 50) -> list[Message]:
        messages = self.get_by_workspace(workspace_id, limit)
        return list(reversed(messages))

    def update(self, message: Message) -> Message:
        try:
            with SQLiteConnection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE messages
                    SET content = ?, sources = ?, is_summarized = ?
                    WHERE id = ?
                """,
                    (
                        message.content,
                        ",".join(message.sources) if message.sources else "",
                        1 if message.is_summarized else 0,
                        message.id,
                    ),
                )
                return message
        except sqlite3.Error as e:
            raise DatabaseQueryError(f"Failed to update message: {e}")

    def delete(self, message_id: str) -> bool:
        try:
            with SQLiteConnection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM messages WHERE id = ?", (message_id,))
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            raise DatabaseQueryError(f"Failed to delete message: {e}")

    def clear_by_workspace(self, workspace_id: str) -> bool:
        try:
            with SQLiteConnection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM messages WHERE workspace_id = ?", (workspace_id,)
                )
                return True
        except sqlite3.Error as e:
            raise DatabaseQueryError(f"Failed to clear messages: {e}")

    def count_by_workspace(self, workspace_id: str) -> int:
        try:
            with SQLiteConnection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT COUNT(*) FROM messages WHERE workspace_id = ?",
                    (workspace_id,),
                )
                return cursor.fetchone()[0]
        except sqlite3.Error as e:
            raise DatabaseQueryError(f"Failed to count messages: {e}")

    @staticmethod
    def _row_to_message(row: sqlite3.Row) -> Message:
        sources = row["sources"]
        return Message(
            id=row["id"],
            role=row["role"],
            content=row["content"],
            timestamp=datetime.fromisoformat(row["timestamp"]),
            workspace_id=row["workspace_id"],
            sources=sources.split(",") if sources else [],
            is_summarized=bool(row["is_summarized"]),
        )


# Continue with more repository implementations as needed...
