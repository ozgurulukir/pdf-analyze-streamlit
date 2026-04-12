"""init

Revision ID: 5e3c5f157425
Revises: 
Create Date: 2026-04-12 20:26:33.115138

"""
from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '5e3c5f157425'
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute('''
        CREATE TABLE IF NOT EXISTS workspaces (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            created_at TEXT NOT NULL,
            last_modified TEXT NOT NULL,
            file_count INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 0
        )
    ''')
    op.execute('''
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
    ''')
    op.execute('''
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
    ''')
    op.execute('''
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id TEXT PRIMARY KEY,
            workspace_id TEXT,
            title TEXT NOT NULL,
            created_at TEXT NOT NULL,
            last_message_at TEXT NOT NULL,
            FOREIGN KEY (workspace_id) REFERENCES workspaces (id) ON DELETE CASCADE
        )
    ''')
    op.execute('''
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
    ''')
    op.execute('''
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
    ''')
    op.execute('''
        CREATE TABLE IF NOT EXISTS preferences (
            id INTEGER PRIMARY KEY,
            weights TEXT,
            config TEXT,
            updated_at TEXT NOT NULL
        )
    ''')
    op.execute('''
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
    ''')


def downgrade() -> None:
    """Downgrade schema."""
    pass
