from datetime import datetime

import streamlit as st

from app.core import ChatSession, Workspace
from app.core.cache import (
    cached_get_messages,
    cached_get_workspace_files,
    clear_all_caches,
    get_cached_chroma_manager,
    get_cached_database_manager,
    invalidate_embedding_cache,
    invalidate_file_cache,
    invalidate_workspace_cache,
)
from app.core.config import AppConfig
from app.core.constants import SessionKeys
from app.core.exceptions import ChromaError, DatabaseError
from app.core.logger import logger
from app.core.services.file_service import FileService


def add_alert(message: str, type: str = "info") -> None:
    """Queue a pure st.toast message for the next rerun."""
    icons = {"success": "✅", "error": "❌", "warning": "⚠️", "info": "ℹ️"}
    st.session_state["pending_toast"] = (message, icons.get(type, "ℹ️"))


def load_workspaces() -> None:
    """Load workspaces into session state using cached query."""
    try:
        # Use cached database manager
        db = get_cached_database_manager()
        workspaces = db.workspaces.get_all()
        st.session_state[SessionKeys.WORKSPACES.value] = workspaces

        active_id = st.session_state.get(SessionKeys.ACTIVE_WORKSPACE_ID.value)
        if not active_id:
            active = next((ws for ws in workspaces if ws.is_active), None)
            if active:
                st.session_state[SessionKeys.ACTIVE_WORKSPACE_ID.value] = active.id
    except Exception as e:
        logger.error(f"Failed to load workspaces: {e}")
        st.error(f"Çalışma alanları yüklenirken bir hata oluştu: {str(e)}")


def create_workspace_callback(name: str) -> None:
    """Create a new workspace and its vector collection."""
    if not name.strip():
        return

    try:
        db = get_cached_database_manager()
        workspace = Workspace(name=name)
        db.workspaces.create(workspace)

        # Initialize ChromaDB collection with cached manager
        chroma = get_cached_chroma_manager()
        chroma.get_or_create_collection(workspace.id, workspace.name)

        db.workspaces.set_active(workspace.id)
        st.session_state[SessionKeys.ACTIVE_WORKSPACE_ID.value] = workspace.id

        # Invalidate workspace cache
        invalidate_workspace_cache(workspace.id)

        load_workspaces()
        add_alert(f"Çalışma alanı oluşturuldu: {name}", "success")
        st.rerun()
    except (DatabaseError, ChromaError) as e:
        logger.error(f"Workspace creation error: {e}")
        add_alert(f"Çalışma alanı oluşturulamadı: {str(e)}", "error")
        st.rerun()
    except Exception as e:
        logger.critical(f"Unexpected error creating workspace: {e}")
        st.error("Beklenmedik bir hata oluştu.")


def select_workspace_callback(workspace_id: str) -> None:
    """Switch the active workspace."""
    try:
        db = get_cached_database_manager()
        db.workspaces.set_active(workspace_id)
        st.session_state[SessionKeys.ACTIVE_WORKSPACE_ID.value] = workspace_id
        # Reset current session when switching workspaces
        st.session_state[SessionKeys.ACTIVE_SESSION_ID.value] = None
        st.rerun()
    except Exception as e:
        logger.error(f"Failed to select workspace {workspace_id}: {e}")
        st.error("Çalışma alanı seçilemedi.")


def rename_workspace_callback(workspace_id: str, new_name: str) -> None:
    """Rename an existing workspace."""
    if not new_name.strip():
        return

    try:
        db = get_cached_database_manager()
        workspace = db.workspaces.get_by_id(workspace_id)
        if workspace:
            workspace.name = new_name
            workspace.last_modified = datetime.now()
            db.workspaces.update(workspace)

            # Invalidate cache
            invalidate_workspace_cache(workspace_id)

            load_workspaces()
            st.success(f"Çalışma alanı adı güncellendi: {new_name}")
            st.rerun()
    except Exception as e:
        logger.error(f"Failed to rename workspace {workspace_id}: {e}")
        st.error("Çalışma alanı adı değiştirilemedi.")


