"""Layout components for tilted-T design."""
import streamlit as st


def apply_layout_styles():
    """Apply professional CSS styles for the app."""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

    :root {
        --primary-color: #6366f1;
        --secondary-color: #4f46e5;
        --background-gradient: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        --card-bg: rgba(255, 255, 255, 0.05);
        --glass-border: rgba(255, 255, 255, 0.1);
    }

    /* Main background */
    .stApp {
        background: var(--background-gradient);
        color: #f8fafc;
        font-family: 'Inter', sans-serif;
    }
    
    /* Header - Modern look */
    .stHeader {
        background: transparent !important;
    }
    
    /* Chat container - High quality glassmorphism */
    .chat-container {
        height: calc(100vh - 220px);
        overflow-y: auto;
        padding: 1.5rem;
        background: var(--card-bg);
        backdrop-filter: blur(12px);
        border-radius: 20px;
        border: 1px solid var(--glass-border);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        margin-bottom: 2rem;
    }
    
    /* Input bar - T-shape bottom container */
    .input-bar-container {
        position: fixed;
        bottom: 20px;
        left: 50%;
        transform: translateX(-50%);
        width: 85%;
        background: rgba(30, 41, 59, 0.8);
        backdrop-filter: blur(16px);
        border-radius: 24px;
        padding: 1rem 1.5rem;
        border: 1px solid var(--glass-border);
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
        z-index: 1000;
    }
    
    /* Chat message bubble styling - Premium style */
    .stChatMessage {
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid var(--glass-border);
        border-radius: 12px !important;
        padding: 12px 16px !important;
        margin-bottom: 12px !important;
        transition: all 0.2s ease;
    }
    
    .stChatMessage:hover {
        background: rgba(255, 255, 255, 0.07) !important;
    }
    
    /* Buttons - Gradient and Hover effects */
    .stButton > button {
        background: linear-gradient(90deg, #6366f1 0%, #4f46e5 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.6rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .stButton > button:hover {
        transform: scale(1.02) translateY(-2px);
        box-shadow: 0 10px 20px rgba(79, 70, 229, 0.4);
        background: linear-gradient(90deg, #4f46e5 0%, #6366f1 100%);
    }
    
    /* Sidebar styling - Dark mode elegance */
    section[data-testid="stSidebar"] {
        background-color: #0b0f19 !important;
        border-right: 1px solid var(--glass-border);
    }
    
    /* Metric styling */
    div[data-testid="stMetric"] {
        background: var(--card-bg);
        padding: 1rem;
        border-radius: 16px;
        border: 1px solid var(--glass-border);
    }
    
    /* Text Input styling */
    .stTextInput > div > div > input {
        background-color: rgba(255, 255, 255, 0.05) !important;
        color: white !important;
        border: 1px solid var(--glass-border) !important;
        border-radius: 12px !important;
    }

    /* Custom scrollbar - Minimalist */
    ::-webkit-scrollbar {
        width: 6px;
    }
    ::-webkit-scrollbar-track {
        background: transparent;
    }
    ::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.2);
        border-radius: 10px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(255, 255, 255, 0.4);
    }

    /* Animations */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .stChatMessage {
        animation: fadeIn 0.4s ease-out forwards;
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
