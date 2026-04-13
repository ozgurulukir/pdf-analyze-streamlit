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


@handle_errors("messages.db_error")
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


@handle_errors("messages.db_error", use_alert=True)
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
    L = st.session_state.locale
    add_alert(L.messages.workspace_created.format(name), "success")


@handle_errors("messages.db_error")
def select_workspace_callback(workspace_id: str) -> None:
    """Switch the active workspace."""
    db = get_cached_database_manager()
    db.workspaces.set_active(workspace_id)
    state.active_workspace_id = workspace_id
    # Reset current session when switching workspaces
    state.active_session_id = None


@handle_errors("messages.db_error")
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
        L = st.session_state.locale
        st.success(L.messages.workspace_created.format(new_name))


@handle_errors("messages.db_error", use_alert=True)
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
        L = st.session_state.locale
        add_alert(L.common.success, "success")


@handle_errors("messages.file_uploaded", use_alert=True)
def upload_files_callback(
    uploaded_files: list, workspace: Workspace
) -> None:
    """Handle multi-file upload via FileService."""
    if not uploaded_files or not workspace:
        return

    db = get_cached_database_manager()
    file_service = FileService(db)
    L = st.session_state.locale

    with st.spinner(L.common.loading):
        # Build embedding settings from SSOT (Session State)
        embedding_settings = {
            "use_huggingface": st.session_state.get(SessionKeys.USE_HUGGINGFACE.value, False),
            "embed_model": st.session_state.get(SessionKeys.EMBED_MODEL.value, ""),
            "ollama_url": st.session_state.get(SessionKeys.OLLAMA_URL.value, ""),
            "hf_model": st.session_state.get(SessionKeys.HF_EMBED_MODEL.value, ""),
        }
        
        added_count, successes, errors = file_service.upload_files(
            uploaded_files, workspace, embedding_settings
        )

        for err in errors:
            add_alert(err, "warning")
        for msg in successes:
            add_alert(msg, "success")

    if added_count > 0:
        # Invalidate file cache for this workspace
        invalidate_file_cache(workspace.id)
        load_workspaces()


@handle_errors("messages.db_error", use_alert=True)
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
    L = st.session_state.locale
    add_alert(L.common.success, "success")


@handle_errors("library.status_error", use_alert=True)
def process_directory_callback(directory_path: str, workspace: Workspace) -> None:
    """Run directory scanner via FileService."""
    if not directory_path or not workspace:
        L = st.session_state.locale
        st.error(L.workspace.no_active)
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

    L = st.session_state.locale
    with st.spinner(L.common.loading):
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


@handle_errors("messages.db_error", use_alert=True)
def reset_system_callback() -> None:
    """Perform a global system hard reset."""
    # 1. Clear all caches first
    clear_all_caches()

    # 2. Reset Vector Store
    config = AppConfig()
    chroma_path = state.get(SessionKeys.CHROMA_PATH, config.CHROMA_PERSIST_DIR)
    chroma = get_cached_chroma_manager({"chroma_path": chroma_path})
    chroma.hard_reset()

    # 3. Clear database tables
    db = get_cached_database_manager()
    db.reset_system()

    # 4. Explicitly Save Factory Defaults to Database using SessionKeys format
    # IMPORTANT: config_dict must use SessionKeys (lowercase) as keys,
    # NOT model_dump() (UPPERCASE), because sync_with_db reads by SessionKeys.
    from app.core.constants import SessionKeys as SK
    from app.core.models import UserPreferences

    default_config = AppConfig()
    config_dict = {
        SK.LLM_MODEL.value:           default_config.LLM_MODEL,
        SK.LLM_BASE_URL.value:        default_config.LLM_BASE_URL,
        SK.OLLAMA_API_KEY.value:      default_config.OLLAMA_API_KEY,
        SK.LLM_TEMPERATURE.value:     default_config.LLM_TEMPERATURE,
        SK.LAST_ENDPOINT_TYPE.value:  default_config.DEFAULT_LLM_PROVIDER,
        SK.USE_HUGGINGFACE.value:     default_config.USE_HUGGINGFACE,
        SK.EMBED_MODEL.value:         default_config.EMBED_MODEL,
        SK.OLLAMA_URL.value:          default_config.OLLAMA_BASE_URL,
        SK.HF_EMBED_MODEL.value:      default_config.HF_EMBED_MODEL,
        SK.DATA_DIR.value:            default_config.DATA_DIR,
        SK.CHROMA_PATH.value:         default_config.CHROMA_PERSIST_DIR,
        SK.CHUNK_SIZE.value:          default_config.CHUNK_SIZE,
        SK.CHUNK_OVERLAP.value:       default_config.CHUNK_OVERLAP,
        SK.PROMPT_TEXTS.value:        default_config.PROMPT_TEXTS,
    }

    init_prefs = UserPreferences(config=config_dict)
    db.preferences.save(init_prefs)
    logger.info("Factory defaults saved to DB with correct SessionKeys format")

    # 5. Reset global container & config singleton
    from app.core.container import reset_container
    reset_container()
    logger.info("Global application container and AppConfig reset to defaults")

    # 5. Clear ALL session state (The nuclear option for 1.40+)
    st.session_state.clear()
    logger.info("Session state cleared completely")

    # 6. Pre-initialize core requirements for the next script run
    from app.core.locales import get_locale
    st.session_state["locale"] = get_locale("tr")

    L = st.session_state.locale
    add_alert(L.common.success, "success")
    load_workspaces()
    # 7. Force app rerun to trigger main.py -> init_session_state()
    st.rerun()


