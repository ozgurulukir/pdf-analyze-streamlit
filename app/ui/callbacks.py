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
from app.core.logger import logger
from app.core.services.file_service import FileService
from app.ui.state import state
from app.ui.utils import handle_errors


def add_alert(message: str, type: str = "info") -> None:
    """Queue a pure st.toast message for the next rerun."""
    icons = {"success": "✅", "error": "❌", "warning": "⚠️", "info": "ℹ️"}
    state.set("pending_toast", (message, icons.get(type, "ℹ️")))


@handle_errors("Çalışma alanları yüklenirken bir hata oluştu")
def load_workspaces() -> None:
    """Load workspaces into session state using cached query."""
    # Use cached database manager
    db = get_cached_database_manager()
    workspaces = db.workspaces.get_all()
    state.workspaces = workspaces

    active_id = state.active_workspace_id
    if not active_id:
        active = next((ws for ws in workspaces if ws.is_active), None)
        if active:
            state.active_workspace_id = active.id


@handle_errors("Çalışma alanı oluşturulamadı", use_alert=True)
def create_workspace_callback(name: str) -> None:
    """Create a new workspace and its vector collection."""
    if not name.strip():
        return

    db = get_cached_database_manager()
    workspace = Workspace(name=name)
    db.workspaces.create(workspace)

    # Initialize ChromaDB collection with cached manager
    chroma = get_cached_chroma_manager()
    chroma.get_or_create_collection(workspace.id, workspace.name)

    db.workspaces.set_active(workspace.id)
    state.active_workspace_id = workspace.id

    # Invalidate workspace cache
    invalidate_workspace_cache(workspace.id)

    load_workspaces()
    add_alert(f"Çalışma alanı oluşturuldu: {name}", "success")


@handle_errors("Çalışma alanı seçilemedi")
def select_workspace_callback(workspace_id: str) -> None:
    """Switch the active workspace."""
    db = get_cached_database_manager()
    db.workspaces.set_active(workspace_id)
    state.active_workspace_id = workspace_id
    # Reset current session when switching workspaces
    state.active_session_id = None


@handle_errors("Çalışma alanı adı değiştirilemedi")
def rename_workspace_callback(workspace_id: str, new_name: str) -> None:
    """Rename an existing workspace."""
    if not new_name.strip():
        return

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


@handle_errors("Çalışma alanı silinirken hata oluştu", use_alert=True)
def delete_workspace_callback(workspace_id: str) -> None:
    """Delete a workspace and all its associated vector data."""
    db = get_cached_database_manager()
    workspace = db.workspaces.get_by_id(workspace_id)
    if workspace:
        chroma = get_cached_chroma_manager()
        chroma.delete_workspace_data(workspace_id, workspace.name)
        db.workspaces.delete(workspace_id)

        # Invalidate cache
        invalidate_workspace_cache(workspace_id)

        if state.active_workspace_id == workspace_id:
            state.active_workspace_id = None

        load_workspaces()
        add_alert("Çalışma alanı silindi.", "success")


@handle_errors("Dosya yükleme işlemi başarısız oldu", use_alert=True)
def upload_files_callback(
    uploaded_files: list, workspace: Workspace, settings: dict
) -> None:
    """Handle multi-file upload via FileService."""
    if not uploaded_files or not workspace:
        return

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


@handle_errors("Dosya silinemedi", use_alert=True)
def delete_file_callback(file_id: str) -> None:
    """Remove a document record."""
    active_ws_id = state.active_workspace_id
    if not active_ws_id:
        return

    db = get_cached_database_manager()
    file_service = FileService(db)
    file_service.delete_file(file_id, active_ws_id)

    # Invalidate file cache
    invalidate_file_cache(active_ws_id, file_id)

    load_workspaces()
    add_alert("Dosya silindi.", "success")