def delete_workspace_callback(workspace_id: str) -> None:
    """Delete a workspace and all its associated vector data."""
    try:
        db = get_cached_database_manager()
        workspace = db.workspaces.get_by_id(workspace_id)
        if workspace:
            chroma = get_cached_chroma_manager()
            chroma.delete_workspace_data(workspace_id, workspace.name)
            db.workspaces.delete(workspace_id)

            # Invalidate cache
            invalidate_workspace_cache(workspace_id)

            if (
                st.session_state.get(SessionKeys.ACTIVE_WORKSPACE_ID.value)
                == workspace_id
            ):
                st.session_state[SessionKeys.ACTIVE_WORKSPACE_ID.value] = None

            load_workspaces()
            add_alert("Çalışma alanı silindi.", "success")
            st.rerun()
    except Exception as e:
        logger.error(f"Failed to delete workspace {workspace_id}: {e}")
        add_alert("Çalışma alanı silinirken hata oluştu.", "error")
        st.rerun()


def upload_files_callback(
    uploaded_files: list, workspace: Workspace, settings: dict
) -> None:
    """Handle multi-file upload via FileService."""
    if not uploaded_files or not workspace:
        return

    try:
        db = get_cached_database_manager()
        file_service = FileService(db)

        with st.spinner("Dosyalar işleniyor..."):
            added_count, successes, errors = file_service.upload_files(
                uploaded_files, workspace, settings.get("embedding", {})
            )

            for err in errors:
                add_alert(err, "warning")
            for msg in successes:
                add_alert(msg, "success")

        if added_count > 0:
            # Invalidate file cache for this workspace
            invalidate_file_cache(workspace.id)
            load_workspaces()
            st.rerun()
    except Exception as e:
        add_alert(f"Dosya yükleme işlemi başarısız oldu: {str(e)}", "error")
        st.rerun()


def delete_file_callback(file_id: str) -> None:
    """Remove a document record."""
    active_ws_id = st.session_state.get(SessionKeys.ACTIVE_WORKSPACE_ID.value)
    if not active_ws_id:
        return

    try:
        db = get_cached_database_manager()
        file_service = FileService(db)
        file_service.delete_file(file_id, active_ws_id)

        # Invalidate file cache
        invalidate_file_cache(active_ws_id, file_id)

        load_workspaces()
        add_alert("Dosya silindi.", "success")
        st.rerun()
    except Exception as e:
        logger.error(f"Failed to delete file {file_id}: {e}")
        add_alert("Dosya silinemedi.", "error")
        st.rerun()


def process_directory_callback(directory_path: str, workspace: Workspace) -> None:
    """Run directory scanner via FileService."""
    if not directory_path or not workspace:
        st.error("Dizin yolu ve Workspace seçilmelidir.")
        return

    try:
        db = get_cached_database_manager()
        file_service = FileService(db)

        # Build embedding settings from state
        settings = {
            "use_huggingface": st.session_state.get(
                SessionKeys.USE_HUGGINGFACE.value, False
            ),
            "model_name": st.session_state.get(SessionKeys.EMBED_MODEL.value)
            if not st.session_state.get(SessionKeys.USE_HUGGINGFACE.value)
            else st.session_state.get(SessionKeys.HF_EMBED_MODEL.value),
            "ollama_url": st.session_state.get(SessionKeys.OLLAMA_URL.value),
        }

        with st.spinner("Dizin taranıyor..."):
            added_count, successes, errors = file_service.process_directory(
                directory_path, workspace, settings
            )

            for err in errors:
                add_alert(err, "error")
            for msg in successes:
                add_alert(msg, "success")

        if added_count > 0:
            # Invalidate file cache
            invalidate_file_cache(workspace.id)
            load_workspaces()
            st.rerun()
    except Exception as e:
        logger.error(f"Directory processing callback failure: {e}")
        add_alert("Dizin işleme hatası.", "error")
        st.rerun()


