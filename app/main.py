"""Main application orchestrator - PDF Analyzer Pro."""

import os
import sys

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

from app.core import DatabaseManager, UserPreferences, get_job_queue
from app.core.config import AppConfig
from app.core.constants import SessionKeys
from app.core.logger import logger
from app.core.router import resolve_page
from app.ui.callbacks import load_workspaces
from app.ui.header import render_header, render_navigation
from app.ui.layout import apply_layout_styles
from app.ui.sidebar import render_sidebar_content

# Configure Streamlit page
st.set_page_config(
    page_title="PDF Analyzer Pro",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)


def init_session_state() -> None:
    """
    Initialize session state variables with persisted values from DB or defaults.
    Loads configuration from database and merges with application defaults.
    """
    logger.info("Initializing session state")

    db = DatabaseManager()
    prefs = db.get_preferences()
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

    # Merge persisted config into defaults
    if prefs.config:
        for key_name, val in prefs.config.items():
            if key_name in defaults:
                defaults[key_name] = val

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    logger.debug(f"Session state initialized with {len(defaults)} keys")


def main() -> None:
    """
    Main application entry point.

    Execution flow:
    1. Initialize session state
    2. Apply layout styles
    3. Render header and navigation
    4. Load workspaces
    5. Render sidebar
    6. Route to the selected page
    """
    logger.info("Starting PDF Analyzer Pro application")

    # 1. Initialize session state
    init_session_state()
    apply_layout_styles()

    # 2. Header & Page Navigation
    render_header()
    current_page = st.session_state[SessionKeys.CURRENT_PAGE.value]
    selected_page = render_navigation(current_page)
    st.session_state[SessionKeys.CURRENT_PAGE.value] = selected_page

    # 3. Sidebar & Global State
    load_workspaces()
    settings = render_sidebar_content()

    # 4. Dynamic Page Routing (using router module)
    resolve_page(selected_page, settings)

    logger.info(f"Page '{selected_page}' rendered successfully")


if __name__ == "__main__":
    main()
