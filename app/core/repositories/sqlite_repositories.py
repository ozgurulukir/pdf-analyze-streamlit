"""SQLite implementation of repositories."""

import json
import sqlite3
from datetime import datetime, timedelta
from typing import Any

from app.core.exceptions import DatabaseQueryError
from app.core.logger import logger
from app.core.models import (
    ChatSession,
    ChunkMetadata,
    FileMetadata,
    Job,
    Message,
    QAPair,
    UserPreferences,
    Workspace,
)
from app.core.repositories.interfaces import (
    ChatSessionRepository,
    ChunkRepository,
    FileRepository,
    JobRepository,
    MessageRepository,
    PreferencesRepository,
    QARepository,
    WorkspaceRepository,
)

# Ensure logger is initialized for this module
_log = logger


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
            processed_at=datetime.fromisoformat(row["processed_at"])
            if row["processed_at"]
            else None,
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
                    INSERT INTO messages (id, role, content, timestamp, workspace_id, session_id, sources, is_summarized)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        message.id,
                        message.role,
                        message.content,
                        message.timestamp.isoformat(),
                        message.workspace_id,
                        message.session_id,
                        json.dumps(message.sources) if message.sources else None,
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
        self, workspace_id: str, limit: int = 100, offset: int = 0, session_id: str | None = None
    ) -> list[Message]:
        try:
            with SQLiteConnection(self.db_path) as conn:
                cursor = conn.cursor()
                if session_id:
                    cursor.execute(
                        """
                        SELECT * FROM messages
                        WHERE workspace_id = ? AND session_id = ?
                        ORDER BY timestamp DESC
                        LIMIT ? OFFSET ?
                    """,
                        (workspace_id, session_id, limit, offset),
                    )
                else:
                    cursor.execute(
                        """
                        SELECT * FROM messages
                        WHERE workspace_id = ? AND session_id IS NULL
                        ORDER BY timestamp DESC
                        LIMIT ? OFFSET ?
                    """,
                        (workspace_id, limit, offset),
                    )
                return [self._row_to_message(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            raise DatabaseQueryError(f"Failed to get messages: {e}")

    def get_recent(self, workspace_id: str, limit: int = 50, session_id: str | None = None) -> list[Message]:
        messages = self.get_by_workspace(workspace_id, limit, session_id=session_id)
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
                        json.dumps(message.sources) if message.sources else None,
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
        return Message(
            id=row["id"],
            role=row["role"],
            content=row["content"],
            timestamp=datetime.fromisoformat(row["timestamp"]),
            workspace_id=row["workspace_id"],
            session_id=row["session_id"] if "session_id" in row.keys() else None,
            sources=json.loads(row["sources"]) if row["sources"] else [],
            is_summarized=bool(row["is_summarized"]),
        )


class SQLiteChatSessionRepository(ChatSessionRepository):
    """SQLite implementation of ChatSessionRepository."""

    def __init__(self, db_path: str):
        self.db_path = db_path

    def create(self, session: ChatSession) -> ChatSession:
        try:
            with SQLiteConnection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO chat_sessions (id, workspace_id, title, created_at, last_message_at)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (
                        session.id,
                        session.workspace_id,
                        session.title,
                        session.created_at.isoformat(),
                        session.last_message_at.isoformat(),
                    ),
                )
                return session
        except sqlite3.Error as e:
            raise DatabaseQueryError(f"Failed to create chat session: {e}")

    def get_by_id(self, session_id: str) -> ChatSession | None:
        try:
            with SQLiteConnection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM chat_sessions WHERE id = ?", (session_id,))
                row = cursor.fetchone()
                if row:
                    return self._row_to_session(row)
                return None
        except sqlite3.Error as e:
            raise DatabaseQueryError(f"Failed to get chat session: {e}")

    def get_by_workspace(self, workspace_id: str) -> list[ChatSession]:
        try:
            with SQLiteConnection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM chat_sessions WHERE workspace_id = ? ORDER BY last_message_at DESC",
                    (workspace_id,),
                )
                return [self._row_to_session(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            raise DatabaseQueryError(f"Failed to get chat sessions: {e}")

    def update(self, session: ChatSession) -> ChatSession:
        try:
            with SQLiteConnection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE chat_sessions
                    SET title = ?, last_message_at = ?
                    WHERE id = ?
                """,
                    (session.title, session.last_message_at.isoformat(), session.id),
                )
                return session
        except sqlite3.Error as e:
            raise DatabaseQueryError(f"Failed to update chat session: {e}")

    def delete(self, session_id: str) -> bool:
        try:
            with SQLiteConnection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM chat_sessions WHERE id = ?", (session_id,))
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            raise DatabaseQueryError(f"Failed to delete chat session: {e}")

    @staticmethod
    def _row_to_session(row: sqlite3.Row) -> ChatSession:
        from app.core.models import ChatSession
        return ChatSession(
            id=row["id"],
            workspace_id=row["workspace_id"],
            title=row["title"],
            created_at=datetime.fromisoformat(row["created_at"]),
            last_message_at=datetime.fromisoformat(row["last_message_at"]),
        )



class SQLiteChunkRepository(ChunkRepository):
    """SQLite implementation of ChunkRepository."""

    def __init__(self, db_path: str):
        self.db_path = db_path

    def create(self, chunk: ChunkMetadata) -> ChunkMetadata:
        try:
            with SQLiteConnection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO chunks (id, file_id, workspace_id, content, page_number,
                                      chunk_index, token_count, metadata, chroma_id, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        chunk.id,
                        chunk.file_id,
                        chunk.workspace_id,
                        chunk.content,
                        chunk.page_number,
                        chunk.chunk_index,
                        chunk.token_count,
                        json.dumps(chunk.metadata),
                        chunk.chroma_id,
                        chunk.created_at.isoformat(),
                    ),
                )
                return chunk
        except sqlite3.Error as e:
            raise DatabaseQueryError(f"Failed to create chunk: {e}")

    def get_by_id(self, chunk_id: str) -> ChunkMetadata | None:
        try:
            with SQLiteConnection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM chunks WHERE id = ?", (chunk_id,))
                row = cursor.fetchone()
                if row:
                    return self._row_to_chunk(row)
                return None
        except sqlite3.Error as e:
            raise DatabaseQueryError(f"Failed to get chunk: {e}")

    def get_by_file(self, file_id: str) -> list[ChunkMetadata]:
        try:
            with SQLiteConnection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM chunks WHERE file_id = ? ORDER BY chunk_index ASC",
                    (file_id,),
                )
                return [self._row_to_chunk(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            raise DatabaseQueryError(f"Failed to get chunks for file: {e}")

    def get_by_workspace(self, workspace_id: str) -> list[ChunkMetadata]:
        try:
            with SQLiteConnection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM chunks WHERE workspace_id = ?", (workspace_id,)
                )
                return [self._row_to_chunk(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            raise DatabaseQueryError(f"Failed to get chunks for workspace: {e}")

    def delete_by_file(self, file_id: str) -> bool:
        try:
            with SQLiteConnection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM chunks WHERE file_id = ?", (file_id,))
                return True
        except sqlite3.Error as e:
            raise DatabaseQueryError(f"Failed to delete chunks for file: {e}")

    def delete_by_workspace(self, workspace_id: str) -> bool:
        try:
            with SQLiteConnection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM chunks WHERE workspace_id = ?", (workspace_id,))
                return True
        except sqlite3.Error as e:
            raise DatabaseQueryError(f"Failed to delete chunks for workspace: {e}")

    def count_by_workspace(self, workspace_id: str) -> int:
        try:
            with SQLiteConnection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT COUNT(*) FROM chunks WHERE workspace_id = ?", (workspace_id,)
                )
                return cursor.fetchone()[0]
        except sqlite3.Error as e:
            raise DatabaseQueryError(f"Failed to count chunks: {e}")

    @staticmethod
    def _row_to_chunk(row: sqlite3.Row) -> ChunkMetadata:
        return ChunkMetadata(
            id=row["id"],
            file_id=row["file_id"],
            workspace_id=row["workspace_id"],
            content=row["content"],
            page_number=row["page_number"],
            chunk_index=row["chunk_index"],
            token_count=row["token_count"],
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
            chroma_id=row["chroma_id"],
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else datetime.now(),
        )


class SQLiteQARepository(QARepository):
    """SQLite implementation of QARepository."""

    def __init__(self, db_path: str):
        self.db_path = db_path

    def create_from_params(self, workspace_id, file_ids, question, answer, tags=None) -> QAPair:
        """Create a QA pair from raw parameters."""
        from app.core.models import QAPair
        qa = QAPair(
            workspace_id=workspace_id,
            file_ids=file_ids,
            question=question,
            answer=answer,
            tags=tags or []
        )
        return self.create(qa)

    def create(self, qa: QAPair) -> QAPair:
        try:
            with SQLiteConnection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO qa_pairs (id, workspace_id, file_ids, question, answer, created_at, likes, dislikes, tags)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        qa.id,
                        qa.workspace_id,
                        json.dumps(qa.file_ids),
                        qa.question,
                        qa.answer,
                        qa.created_at.isoformat(),
                        qa.likes,
                        qa.dislikes,
                        json.dumps(qa.tags) if qa.tags else json.dumps([]),
                    ),
                )
                return qa
        except sqlite3.Error as e:
            raise DatabaseQueryError(f"Failed to create Q&A pair: {e}")

    def get_by_id(self, qa_id: str) -> QAPair | None:
        try:
            with SQLiteConnection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM qa_pairs WHERE id = ?", (qa_id,))
                row = cursor.fetchone()
                if row:
                    return self._row_to_qa(row)
                return None
        except sqlite3.Error as e:
            raise DatabaseQueryError(f"Failed to get Q&A pair: {e}")

    def get_by_workspace(self, workspace_id: str) -> list[QAPair]:
        try:
            with SQLiteConnection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM qa_pairs WHERE workspace_id = ? ORDER BY created_at DESC",
                    (workspace_id,),
                )
                return [self._row_to_qa(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            raise DatabaseQueryError(f"Failed to get Q&A pairs: {e}")

    def get_by_file(self, file_id: str) -> list[QAPair]:
        # This implementation requires JSON searching or a join table, simplified for now
        # SQLite doesn't have native JSON array search easily without json_each
        try:
            with SQLiteConnection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM qa_pairs WHERE file_ids LIKE ?", (f"%{file_id}%",)
                )
                return [self._row_to_qa(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            raise DatabaseQueryError(f"Failed to get Q&A pairs for file: {e}")

    def update(self, qa: QAPair) -> QAPair:
        try:
            with SQLiteConnection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE qa_pairs
                    SET question = ?, answer = ?, likes = ?, dislikes = ?, tags = ?
                    WHERE id = ?
                """,
                    (
                        qa.question,
                        qa.answer,
                        qa.likes,
                        qa.dislikes,
                        json.dumps(qa.tags) if qa.tags else json.dumps([]),
                        qa.id,
                    ),
                )
                return qa
        except sqlite3.Error as e:
            raise DatabaseQueryError(f"Failed to update Q&A pair: {e}")

    def update_votes(self, qa_id: str, likes: int, dislikes: int) -> bool:
        try:
            with SQLiteConnection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE qa_pairs SET likes = ?, dislikes = ? WHERE id = ?",
                    (likes, dislikes, qa_id),
                )
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            raise DatabaseQueryError(f"Failed to update votes: {e}")

    def delete(self, qa_id: str) -> bool:
        try:
            with SQLiteConnection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM qa_pairs WHERE id = ?", (qa_id,))
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            raise DatabaseQueryError(f"Failed to delete Q&A pair: {e}")

    @staticmethod
    def _row_to_qa(row: sqlite3.Row) -> QAPair:
        return QAPair(
            id=row["id"],
            workspace_id=row["workspace_id"],
            file_ids=json.loads(row["file_ids"]) if row["file_ids"] else [],
            question=row["question"],
            answer=row["answer"],
            created_at=datetime.fromisoformat(row["created_at"]),
            likes=row["likes"] or 0,
            dislikes=row["dislikes"] or 0,
            tags=json.loads(row["tags"]) if "tags" in row.keys() and row["tags"] else [],
        )


