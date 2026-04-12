"""Layout components for modern Streamlit design."""

import streamlit as st


def apply_layout_styles():
    """Apply professional CSS styles for the Canvas (Sidebar-less) experience."""
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
       HIDE SIDEBAR COMPLETELY
    ======================== */
    [data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"] {
        display: none !important;
    }

    /* ========================
       CUSTOM SCROLLBAR
    ======================== */
    ::-webkit-scrollbar { width: 5px; height: 5px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: #4f46e5; border-radius: 10px; }
    ::-webkit-scrollbar-thumb:hover { background: #6366f1; }

    /* ========================
       MAIN APP BACKGROUND & CANVAS
    ======================== */
    .stApp {
        background: #0f172a !important;
    }
    .main .block-container {
        padding-top: 5rem !important; /* Space for Top-Nav */
        padding-bottom: 2rem !important;
        max-width: 900px; /* Focused Canvas Width */
        margin: 0 auto;
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
    .stChatInput textarea {
        background: rgba(255,255,255,0.03) !important;
        border: 1px solid rgba(99, 102, 241, 0.2) !important;
        border-radius: 12px !important;
    }

    /* ========================
       CHAT MESSAGES
    ======================== */
    div[data-testid="stChatMessage"] {
        background: rgba(30, 41, 59, 0.6) !important;
        border: 1px solid rgba(99, 102, 241, 0.1) !important;
        border-radius: 18px !important;
        backdrop-filter: blur(12px) !important;
        margin-bottom: 1rem !important;
        padding: 1.25rem !important;
    }

    /* ========================
       SOURCE CARDS
    ======================== */
    .source-card {
        background: rgba(99, 102, 241, 0.05);
        border: 1px solid rgba(99, 102, 241, 0.2);
        border-radius: 8px;
        padding: 6px 10px;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        margin-right: 6px;
        margin-top: 6px;
        font-size: 0.75rem;
        color: #a5b4fc;
        transition: all 0.2s;
    }
    .source-card:hover {
        background: rgba(99, 102, 241, 0.15);
        border-color: rgba(99, 102, 241, 0.4);
        transform: translateY(-1px);
    }

    /* ========================
       TOP NAV STYLING
    ======================== */
    .top-nav {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        height: 64px;
        background: rgba(15, 23, 42, 0.8);
        backdrop-filter: blur(20px);
        border-bottom: 1px solid rgba(99, 102, 241, 0.15);
        z-index: 1000;
        display: flex;
        align-items: center;
        padding: 0 2rem;
        justify-content: space-between;
    }

    /* ========================
       PREMIUM KNOWLEDGE BASE COMPONENTS
    ======================== */
    .kb-tag {
        background-color: rgba(99, 102, 241, 0.1) !important;
        color: #818cf8 !important;
        padding: 4px 12px !important;
        border-radius: 20px !important;
        font-size: 0.7rem !important;
        margin-right: 8px !important;
        border: 1px solid rgba(99, 102, 241, 0.2) !important;
        font-weight: 600 !important;
        display: inline-block !important;
        margin-bottom: 8px !important;
        transition: all 0.3s ease;
    }
    .kb-tag:hover {
        background-color: rgba(99, 102, 241, 0.2) !important;
        border-color: rgba(99, 102, 241, 0.4) !important;
    }

    .kb-header-box {
        background: linear-gradient(90deg, rgba(30, 41, 59, 0.8), rgba(15, 23, 42, 0.8));
        padding: 24px;
        border-radius: 12px;
        border-left: 6px solid #6366f1;
        margin-bottom: 30px;
        backdrop-filter: blur(10px);
    }

    .kb-answer-text {
        color: #cbd5e1 !important;
        line-height: 1.7 !important;
        font-size: 0.95rem !important;
    }

    .kb-empty-state {
        text-align: center;
        padding: 60px;
        color: #475569;
        font-style: italic;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )


def render_canvas_layout(main_content):
    """
    Render centered canvas layout.
    """
    st.container().write("") # Top spacing
    main_content()
