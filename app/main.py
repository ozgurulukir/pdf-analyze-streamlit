import sys
from pathlib import Path

# Fix for ModuleNotFoundError: Ensure root directory is in sys.path
root_path = str(Path(__file__).parent.parent)
if root_path not in sys.path:
    sys.path.insert(0, root_path)

import streamlit as st  # noqa: E402

from app.core.config import AppConfig  # noqa: E402
from app.core.constants import SessionKeys  # noqa: E402
from app.core.logger import logger  # noqa: E402
from app.core.router import resolve_page  # noqa: E402
from app.ui.callbacks import load_workspaces  # noqa: E402
from app.ui.header import render_header  # noqa: E402
from app.ui.layout import apply_layout_styles  # noqa: E402

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

    Strategy:
    - On a fresh run (after reset or first boot), '_state_initialized' is absent
      → write ALL config defaults unconditionally so widgets never start empty.
    - On a normal rerun, '_state_initialized' is present
      → only fill in truly missing / conceptually-empty slots.
    """
    logger.info("Initializing session state")

    # ── 1. Detect whether this is a fresh run (post-reset or first boot)
    is_fresh_run = "_state_initialized" not in st.session_state

    # ── 2. Load preferences from DB
    from app.core.exceptions import DatabaseError
    try:
        from app.core.container import get_database
        db = get_database()
        prefs = db.preferences.get()
    except DatabaseError as e:
        logger.error(f"Failed to load preferences from DB: {e}")
        from app.core.models import UserPreferences
        prefs = UserPreferences()

    # ── 3. Start with synchronized AppConfig from Container
    from app.core.container import get_config
    config_obj = get_config()

    # The container already synchronized config_obj with DB preferences during its own init.
    # However, we ensure it matches the user's specific prefs object here if needed.
    if prefs.config:
        config_obj.sync_with_db(prefs.config)
        logger.info("Global AppConfig synchronized with DB preferences during init_session_state")

    defaults = {
        SessionKeys.ACTIVE_WORKSPACE_ID.value: None,
        SessionKeys.WORKSPACES.value: [],
        SessionKeys.CHAT_HISTORY.value: [],
        SessionKeys.SIDEBAR_OPEN.value: config_obj.SIDEBAR_DEFAULT_OPEN,
        SessionKeys.CURRENT_PAGE.value: config_obj.DEFAULT_PAGE,
        SessionKeys.PREFERENCES.value: prefs,
        # LLM
        SessionKeys.LLM_MODEL.value: config_obj.LLM_MODEL,
        SessionKeys.LLM_BASE_URL.value: config_obj.LLM_BASE_URL,
        SessionKeys.OLLAMA_API_KEY.value: config_obj.OLLAMA_API_KEY,
        SessionKeys.LLM_TEMPERATURE.value: config_obj.LLM_TEMPERATURE,
        SessionKeys.LAST_ENDPOINT_TYPE.value: config_obj.DEFAULT_LLM_PROVIDER,
        # Embedding
        SessionKeys.USE_HUGGINGFACE.value: config_obj.USE_HUGGINGFACE,
        SessionKeys.EMBED_MODEL.value: config_obj.EMBED_MODEL,
        SessionKeys.OLLAMA_URL.value: config_obj.OLLAMA_BASE_URL,
        SessionKeys.HF_EMBED_MODEL.value: config_obj.HF_EMBED_MODEL,
        # Data & System
        SessionKeys.DATA_DIR.value: config_obj.DATA_DIR,
        SessionKeys.CHROMA_PATH.value: config_obj.CHROMA_PERSIST_DIR,
        SessionKeys.CHUNK_SIZE.value: config_obj.CHUNK_SIZE,
        SessionKeys.CHUNK_OVERLAP.value: config_obj.CHUNK_OVERLAP,
        SessionKeys.THEME.value: "dark",
        SessionKeys.OLLAMA_LLM_MODELS.value: [],
        SessionKeys.OLLAMA_EMBED_MODELS.value: [],
        "use_custom_llm_flag": False,
        "_temp_embed_type": "hf" if config_obj.USE_HUGGINGFACE else "ollama",
    }

    # ── 5. Model lists (UI selectbox source)
    from app.core.config import get_ollama_llm_models, get_ollama_models
    llm_models = get_ollama_llm_models(config_obj.OLLAMA_BASE_URL)
    embed_models = get_ollama_models(config_obj.OLLAMA_BASE_URL)

    # ── FALLBACK: Ensure lists are never empty so UI selectboxes don't break
    if not llm_models:
        llm_models = [{"label": config_obj.LLM_MODEL, "value": config_obj.LLM_MODEL}]
    if not embed_models:
        embed_models = [{"label": config_obj.EMBED_MODEL, "value": config_obj.EMBED_MODEL}]

    defaults[SessionKeys.OLLAMA_LLM_MODELS.value] = llm_models
    defaults[SessionKeys.OLLAMA_EMBED_MODELS.value] = embed_models

    # ── 6. Locale
    from app.core.locales import get_locale
    defaults["locale"] = get_locale("tr")

    # ── 7. Write to session state
    # Config keys that must never hold an empty/whitespace string
    config_keys = {
        SessionKeys.LLM_MODEL.value,
        SessionKeys.LLM_BASE_URL.value,
        SessionKeys.OLLAMA_API_KEY.value,
        SessionKeys.LAST_ENDPOINT_TYPE.value,
        SessionKeys.EMBED_MODEL.value,
        SessionKeys.OLLAMA_URL.value,
        SessionKeys.HF_EMBED_MODEL.value,
        SessionKeys.DATA_DIR.value,
        SessionKeys.CHROMA_PATH.value,
        SessionKeys.CHUNK_SIZE.value,
        SessionKeys.CHUNK_OVERLAP.value,
        "_temp_embed_type",
    }

    for key, value in defaults.items():
        if is_fresh_run:
            # Post-reset or first boot: force-write everything so widgets
            # never display stale/empty values from Streamlit's widget cache.
            st.session_state[key] = value
            logger.debug(f"[fresh] State forced for {key}")
        else:
            current = st.session_state.get(key)
            is_missing = key not in st.session_state or current is None
            is_empty = key in config_keys and isinstance(current, str) and current.strip() == ""
            if is_missing or is_empty:
                st.session_state[key] = value
                logger.debug(f"[rerun] State filled for {key}")

    # Mark as initialized so subsequent reruns skip force-write
    st.session_state["_state_initialized"] = True
    logger.debug(f"Session state initialized ({len(defaults)} keys, fresh={is_fresh_run})")


# Define Navigation Pages (Global for st.switch_page compatibility)
def show_chat():
    from app.core.constants import UIPages
    resolve_page(UIPages.CHAT)

def show_docs():
    from app.core.constants import UIPages
    resolve_page(UIPages.DOCUMENTS)

def show_analysis():
    from app.core.constants import UIPages
    resolve_page(UIPages.ANALYSIS)

def show_knowledge():
    from app.core.constants import UIPages
    resolve_page(UIPages.KNOWLEDGE)

def show_settings():
    from app.core.constants import UIPages
    resolve_page(UIPages.SETTINGS)

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