class SQLitePreferencesRepository(PreferencesRepository):
    """SQLite implementation of PreferencesRepository."""

    def __init__(self, db_path: str):
        self.db_path = db_path

    def get(self) -> UserPreferences:
        try:
            with SQLiteConnection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM preferences WHERE id = 1")
                row = cursor.fetchone()
                if row:
                    return UserPreferences(
                        weights=json.loads(row["weights"]) if row["weights"] else {},
                        config=json.loads(row["config"]) if row["config"] else {},
                        updated_at=datetime.fromisoformat(row["updated_at"]),
                    )
                return UserPreferences()
        except sqlite3.Error as e:
            raise DatabaseQueryError(f"Failed to get preferences: {e}")

    def save(self, preferences: UserPreferences) -> UserPreferences:
        try:
            with SQLiteConnection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO preferences (id, weights, config, updated_at)
                    VALUES (1, ?, ?, ?)
                """,
                    (
                        json.dumps(preferences.weights),
                        json.dumps(preferences.config),
                        preferences.updated_at.isoformat(),
                    ),
                )
                return preferences
        except sqlite3.Error as e:
            raise DatabaseQueryError(f"Failed to save preferences: {e}")

    def update_weights(self, weights: dict[str, float]) -> UserPreferences:
        prefs = self.get()
        prefs.weights.update(weights)
        prefs.updated_at = datetime.now()
        return self.save(prefs)

    def update_config(self, config: dict[str, Any]) -> UserPreferences:
        prefs = self.get()
        if prefs.config is None:
            prefs.config = {}
        prefs.config.update(config)
        prefs.updated_at = datetime.now()
        return self.save(prefs)


class SQLiteJobRepository(JobRepository):
    """SQLite implementation of JobRepository."""

    def __init__(self, db_path: str):
        self.db_path = db_path

    def create(self, job: Job) -> Job:
        try:
            with SQLiteConnection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO jobs (id, job_type, workspace_id, file_ids, status, progress, total, current,
                                    error_message, created_at, started_at, completed_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        job.id,
                        job.job_type,
                        job.workspace_id,
                        json.dumps(job.file_ids),
                        job.status,
                        job.progress,
                        job.total,
                        job.current,
                        job.error_message,
                        job.created_at.isoformat(),
                        job.started_at.isoformat() if job.started_at else None,
                        job.completed_at.isoformat() if job.completed_at else None,
                    ),
                )
                return job
        except sqlite3.Error as e:
            raise DatabaseQueryError(f"Failed to create job: {e}")

    def get_by_id(self, job_id: str) -> Job | None:
        try:
            with SQLiteConnection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
                row = cursor.fetchone()
                if row:
                    return self._row_to_job(row)
                return None
        except sqlite3.Error as e:
            raise DatabaseQueryError(f"Failed to get job: {e}")

    def get_by_workspace(self, workspace_id: str) -> list[Job]:
        try:
            with SQLiteConnection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM jobs WHERE workspace_id = ? ORDER BY created_at DESC",
                    (workspace_id,),
                )
                return [self._row_to_job(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            raise DatabaseQueryError(f"Failed to get jobs for workspace: {e}")

    def get_by_status(self, status: str) -> list[Job]:
        try:
            with SQLiteConnection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM jobs WHERE status = ? ORDER BY created_at DESC",
                    (status,),
                )
                return [self._row_to_job(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            raise DatabaseQueryError(f"Failed to get jobs by status: {e}")

    def get_pending(self, limit: int = 10) -> list[Job]:
        return self.get_by_status("pending")[:limit]

    def get_active(self) -> list[Job]:
        """Fetch all jobs with pending or running status, plus recently finished ones."""
        try:
            with SQLiteConnection(self.db_path) as conn:
                cursor = conn.cursor()
                # Include pending/running OR recently (last 60s) completed/failed
                cursor.execute(
                    """
                    SELECT * FROM jobs 
                    WHERE status IN ('pending', 'running') 
                    OR (status IN ('completed', 'failed') AND completed_at > ?)
                    ORDER BY created_at ASC
                """,
                    ((datetime.now() - timedelta(seconds=60)).isoformat(),),
                )
                return [self._row_to_job(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            raise DatabaseQueryError(f"Failed to get active jobs: {e}")

    def update(self, job: Job) -> Job:
        try:
            with SQLiteConnection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE jobs
                    SET status = ?, progress = ?, total = ?, current = ?, error_message = ?,
                        started_at = ?, completed_at = ?
                    WHERE id = ?
                """,
                    (
                        job.status,
                        job.progress,
                        job.total,
                        job.current,
                        job.error_message,
                        job.started_at.isoformat() if job.started_at else None,
                        job.completed_at.isoformat() if job.completed_at else None,
                        job.id,
                    ),
                )
                return job
        except sqlite3.Error as e:
            raise DatabaseQueryError(f"Failed to update job: {e}")

    def update_progress(self, job_id: str, progress: float, current: int) -> bool:
        try:
            with SQLiteConnection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE jobs SET progress = ?, current = ? WHERE id = ?",
                    (progress, current, job_id),
                )
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            raise DatabaseQueryError(f"Failed to update job progress: {e}")

    def delete(self, job_id: str) -> bool:
        try:
            with SQLiteConnection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            raise DatabaseQueryError(f"Failed to delete job: {e}")

    def delete_completed(self, older_than_days: int = 7) -> int:
        try:
            with SQLiteConnection(self.db_path) as conn:
                cursor = conn.cursor()
                # Simplified date logic using SQLite's datetime support
                cursor.execute(
                    """
                    DELETE FROM jobs
                    WHERE status IN ('completed', 'failed')
                    AND datetime(completed_at) < datetime('now', ?)
                """,
                    (f"-{older_than_days} days",),
                )
                return cursor.rowcount
        except sqlite3.Error as e:
            raise DatabaseQueryError(f"Failed to delete old jobs: {e}")

    @staticmethod
    def _row_to_job(row: sqlite3.Row) -> Job:
        return Job(
            id=row["id"],
            job_type=row["job_type"],
            workspace_id=row["workspace_id"],
            file_ids=json.loads(row["file_ids"]) if row["file_ids"] else [],
            status=row["status"],
            progress=row["progress"] or 0.0,
            total=row["total"] or 0,
            current=row["current"] or 0,
            error_message=row["error_message"],
            created_at=datetime.fromisoformat(row["created_at"]),
            started_at=datetime.fromisoformat(row["started_at"])
            if row["started_at"]
            else None,
            completed_at=datetime.fromisoformat(row["completed_at"])
            if row["completed_at"]
            else None,
        )

