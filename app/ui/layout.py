"""Layout components for tilted-T design."""
import streamlit as st


def apply_layout_styles():
    """Apply professional CSS styles aligned with Streamlit's native dark theme."""
    st.markdown("""
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
        padding: 0.4rem 0.8rem !important;
        box-shadow: none !important;
    }
    .stButton > button:hover {
        background: rgba(99, 102, 241, 0.2) !important;
        border-color: rgba(99, 102, 241, 0.5) !important;
        color: #e0e7ff !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.2) !important;
    }
    .stButton > button:active {
        transform: translateY(0px) !important;
        box-shadow: none !important;
    }
    /* Primary action buttons */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #6366f1, #7c3aed) !important;
        border: none !important;
        color: white !important;
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.35) !important;
    }
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #7c3aed, #6366f1) !important;
        box-shadow: 0 6px 20px rgba(99, 102, 241, 0.5) !important;
        transform: translateY(-2px) !important;
    }

    /* ========================
       INPUTS
    ======================== */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background: rgba(255,255,255,0.03) !important;
        border: 1px solid rgba(99, 102, 241, 0.2) !important;
        border-radius: 10px !important;
        color: #e2e8f0 !important;
        font-family: 'Inter', sans-serif !important;
        transition: border-color 0.2s ease !important;
    }
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #6366f1 !important;
        box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.15) !important;
    }
    
    /* Chat Input */
    .stChatInput {
        border-radius: 14px !important;
        border: 1px solid rgba(99, 102, 241, 0.3) !important;
        background: rgba(99, 102, 241, 0.05) !important;
        transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
    }
    .stChatInput:focus-within {
        border-color: #6366f1 !important;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.12) !important;
    }

    /* ========================
       SELECTBOX & NUMBER INPUT
    ======================== */
    .stSelectbox > div > div > div,
    .stNumberInput > div > div > input {
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
        padding: 1rem 1.2rem !important;
        margin-bottom: 0.75rem !important;
        backdrop-filter: blur(10px) !important;
        transition: border-color 0.2s ease !important;
        animation: msgIn 0.3s ease !important;
    }
    div[data-testid="stChatMessage"]:hover {
        border-color: rgba(99, 102, 241, 0.25) !important;
    }
    @keyframes msgIn {
        from { opacity: 0; transform: translateY(6px); }
        to   { opacity: 1; transform: translateY(0); }
    }

    /* ========================
       EXPANDERS - Glassmorphism
    ======================== */
    .stExpander {
        border: 1px solid rgba(99, 102, 241, 0.15) !important;
        border-radius: 12px !important;
        background: rgba(15, 23, 42, 0.6) !important;
        overflow: hidden !important;
    }
    .stExpander:hover {
        border-color: rgba(99, 102, 241, 0.3) !important;
    }
    .stExpander summary {
        font-weight: 500 !important;
        color: #a5b4fc !important;
        padding: 0.75rem 1rem !important;
    }
    .stExpander summary::marker { color: #6366f1; }
    
    /* ========================
       METRIC CARDS
    ======================== */
    div[data-testid="stMetric"] {
        background: rgba(30, 41, 59, 0.7) !important;
        border: 1px solid rgba(99, 102, 241, 0.15) !important;
        border-radius: 14px !important;
        padding: 1rem 1.25rem !important;
        backdrop-filter: blur(8px) !important;
        transition: all 0.2s ease !important;
    }
    div[data-testid="stMetric"]:hover {
        border-color: rgba(99, 102, 241, 0.35) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(0,0,0,0.3) !important;
    }
    div[data-testid="stMetricValue"] {
        color: #c7d2fe !important;
        font-size: 2rem !important;
        font-weight: 700 !important;
    }
    div[data-testid="stMetricLabel"] {
        color: #64748b !important;
        font-size: 0.8rem !important;
        font-weight: 500 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
    }

    /* ========================
       TABS
    ======================== */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(30, 41, 59, 0.6) !important;
        border-radius: 10px !important;
        padding: 0.3rem !important;
        gap: 2px !important;
        border-bottom: none !important;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px !important;
        font-size: 0.85rem !important;
        font-weight: 500 !important;
        color: #64748b !important;
        padding: 0.4rem 1rem !important;
        transition: all 0.2s ease !important;
    }
    .stTabs [aria-selected="true"] {
        background: #6366f1 !important;
        color: white !important;
    }

    /* ========================
       PROGRESS / STATUS BARS
    ======================== */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #6366f1, #a5b4fc) !important;
        border-radius: 4px !important;
    }

    /* ========================
       DIVIDERS
    ======================== */
    hr {
        border-color: rgba(99, 102, 241, 0.1) !important;
        margin: 1rem 0 !important;
    }

    /* ========================
       SUCCESS / ERROR / WARNING boxes
    ======================== */
    div[data-testid="stAlert"] {
        border-radius: 12px !important;
        border-left-width: 4px !important;
        backdrop-filter: blur(8px) !important;
    }

    /* ========================
       FILE UPLOADER
    ======================== */
    section[data-testid="stFileUploaderDropzone"] {
        background: rgba(99, 102, 241, 0.04) !important;
        border: 2px dashed rgba(99, 102, 241, 0.3) !important;
        border-radius: 14px !important;
        transition: all 0.2s ease !important;
    }
    section[data-testid="stFileUploaderDropzone"]:hover {
        background: rgba(99, 102, 241, 0.1) !important;
        border-color: #6366f1 !important;
    }

    /* ========================
       RADIO / CHECKBOX
    ======================== */
    .stRadio > div { gap: 0.5rem !important; }
    .stRadio > div > label {
        background: rgba(255,255,255,0.02) !important;
        border: 1px solid rgba(99, 102, 241, 0.15) !important;
        border-radius: 8px !important;
        padding: 0.4rem 0.8rem !important;
        transition: all 0.2s ease !important;
        font-size: 0.85rem !important;
    }
    .stRadio > div > label:hover {
        border-color: rgba(99, 102, 241, 0.4) !important;
        background: rgba(99, 102, 241, 0.07) !important;
    }

    /* ========================
       INPUT-BAR (FIXED FOOTER)
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
        box-shadow: 0 8px 32px rgba(0,0,0,0.4), 0 0 0 1px rgba(99,102,241,0.1);
        backdrop-filter: blur(16px);
    }

    /* ========================
       CAPTAIN HINT - Empty State
    ======================== */
    .empty-state-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        min-height: 45vh;
        opacity: 0;
        animation: fadeUp 0.6s ease 0.2s forwards;
    }
    @keyframes fadeUp {
        from { opacity:0; transform: translateY(20px); }
        to   { opacity:1; transform: translateY(0); }
    }
    </style>
    """, unsafe_allow_html=True)

def render_tilted_t_layout(chat_area, input_area, sidebar=None):
    """
    Render tilted-T layout.
    
    Structure:
    - Top: Wide chat message area
    - Bottom: Wide input bar
    - Right: Optional sidebar
    """
    # Main columns
    if sidebar:
        main_col, side_col = st.columns([4, 1])
    else:
        main_col = st.container()
    
    with main_col:
        # Chat area (top - takes most space)
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        chat_area()
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Input bar (bottom - wide)
        st.markdown('<div class="input-bar-container">', unsafe_allow_html=True)
        input_area()
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Sidebar
    if sidebar:
        with side_col:
            sidebar()


def render_simple_layout(sidebar_content, main_content):
    """Render simple layout with sidebar."""
    with st.sidebar:
        sidebar_content()
    
    main_content()
