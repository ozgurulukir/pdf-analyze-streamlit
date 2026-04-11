"""Layout components for modern Streamlit design."""

import streamlit as st


def apply_layout_styles():
    """Apply professional CSS styles aligned with Streamlit's native dark theme."""
    st.markdown(
        """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* ========================
       GLOBAL RESET & TYPOGRAPHY
    ======================== */
    html, body, [class*="css"], .stApp {
        font-family: 'Inter', sans-serif !important;
        letter-spacing: -0.01em;
    }

    /* ========================
       CUSTOM SCROLLBAR
    ======================== */
    ::-webkit-scrollbar { width: 5px; height: 5px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: #4f46e5; border-radius: 10px; }
    ::-webkit-scrollbar-thumb:hover { background: #6366f1; }

    /* ========================
       SIDEBAR PREMIUM POLISH
    ======================== */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0a0f1e 0%, #0f172a 100%) !important;
        border-right: 1px solid rgba(99, 102, 241, 0.15) !important;
    }
    section[data-testid="stSidebar"] > div {
        padding-top: 1rem !important;
    }

    /* ========================
       MAIN APP BACKGROUND
    ======================== */
    .stApp {
        background: #0f172a !important;
    }
    .main .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 2rem !important;
        max-width: 1100px;
    }

    /* ========================
       NATIVE CONTAINERS BORDER
    ======================== */
    div[data-testid="stVerticalBlockBorderWrapper"] > div {
        border-color: rgba(99, 102, 241, 0.15) !important;
        background: rgba(30, 41, 59, 0.4) !important;
        backdrop-filter: blur(8px) !important;
        border-radius: 14px !important;
    }

    /* ========================
       BUTTONS - Premium Polish
    ======================== */
    .stButton > button {
        border-radius: 10px !important;
        font-weight: 500 !important;
        font-size: 0.85rem !important;
        transition: all 0.2s ease !important;
        border: 1px solid rgba(99, 102, 241, 0.25) !important;
        background: rgba(99, 102, 241, 0.08) !important;
        color: #a5b4fc !important;
    }
    .stButton > button:hover {
        background: rgba(99, 102, 241, 0.2) !important;
        border-color: rgba(99, 102, 241, 0.5) !important;
        color: #e0e7ff !important;
    }

    /* Primary action buttons */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #6366f1, #7c3aed) !important;
        border: none !important;
        color: white !important;
    }

    /* ========================
       INPUTS
    ======================== */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stChatInput {
        background: rgba(255,255,255,0.03) !important;
        border: 1px solid rgba(99, 102, 241, 0.2) !important;
        border-radius: 10px !important;
    }

    /* ========================
       CHAT MESSAGES
    ======================== */
    div[data-testid="stChatMessage"] {
        background: rgba(30, 41, 59, 0.7) !important;
        border: 1px solid rgba(99, 102, 241, 0.12) !important;
        border-radius: 16px !important;
        backdrop-filter: blur(10px) !important;
        margin-bottom: 0.75rem !important;
    }

    /* ========================
       INPUT-BAR (FIXED FOOTER) - If used
    ======================== */
    .input-bar-container {
        position: fixed;
        bottom: 2rem;
        left: 50%;
        transform: translateX(-50%);
        width: 75%;
        z-index: 1000;
        background: rgba(15, 23, 42, 0.85);
        border-radius: 20px;
        border: 1px solid rgba(99, 102, 241, 0.25);
        padding: 10px 20px;
        backdrop-filter: blur(16px);
    }
    </style>
    """,
        unsafe_allow_html=True,
    )


def render_tilted_t_layout(chat_area, input_area, sidebar=None):
    """
    Render modernized tilted-T layout.
    """
    if sidebar:
        main_col, side_col = st.columns([4, 1])
    else:
        main_col = st.container()

    with main_col:
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        chat_area()
        st.markdown("</div>", unsafe_allow_html=True)

        # In modern Streamlit, st.chat_input is fixed by default.
        # But if we want a custom container:
        input_area()

    if sidebar:
        with side_col:
            sidebar()


def render_simple_layout(sidebar_content, main_content):
    """Render simple layout with sidebar."""
    with st.sidebar:
        sidebar_content()

    main_content()