@handle_errors("messages.db_error")
def clear_chat_history_callback(workspace_id: str) -> None:
    """Clear chat history for a workspace and reset UI state."""
    db = get_cached_database_manager()
    db.messages.clear_by_workspace(workspace_id)

    # Invalidate message cache
    cached_get_messages.clear(workspace_id)

    # Sync session state to reflect changes in UI immediately
    if state.get(SessionKeys.CHAT_HISTORY) is not None:
        state.set(SessionKeys.CHAT_HISTORY, [])

    L = st.session_state.locale
    st.success(L.common.success)


@handle_errors("messages.chat_init_failed")
def create_chat_session_callback(workspace_id: str, title: str = "Yeni Sohbet") -> None:
    """Create a new chat session for a workspace."""
    db = get_cached_database_manager()
    session = ChatSession(workspace_id=workspace_id, title=title)
    db.chat_sessions.create(session)
    state.active_session_id = session.id
    L = st.session_state.locale
    st.success(L.messages.workspace_created.format(title))
    # Invalidate session cache
    from app.core.cache import invalidate_workspace_cache
    invalidate_workspace_cache(workspace_id)


def select_chat_session_callback(session_id: str | None) -> None:
    """Switch the active chat session."""
    state.active_session_id = session_id


@handle_errors("messages.db_error")
def rename_chat_session_callback(session_id: str, new_title: str) -> None:
    """Rename an existing chat session."""
    if not new_title.strip():
        return
    db = get_cached_database_manager()
    session = db.chat_sessions.get_by_id(session_id)
    if session:
        session.title = new_title
        db.chat_sessions.update(session)
        L = st.session_state.locale
        st.success(L.common.success)


@handle_errors("messages.db_error")
def delete_chat_session_callback(session_id: str) -> None:
    """Delete a chat session."""
    db = get_cached_database_manager()
    db.chat_sessions.delete(session_id)
    if state.active_session_id == session_id:
        state.active_session_id = None
    L = st.session_state.locale
    st.success(L.common.success)


@handle_errors("messages.db_error")
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
    """Update Base URL automatically when provider type changes using AppConfig defaults."""
    from app.core.container import get_config
    config = get_config()
    new_type = state.get(SessionKeys.LAST_ENDPOINT_TYPE)
    
    if new_type == "cloud":
        state.set(SessionKeys.LLM_BASE_URL, config.LLM_BASE_URL)
    elif new_type == "ollama":
        # For local Ollama, we usually append /v1 for OpenAI compatibility if using a proxy,
        # but the default OLLAMA_BASE_URL (11434) is typically used for discovery.
        # We ensure it is a valid LLM endpoint.
        local_url = config.OLLAMA_BASE_URL
        if "11434" in local_url and not local_url.endswith("/v1"):
            local_url = local_url.rstrip("/") + "/v1"
        state.set(SessionKeys.LLM_BASE_URL, local_url)
    save_settings_callback()


def on_embed_type_change_callback():
    """Sync boolean state with radio selection."""
    embed_choice = state.get("_temp_embed_type")
    state.set(SessionKeys.USE_HUGGINGFACE, embed_choice == "hf")
    save_settings_callback()


@handle_errors("messages.llm_error", use_alert=True)
def test_connections_callback():
    """Test both LLM and Embedding connections with current settings."""
    from app.core.chroma import EmbeddingManager
    from app.core.container import get_config
    from app.core.rag import create_llm

    config = get_config()
    L = st.session_state.locale

    with st.spinner(L.common.loading):
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
            add_alert(L.common.success, "success")
        elif llm_ok:
            add_alert(f"{L.chat.title} OK, {L.settings.embed_tab} ERR", "warning")
        elif embed_ok:
            add_alert(f"{L.settings.embed_tab} OK, {L.chat.title} ERR", "warning")


@handle_errors("messages.db_error")
def clear_cache_callback() -> None:
    """Clear all caches from UI."""
    clear_all_caches()
    L = st.session_state.locale
    st.success(L.common.success)


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
