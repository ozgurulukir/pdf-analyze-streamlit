"""Callback functions for UI events with cache integration."""
from datetime import datetime
from typing import Dict, List

import streamlit as st

from app.core import DatabaseManager, FileMetadata, Message, Workspace, get_job_queue
from app.core.cache import (
    cached_get_messages,
    cached_get_workspace_files,
    cached_get_workspaces,
    clear_all_caches,
    get_cache_stats,
    get_cached_chroma_manager,
    get_cached_database_manager,
    get_cached_embedding_manager,
    invalidate_embedding_cache,
    invalidate_file_cache,
    invalidate_workspace_cache,
)
from app.core.chroma import ChromaManager, EmbeddingManager
from app.core.config import AppConfig
from app.core.constants import SessionKeys
from app.core.logger import logger
from app.core.services.chat_service import ChatService
from app.core.services.file_service import FileService


def load_workspaces() -> None:
    """Load workspaces into session state using cached query."""
    try:
        # Use cached database manager
        db = get_cached_database_manager()
        workspaces = db.get_workspaces()
        st.session_state[SessionKeys.WORKSPACES.value] = workspaces

        active_id = st.session_state.get(SessionKeys.ACTIVE_WORKSPACE_ID.value)
        if not active_id:
            active = next((ws for ws in workspaces if ws.is_active), None)
            if active:
                st.session_state[SessionKeys.ACTIVE_WORKSPACE_ID.value] = active.id
    except Exception as e:
        logger.error(f"Failed to load workspaces: {e}")
        st.error("Çalışma alanları yüklenirken bir hata oluştu.")


def create_workspace_callback(name: str) -> None:
    """Create a new workspace and its vector collection."""
    if not name.strip():
        return

    try:
        db = get_cached_database_manager()
        workspace = Workspace(name=name)
        db.create_workspace(workspace)

        # Initialize ChromaDB collection with cached manager
        chroma = get_cached_chroma_manager()
        chroma.get_or_create_collection(workspace.id, workspace.name)

        db.set_active_workspace(workspace.id)
        st.session_state[SessionKeys.ACTIVE_WORKSPACE_ID.value] = workspace.id

        # Invalidate workspace cache
        invalidate_workspace_cache(workspace.id)

        load_workspaces()
        st.success(f"Çalışma alanı oluşturuldu: {name}")
    except Exception as e:
        logger.error(f"Failed to create workspace '{name}': {e}")
        st.error("Çalışma alanı oluşturulamadı.")


def select_workspace_callback(workspace_id: str) -> None:
    """Switch the active workspace."""
    try:
        db = get_cached_database_manager()
        db.set_active_workspace(workspace_id)
        st.session_state[SessionKeys.ACTIVE_WORKSPACE_ID.value] = workspace_id
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
        workspace = db.get_workspace(workspace_id)
        if workspace:
            workspace.name = new_name
            workspace.last_modified = datetime.now()
            db.update_workspace(workspace)

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
        workspace = db.get_workspace(workspace_id)
        if workspace:
            chroma = get_cached_chroma_manager()
            chroma.delete_workspace_data(workspace_id, workspace.name)
            db.delete_workspace(workspace_id)

            # Invalidate cache
            invalidate_workspace_cache(workspace_id)

            if st.session_state.get(SessionKeys.ACTIVE_WORKSPACE_ID.value) == workspace_id:
                st.session_state[SessionKeys.ACTIVE_WORKSPACE_ID.value] = None

            load_workspaces()
            st.success("Çalışma alanı silindi.")
    except Exception as e:
        logger.error(f"Failed to delete workspace {workspace_id}: {e}")
        st.error("Çalışma alanı silinirken hata oluştu.")