def reset_system_callback() -> None:
    """Perform a global system hard reset."""
    try:
        # 1. Clear all caches first
        clear_all_caches()

        # 2. Reset Vector Store
        config = AppConfig()
        chroma_path = st.session_state.get(
            SessionKeys.CHROMA_PATH.value, config.CHROMA_PERSIST_DIR
        )
        chroma = get_cached_chroma_manager({"chroma_path": chroma_path})
        chroma.hard_reset()

        # 3. Reset SQLite DB
        db = get_cached_database_manager()
        db.reset_system()

        # 4. Reset global config singleton to defaults
        from app.core.container import get_config
        config_obj = get_config()
        default_config = AppConfig()
        config_obj.DATA_DIR = default_config.DATA_DIR
        config_obj.CHROMA_PERSIST_DIR = default_config.CHROMA_PERSIST_DIR
        config_obj.validate_paths_and_config() # Re-resolve absolute paths
        logger.info("Global AppConfig paths reset to defaults")

        # 5. Clear session state comprehensively
        keys_to_reset = [
            SessionKeys.ACTIVE_WORKSPACE_ID.value,
            SessionKeys.ACTIVE_SESSION_ID.value,
            SessionKeys.CHAT_HISTORY.value,
            SessionKeys.WORKSPACES.value,
            SessionKeys.PREFERENCES.value,
            SessionKeys.CURRENT_PAGE.value,
            SessionKeys.DATA_DIR.value,
            SessionKeys.CHROMA_PATH.value,
        ]

        for key in keys_to_reset:
            if key in st.session_state:
                del st.session_state[key]

        add_alert("Tüm sistem başarıyla sıfırlandı!", "success")
        load_workspaces()
        st.rerun()
    except Exception as e:
        logger.error(f"System reset failure: {e}")
        add_alert("Sistem sıfırlanırken kritik bir hata oluştu.", "error")
        st.rerun()


def clear_chat_history_callback(workspace_id: str) -> None:
    """Clear chat history for a workspace and reset UI state."""
    try:
        db = get_cached_database_manager()
        db.messages.clear_by_workspace(workspace_id)

        # Invalidate message cache
        cached_get_messages.clear(workspace_id)

        # Sync session state to reflect changes in UI immediately
        if SessionKeys.CHAT_HISTORY.value in st.session_state:
            st.session_state[SessionKeys.CHAT_HISTORY.value] = []

        st.success("Sohbet geçmişi temizlendi!")
        st.rerun()
    except Exception as e:
        logger.error(f"Failed to clear chat history: {e}")
        st.error("Sohbet geçmişi temizlenemedi.")


def create_chat_session_callback(workspace_id: str, title: str = "Yeni Sohbet") -> None:
    """Create a new chat session for a workspace."""
    try:
        db = get_cached_database_manager()
        session = ChatSession(workspace_id=workspace_id, title=title)
        db.chat_sessions.create(session)
        st.session_state[SessionKeys.ACTIVE_SESSION_ID.value] = session.id
        st.success(f"Yeni sohbet başlatıldı: {title}")
        st.rerun()
    except Exception as e:
        logger.error(f"Failed to create chat session: {e}")
        st.error("Yeni sohbet başlatılamadı.")


def select_chat_session_callback(session_id: str | None) -> None:
    """Switch the active chat session."""
    st.session_state[SessionKeys.ACTIVE_SESSION_ID.value] = session_id
    st.rerun()


def rename_chat_session_callback(session_id: str, new_title: str) -> None:
    """Rename an existing chat session."""
    if not new_title.strip():
        return
    try:
        db = get_cached_database_manager()
        session = db.chat_sessions.get_by_id(session_id)
        if session:
            session.title = new_title
            db.chat_sessions.update(session)
            st.success("Sohbet başlığı güncellendi.")
            st.rerun()
    except Exception as e:
        logger.error(f"Failed to rename chat session: {e}")
        st.error("Sohbet başlığı değiştirilemedi.")


def delete_chat_session_callback(session_id: str) -> None:
    """Delete a chat session."""
    try:
        db = get_cached_database_manager()
        db.chat_sessions.delete(session_id)
        if st.session_state.get(SessionKeys.ACTIVE_SESSION_ID.value) == session_id:
            st.session_state[SessionKeys.ACTIVE_SESSION_ID.value] = None
        st.success("Sohbet oturumu silindi.")
        st.rerun()
    except Exception as e:
        logger.error(f"Failed to delete chat session: {e}")
        st.error("Sohbet oturumu silinemedi.")


