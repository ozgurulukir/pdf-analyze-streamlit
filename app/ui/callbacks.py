"""Callback functions for UI events."""
import streamlit as st
from typing import List, Dict
from datetime import datetime

from app.core import DatabaseManager, Workspace, FileMetadata, Message, get_job_queue
from app.core.chroma import ChromaManager, EmbeddingManager
from app.core.services.file_service import FileService
from app.core.services.chat_service import ChatService
from app.core.constants import SessionKeys
from app.core.logger import logger
from app.core.config import AppConfig


def load_workspaces() -> None:
    """Load workspaces into session state using standardized keys."""
    try:
        db = DatabaseManager()
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
        db = DatabaseManager()
        workspace = Workspace(name=name)
        db.create_workspace(workspace)
        
        # Initialize ChromaDB collection
        chroma = ChromaManager()
        chroma.get_or_create_collection(workspace.id, workspace.name)
        
        db.set_active_workspace(workspace.id)
        st.session_state[SessionKeys.ACTIVE_WORKSPACE_ID.value] = workspace.id
        load_workspaces()
        st.success(f"Çalışma alanı oluşturuldu: {name}")
    except Exception as e:
        logger.error(f"Failed to create workspace '{name}': {e}")
        st.error("Çalışma alanı oluşturulamadı.")


def select_workspace_callback(workspace_id: str) -> None:
    """Switch the active workspace."""
    try:
        db = DatabaseManager()
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
        db = DatabaseManager()
        workspace = db.get_workspace(workspace_id)
        if workspace:
            workspace.name = new_name
            workspace.last_modified = datetime.now()
            db.update_workspace(workspace)
            load_workspaces()
            st.success(f"Çalışma alanı adı güncellendi: {new_name}")
            st.rerun()
    except Exception as e:
        logger.error(f"Failed to rename workspace {workspace_id}: {e}")
        st.error("Çalışma alanı adı değiştirilemedi.")


def delete_workspace_callback(workspace_id: str) -> None:
    """Delete a workspace and all its associated vector data."""
    try:
        db = DatabaseManager()
        workspace = db.get_workspace(workspace_id)
        if workspace:
            chroma = ChromaManager()
            chroma.delete_workspace_data(workspace_id, workspace.name)
            db.delete_workspace(workspace_id)
            
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
        db = DatabaseManager()
        file_service = FileService(db)
        
        with st.spinner("Dosyalar işleniyor..."):
            added_count, successes, errors = file_service.upload_files(
                uploaded_files, workspace, settings["embedding"]
            )
            
            for err in errors:
                st.warning(err)
            for msg in successes:
                st.success(msg)
                
        if added_count > 0:
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
        db = DatabaseManager()
        file_service = FileService(db)
        file_service.delete_file(file_id, active_ws_id)
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
        db = DatabaseManager()
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
            load_workspaces()
            st.rerun()
    except Exception as e:
        logger.error(f"Directory processing callback failure: {e}")
        st.error("Dizin işleme hatası.")


def reset_system_callback() -> None:
    """Perform a global system hard reset."""
    try:
        # 1. Reset Vector Store
        config = AppConfig()
        chroma_path = st.session_state.get(SessionKeys.CHROMA_PATH.value, config.CHROMA_PERSIST_DIR)
        chroma = ChromaManager(persist_directory=chroma_path)
        chroma.hard_reset()
            
        # 2. Reset SQLite DB
        db = DatabaseManager()
        db.reset_system()
        
        # 3. Clear session state
        st.session_state[SessionKeys.ACTIVE_WORKSPACE_ID.value] = None
        st.session_state[SessionKeys.CHAT_HISTORY.value] = []
        st.session_state[SessionKeys.WORKSPACES.value] = []
        
        st.success("Tüm sistem başarıyla sıfırlandı!")
        load_workspaces()
        st.rerun()
    except Exception as e:
        logger.error(f"System reset failure: {e}")
        st.error("Sistem sıfırlanırken kritik bir hata oluştu.")
def save_settings_callback() -> None:
    """Extract current settings from session state and persist to database."""
    try:
        db = DatabaseManager()
        prefs = db.get_preferences()
        
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
        
    except Exception as e:
        logger.error(f"Failed to save settings: {e}")