def upload_files_callback(uploaded_files: List, workspace: Workspace, settings: Dict) -> None:
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
                st.warning(err)
            for msg in successes:
                st.success(msg)

        if added_count > 0:
            # Invalidate file cache for this workspace
            invalidate_file_cache(workspace.id)
            load_workspaces()
            st.rerun()
    except Exception as e:
        st.error(f"Dosya yükleme işlemi başarısız oldu: {str(e)}")


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
        st.rerun()
    except Exception as e:
        logger.error(f"Failed to delete file {file_id}: {e}")
        st.error("Dosya silinemedi.")


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
            "use_huggingface": st.session_state.get(SessionKeys.USE_HUGGINGFACE.value, False),
            "model_name": st.session_state.get(SessionKeys.EMBED_MODEL.value) if not st.session_state.get(SessionKeys.USE_HUGGINGFACE.value) else st.session_state.get(SessionKeys.HF_EMBED_MODEL.value),
            "ollama_url": st.session_state.get(SessionKeys.OLLAMA_URL.value)
        }

        with st.spinner("Dizin taranıyor..."):
            added_count, successes, errors = file_service.process_directory(
                directory_path, workspace, settings
            )

            for err in errors:
                st.error(err)
            for msg in successes:
                st.success(msg)

        if added_count > 0:
            # Invalidate file cache
            invalidate_file_cache(workspace.id)
            load_workspaces()
            st.rerun()
    except Exception as e:
        logger.error(f"Directory processing callback failure: {e}")
        st.error("Dizin işleme hatası.")


def reset_system_callback() -> None:
    """Perform a global system hard reset."""
    try:
        # 1. Clear all caches first
        clear_all_caches()

        # 2. Reset Vector Store
        config = AppConfig()
        chroma_path = st.session_state.get(SessionKeys.CHROMA_PATH.value, config.CHROMA_PERSIST_DIR)
        chroma = get_cached_chroma_manager({"chroma_path": chroma_path})
        chroma.hard_reset()

        # 3. Reset SQLite DB
        db = get_cached_database_manager()
        db.reset_system()

        # 4. Clear session state
        st.session_state[SessionKeys.ACTIVE_WORKSPACE_ID.value] = None
        st.session_state[SessionKeys.CHAT_HISTORY.value] = []
        st.session_state[SessionKeys.WORKSPACES.value] = []

        st.success("Tüm sistem başarıyla sıfırlandı!")
        load_workspaces()
        st.rerun()
    except Exception as e:
        logger.error(f"System reset failure: {e}")
        st.error("Sistem sıfırlanırken kritik bir hata oluştu.")


def clear_chat_history_callback(workspace_id: str) -> None:
    """Clear chat history for a workspace."""
    try:
        db = get_cached_database_manager()
        db.clear_messages(workspace_id)

        # Invalidate message cache
        cached_get_messages.clear(workspace_id)

        st.success("Sohbet geçmişi temizlendi!")
        st.rerun()
    except Exception as e:
        logger.error(f"Failed to clear chat history: {e}")
        st.error("Sohbet geçmişi temizlenemedi.")


def save_settings_callback() -> None:
    """Extract current settings from session state and persist to database."""
    try:
        db = get_cached_database_manager()
        prefs = db.get_preferences()

        # Check if embedding settings changed
        old_use_hf = prefs.config.get(SessionKeys.USE_HUGGINGFACE.value, False)
        old_embed_model = prefs.config.get(SessionKeys.EMBED_MODEL.value, "nomic-embed-text")

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
            SessionKeys.THEME.value
        ]

        # Capture current state
        new_config = {}
        for key in config_keys:
            if key in st.session_state:
                new_config[key] = st.session_state[key]

        prefs.config = new_config
        prefs.updated_at = datetime.now()
        db.save_preferences(prefs)

        # Invalidate embedding cache if settings changed
        new_use_hf = new_config.get(SessionKeys.USE_HUGGINGFACE.value, False)
        new_embed_model = new_config.get(SessionKeys.EMBED_MODEL.value, "nomic-embed-text")

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


def get_cached_files(workspace_id: str) -> List:
    """Get files for a workspace using cache."""
    from app.core.models import FileMetadata

    db = get_cached_database_manager()
    files_data = cached_get_workspace_files(workspace_id)

    # Convert dicts back to objects if needed
    files = []
    for f in files_data:
        if isinstance(f, dict):
            file_obj = FileMetadata(
                id=f.get('id'),
                workspace_id=f.get('workspace_id'),
                filename=f.get('filename'),
                original_name=f.get('original_name'),
                file_type=f.get('file_type'),
                size=f.get('size', 0),
                status=f.get('status', 'pending'),
                chunk_count=f.get('chunk_count', 0),
                content_hash=f.get('content_hash'),
                uploaded_at=f.get('uploaded_at'),
                processed_at=f.get('processed_at'),
                error_message=f.get('error_message'),
                tags=f.get('tags', [])
            )
            files.append(file_obj)
        else:
            files.append(f)

    return files