@handle_errors("Dizin işleme hatası", use_alert=True)
def process_directory_callback(directory_path: str, workspace: Workspace) -> None:
    """Run directory scanner via FileService."""
    if not directory_path or not workspace:
        st.error("Dizin yolu ve Workspace seçilmelidir.")
        return

    db = get_cached_database_manager()
    file_service = FileService(db)

    # Build embedding settings from state
    use_hf = state.get(SessionKeys.USE_HUGGINGFACE, False)
    settings = {
        "use_huggingface": use_hf,
        "model_name": state.get(SessionKeys.HF_EMBED_MODEL)
        if use_hf
        else state.get(SessionKeys.EMBED_MODEL),
        "ollama_url": state.get(SessionKeys.OLLAMA_URL),
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


@handle_errors("Sistem sıfırlanırken kritik bir hata oluştu", use_alert=True)
def reset_system_callback() -> None:
    """Perform a global system hard reset."""
    # 1. Clear all caches first
    clear_all_caches()

    # 2. Reset Vector Store
    config = AppConfig()
    chroma_path = state.get(SessionKeys.CHROMA_PATH, config.CHROMA_PERSIST_DIR)
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
    config_obj._perform_validation() # Re-resolve absolute paths
    logger.info("Global AppConfig paths reset to defaults")

    # 5. Clear session state comprehensively
    keys_to_reset = [
        SessionKeys.ACTIVE_WORKSPACE_ID,
        SessionKeys.ACTIVE_SESSION_ID,
        SessionKeys.CHAT_HISTORY,
        SessionKeys.WORKSPACES,
        SessionKeys.PREFERENCES,
        SessionKeys.CURRENT_PAGE,
        SessionKeys.DATA_DIR,
        SessionKeys.CHROMA_PATH,
    ]

    for key in keys_to_reset:
        state.delete(key)

    add_alert("Tüm sistem başarıyla sıfırlandı!", "success")
    load_workspaces()


@handle_errors("Sohbet geçmişi temizlenemedi")
def clear_chat_history_callback(workspace_id: str) -> None:
    """Clear chat history for a workspace and reset UI state."""
    db = get_cached_database_manager()
    db.messages.clear_by_workspace(workspace_id)

    # Invalidate message cache
    cached_get_messages.clear(workspace_id)

    # Sync session state to reflect changes in UI immediately
    if state.get(SessionKeys.CHAT_HISTORY) is not None:
        state.set(SessionKeys.CHAT_HISTORY, [])

    st.success("Sohbet geçmişi temizlendi!")
    st.rerun()


@handle_errors("Yeni sohbet başlatılamadı")
def create_chat_session_callback(workspace_id: str, title: str = "Yeni Sohbet") -> None:
    """Create a new chat session for a workspace."""
    db = get_cached_database_manager()
    session = ChatSession(workspace_id=workspace_id, title=title)
    db.chat_sessions.create(session)
    state.active_session_id = session.id
    st.success(f"Yeni sohbet başlatıldı: {title}")
    # Invalidate session cache
    from app.core.cache import invalidate_session_cache
    invalidate_session_cache(workspace_id)


def select_chat_session_callback(session_id: str | None) -> None:
    """Switch the active chat session."""
    state.active_session_id = session_id
    st.rerun()


@handle_errors("Sohbet başlığı değiştirilemedi")
def rename_chat_session_callback(session_id: str, new_title: str) -> None:
    """Rename an existing chat session."""
    if not new_title.strip():
        return
    db = get_cached_database_manager()
    session = db.chat_sessions.get_by_id(session_id)
    if session:
        session.title = new_title
        db.chat_sessions.update(session)
        st.success("Sohbet başlığı güncellendi.")
        st.rerun()


@handle_errors("Sohbet oturumu silinemedi")
def delete_chat_session_callback(session_id: str) -> None:
    """Delete a chat session."""
    db = get_cached_database_manager()
    db.chat_sessions.delete(session_id)
    if state.active_session_id == session_id:
        state.active_session_id = None
    st.success("Sohbet oturumu silindi.")


@handle_errors("Ayarlar kaydedilirken hata oluştu")
def save_settings_callback() -> None:
    """Extract current settings from session state and persist to database."""
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
        val = state.get(key)
        if val is not None:
            new_config[key] = val

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


def on_provider_change_callback():
    """Update Base URL automatically when provider type changes."""
    new_type = state.get(SessionKeys.LAST_ENDPOINT_TYPE)
    if new_type == "Ollama Cloud":
        state.set(SessionKeys.LLM_BASE_URL, "https://ollama.com/v1")
    elif new_type == "Yerel Ollama":
        state.set(SessionKeys.LLM_BASE_URL, "http://localhost:11434/v1")
    save_settings_callback()


def on_embed_type_change_callback():
    """Sync boolean state with radio selection."""
    embed_choice = state.get("_temp_embed_type")
    state.set(SessionKeys.USE_HUGGINGFACE, embed_choice == "HuggingFace")
    save_settings_callback()


@handle_errors("Bağlantı testi sırasında hata oluştu", use_alert=True)
def test_connections_callback():
    """Test both LLM and Embedding connections with current settings."""
    from app.core.rag import create_llm
    from app.core.chroma import EmbeddingManager
    from app.core.container import get_config
    
    config = get_config()
    
    with st.spinner("Bağlantılar test ediliyor..."):
        # 1. Test LLM
        try:
            llm = create_llm(
                base_url=state.get(SessionKeys.LLM_BASE_URL) or config.LLM_BASE_URL,
                api_key=state.get(SessionKeys.OLLAMA_API_KEY) or config.OLLAMA_API_KEY,
                model=state.get(SessionKeys.LLM_MODEL) or config.LLM_MODEL,
                temperature=0.1
            )
            # Try a simple invoke (some providers might require this to check runner)
            llm.invoke("Merhaba")
            llm_ok = True
        except Exception as e:
            logger.error(f"LLM test failed: {e}")
            add_alert(f"LLM Bağlantı Hatası: {str(e)}", "error")
            llm_ok = False

        # 2. Test Embedding
        try:
            use_hf = state.get(SessionKeys.USE_HUGGINGFACE, False)
            embed_manager = EmbeddingManager(
                use_huggingface=use_hf,
                ollama_model=state.get(SessionKeys.EMBED_MODEL) or config.EMBED_MODEL,
                ollama_url=state.get(SessionKeys.OLLAMA_URL) or config.OLLAMA_BASE_URL,
                hf_model=state.get(SessionKeys.HF_EMBED_MODEL) or config.HF_EMBED_MODEL
            )
            # Try a simple embedding
            embed_manager.get_query_embedding("test")
            embed_ok = True
        except Exception as e:
            logger.error(f"Embedding test failed: {e}")
            add_alert(f"Embedding Bağlantı Hatası: {str(e)}", "error")
            embed_ok = False

        if llm_ok and embed_ok:
            add_alert("Tüm bağlantılar başarıyla doğrulandı!", "success")
        elif llm_ok:
            add_alert("LLM bağlantısı başarılı, ancak Embedding hatası var.", "warning")
        elif embed_ok:
            add_alert("Embedding bağlantısı başarılı, ancak LLM hatası var.", "warning")


@handle_errors("Önbellek temizlenemedi")
def clear_cache_callback() -> None:
    """Clear all caches from UI."""
    stats = clear_all_caches()
    st.success(f"Önbellekler temizlendi! ({len(stats)} cache)")


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