def save_settings_callback() -> None:
    """Extract current settings from session state and persist to database."""
    try:
        db = get_cached_database_manager()
        prefs = db.preferences.get()

        # Check if embedding settings changed
        old_use_hf = prefs.config.get(SessionKeys.USE_HUGGINGFACE.value, False)
        old_embed_model = prefs.config.get(
            SessionKeys.EMBED_MODEL.value, "nomic-embed-text"
        )

        # Define keys to persist
        config_keys = [
            SessionKeys.LLM_MODEL.value,
            SessionKeys.LLM_BASE_URL.value,
            SessionKeys.OLLAMA_API_KEY.value,
            SessionKeys.LLM_TEMPERATURE.value,
            SessionKeys.LAST_ENDPOINT_TYPE.value,
            SessionKeys.USE_HUGGINGFACE.value,
            SessionKeys.EMBED_MODEL.value,
            SessionKeys.OLLAMA_URL.value,
            SessionKeys.HF_EMBED_MODEL.value,
            SessionKeys.DATA_DIR.value,
            SessionKeys.CHROMA_PATH.value,
            SessionKeys.CHUNK_SIZE.value,
            SessionKeys.CHUNK_OVERLAP.value,
            SessionKeys.THEME.value,
        ]

        # Capture current state
        new_config = {}
        for key in config_keys:
            if key in st.session_state:
                new_config[key] = st.session_state[key]

        prefs.config = new_config
        prefs.updated_at = datetime.now()
        db.preferences.save(prefs)

        # Update live config singleton so background services see the change immediately
        from app.core.container import get_config
        get_config().sync_with_db(new_config)
        logger.info("Live AppConfig synced after settings update")

        # Invalidate embedding cache if settings changed
        new_use_hf = new_config.get(SessionKeys.USE_HUGGINGFACE.value, False)
        new_embed_model = new_config.get(
            SessionKeys.EMBED_MODEL.value, "nomic-embed-text"
        )

        if old_use_hf != new_use_hf or old_embed_model != new_embed_model:
            invalidate_embedding_cache()
            logger.info("Embedding cache invalidated due to settings change")

    except Exception as e:
        logger.error(f"Failed to save settings: {e}")


def clear_cache_callback() -> None:
    """Clear all caches from UI."""
    try:
        stats = clear_all_caches()
        st.success(f"Önbellekler temizlendi! ({len(stats)} cache)")
        st.rerun()
    except Exception as e:
        logger.error(f"Failed to clear caches: {e}")
        st.error("Önbellek temizlenemedi.")


def get_cached_files(workspace_id: str) -> list:
    """Get files for a workspace using cache."""
    from app.core.models import FileMetadata

    files_data = cached_get_workspace_files(workspace_id)

    # Convert dicts back to objects if needed
    files = []
    for f in files_data:
        if isinstance(f, dict):
            # Safe parsing for FileMetadata with fixed types
            uploaded_raw = f.get("uploaded_at")
            if isinstance(uploaded_raw, datetime):
                uploaded_at = uploaded_raw
            elif isinstance(uploaded_raw, str):
                try:
                    uploaded_at = datetime.fromisoformat(uploaded_raw)
                except ValueError:
                    uploaded_at = datetime.now()
            else:
                uploaded_at = datetime.now()

            processed_raw = f.get("processed_at")
            if isinstance(processed_raw, datetime):
                processed_at = processed_raw
            elif isinstance(processed_raw, str):
                try:
                    processed_at = datetime.fromisoformat(processed_raw)
                except ValueError:
                    processed_at = None
            else:
                processed_at = None

            file_obj = FileMetadata(
                id=str(f.get("id", "")),
                workspace_id=str(f.get("workspace_id", "")),
                filename=str(f.get("filename", "")),
                original_name=str(f.get("original_name", "")),
                file_type=str(f.get("file_type", "")),
                size=int(f.get("size", 0)),
                status=str(f.get("status", "pending")),
                chunk_count=int(f.get("chunk_count", 0)),
                content_hash=str(f.get("content_hash", "")),
                uploaded_at=uploaded_at,
                processed_at=processed_at,
                error_message=str(f.get("error_message", ""))
                if f.get("error_message")
                else None,
                tags=list(f.get("tags", [])),
            )
            files.append(file_obj)
        else:
            files.append(f)

    return files
