import sys
from pathlib import Path

# Fix for ModuleNotFoundError: Ensure root directory is in sys.path
root_path = str(Path(__file__).parent.parent)
if root_path not in sys.path:
    sys.path.insert(0, root_path)

import streamlit as st

from app.core.config import AppConfig
from app.core.constants import SessionKeys
from app.core.logger import logger
from app.core.router import resolve_page
from app.ui.callbacks import load_workspaces
from app.ui.header import render_header
from app.ui.layout import apply_layout_styles

# Configure Streamlit page
st.set_page_config(
    page_title="Doc Analyzer Pro",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def init_session_state() -> None:
    """
    Initialize session state variables with persisted values from DB or defaults.
    Loads configuration from database and merges with application defaults.
    """
    logger.info("Initializing session state")

    try:
        from app.core.container import get_database, get_chroma
        from app.core.exceptions import DatabaseError
        db = get_database()
        chroma_manager = get_chroma()
        prefs = db.preferences.get()
    except DatabaseError as e:
        logger.error(f"Failed to load preferences from DB: {e}")
        from app.core.models import UserPreferences
        prefs = UserPreferences()

    config = AppConfig()

    # Base defaults
    defaults = {
        SessionKeys.ACTIVE_WORKSPACE_ID.value: None,
        SessionKeys.WORKSPACES.value: [],
        SessionKeys.CHAT_HISTORY.value: [],
        SessionKeys.SIDEBAR_OPEN.value: config.SIDEBAR_DEFAULT_OPEN,
        SessionKeys.CURRENT_PAGE.value: config.DEFAULT_PAGE,
        SessionKeys.PREFERENCES.value: prefs,
        # LLM defaults
        SessionKeys.LLM_MODEL.value: config.LLM_MODEL,
        SessionKeys.LLM_BASE_URL.value: config.LLM_BASE_URL,
        SessionKeys.OLLAMA_API_KEY.value: config.OLLAMA_API_KEY,
        SessionKeys.LLM_TEMPERATURE.value: config.LLM_TEMPERATURE,
        SessionKeys.LAST_ENDPOINT_TYPE.value: config.DEFAULT_LLM_PROVIDER,
        # Embedding defaults
        SessionKeys.USE_HUGGINGFACE.value: config.USE_HUGGINGFACE,
        SessionKeys.EMBED_MODEL.value: config.EMBED_MODEL,
        SessionKeys.OLLAMA_URL.value: config.OLLAMA_BASE_URL,
        SessionKeys.HF_EMBED_MODEL.value: config.HF_EMBED_MODEL,
        # Data & System defaults
        SessionKeys.DATA_DIR.value: config.DATA_DIR,
        SessionKeys.CHROMA_PATH.value: config.CHROMA_PERSIST_DIR,
        SessionKeys.CHUNK_SIZE.value: config.CHUNK_SIZE,
        SessionKeys.CHUNK_OVERLAP.value: config.CHUNK_OVERLAP,
        SessionKeys.THEME.value: "dark",
    }

    # Sync global config from DB via container
    from app.core.container import get_config
    config_obj = get_config()
    if prefs.config:
        config_obj.sync_with_db(prefs.config)
        logger.info("Global AppConfig synchronized with DB preferences during init")

    # Finalize session state from synced config
    defaults[SessionKeys.DATA_DIR.value] = config_obj.DATA_DIR
    defaults[SessionKeys.CHROMA_PATH.value] = config_obj.CHROMA_PERSIST_DIR
    defaults[SessionKeys.CHUNK_SIZE.value] = config_obj.CHUNK_SIZE
    defaults[SessionKeys.CHUNK_OVERLAP.value] = config_obj.CHUNK_OVERLAP
    defaults[SessionKeys.LLM_MODEL.value] = config_obj.LLM_MODEL
    defaults[SessionKeys.LLM_BASE_URL.value] = config_obj.LLM_BASE_URL
    defaults[SessionKeys.OLLAMA_API_KEY.value] = config_obj.OLLAMA_API_KEY
    defaults[SessionKeys.LLM_TEMPERATURE.value] = config_obj.LLM_TEMPERATURE
    defaults[SessionKeys.LAST_ENDPOINT_TYPE.value] = config_obj.DEFAULT_LLM_PROVIDER
    defaults[SessionKeys.EMBED_MODEL.value] = config_obj.EMBED_MODEL
    defaults[SessionKeys.USE_HUGGINGFACE.value] = config_obj.USE_HUGGINGFACE
    defaults[SessionKeys.HF_EMBED_MODEL.value] = config_obj.HF_EMBED_MODEL
    defaults[SessionKeys.OLLAMA_URL.value] = config_obj.OLLAMA_BASE_URL

    # Locale / i18n
    from app.core.locales import get_locale
    defaults["locale"] = get_locale("tr")

    for key, value in defaults.items():
        if key not in st.session_state or st.session_state[key] is None:
            st.session_state[key] = value

    logger.debug(f"Session state initialized with {len(defaults)} keys")


# Define Navigation Pages (Global for st.switch_page compatibility)
def show_chat():
    from app.core.constants import UIPages
    resolve_page(UIPages.CHAT, {})

def show_docs():
    from app.core.constants import UIPages
    resolve_page(UIPages.DOCUMENTS, {})

def show_analysis():
    from app.core.constants import UIPages
    resolve_page(UIPages.ANALYSIS, {})

def show_knowledge():
    from app.core.constants import UIPages
    resolve_page(UIPages.KNOWLEDGE, {})

def show_settings():
    from app.core.constants import UIPages
    resolve_page(UIPages.SETTINGS, {})

def main() -> None:
    """
    Main application entry point with Sidebar-less Navigation.
    """
    logger.info("Starting Doc Analyzer Pro application")

    # 1. Initialize session state & Styles
    init_session_state()
    apply_layout_styles()

    # 2. Define Sidebar-less Navigation
    L = st.session_state.locale

    pages = [
        st.Page(show_chat, title=L.chat.title, icon="💬"),
        st.Page(show_docs, title=L.library.title, icon="📚"),
        st.Page(show_analysis, title=L.analysis.title, icon="📊"),
        st.Page(show_knowledge, title=L.knowledge.title, icon="⭐"),
        st.Page(show_settings, title=L.settings.title, icon="⚙️"),
    ]

    # Store pages in session state for cross-module st.switch_page access
    from app.core.constants import UIPages
    st.session_state["NAV_MAP"] = {
        UIPages.CHAT: pages[0],
        UIPages.DOCUMENTS: pages[1],
        UIPages.ANALYSIS: pages[2],
        UIPages.KNOWLEDGE: pages[3],
        UIPages.SETTINGS: pages[4],
    }

    # Initialize Sidebar-less Nav
    pg = st.navigation(pages, position="hidden")

    # 3. Header (Internal Nav) & Workspaces
    render_header()
    load_workspaces()

    # 4. Render the active page
    pg.run()

    logger.info("Page routing managed by st.navigation")


if __name__ == "__main__":
    main()
