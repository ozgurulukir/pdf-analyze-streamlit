"""Header and navigation components."""
import streamlit as st
from streamlit_option_menu import option_menu


def render_header(
    title: str = "PDF Analyzer Pro",
    on_theme_toggle: callable = None,
    on_settings: callable = None
):
    """Render app header with premium styling."""
    st.markdown(f"""
    <div style="
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.75rem 1.5rem;
        background: rgba(15, 23, 42, 0.7);
        border: 1px solid rgba(99, 102, 241, 0.15);
        border-radius: 16px;
        margin-bottom: 1.25rem;
        backdrop-filter: blur(12px);
    ">
        <div style="display:flex; align-items:center; gap:12px;">
            <div style="
                width: 38px; height: 38px;
                background: linear-gradient(135deg, #6366f1, #7c3aed);
                border-radius: 10px;
                display: flex; align-items: center; justify-content: center;
                font-size: 1.2rem;
                box-shadow: 0 4px 12px rgba(99, 102, 241, 0.35);
            ">🎯</div>
            <div>
                <div style="
                    font-size: 1.05rem; font-weight: 700;
                    background: linear-gradient(to right, #a5b4fc, #e0e7ff);
                    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                    letter-spacing: -0.02em;
                ">{title}</div>
                <div style="font-size: 0.7rem; color: #475569; margin-top: -2px;">AI-Powered Document Intelligence</div>
            </div>
        </div>
        <div style="display:flex; align-items:center; gap:8px;">
            <div style="
                font-size: 0.7rem; font-weight: 600;
                color: #10b981;
                background: rgba(16, 185, 129, 0.1);
                border: 1px solid rgba(16, 185, 129, 0.25);
                border-radius: 20px; padding: 3px 10px;
                letter-spacing: 0.05em;
            ">● LIVE</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Header action buttons (compact)
    _, col_btns = st.columns([6, 1])
    with col_btns:
        cols = st.columns(2)
        with cols[0]:
            if st.button("⚙️", key="settings_btn", help="Ayarlar", use_container_width=True):
                if on_settings: on_settings()
        with cols[1]:
            if st.button("ℹ️", key="help_btn", help="Yardım", use_container_width=True):
                st.toast("Çalışma alanı seçin ve belgelerinizi yükleyin!", icon="ℹ️")


def render_navigation(
    current_page: str,
    on_change: callable = None
):
    """Render main navigation menu with indigo theme."""
    
    pages = ["💬 Chat", "📁 Belgeler", "📊 Analiz", "⚙️ Ayarlar"]
    icons = ["chat", "folder", "chart-bar", "cog"]
    
    try:
        default_index = pages.index(current_page)
    except ValueError:
        default_index = 0
    
    selected = option_menu(
        menu_title=None,
        options=pages,
        icons=icons,
        orientation="horizontal",
        default_index=default_index,
        styles={
            "container": {
                "padding": "0.35rem",
                "background-color": "rgba(15, 23, 42, 0.8)",
                "border": "1px solid rgba(99, 102, 241, 0.12)",
                "border-radius": "14px",
                "margin-top": "0.5rem",
                "backdrop-filter": "blur(10px)",
            },
            "nav-link": {
                "font-size": "0.82rem",
                "font-weight": "500",
                "color": "#64748b",
                "text-align": "center",
                "margin": "0 2px",
                "--hover-color": "rgba(99, 102, 241, 0.1)",
                "border-radius": "10px",
                "transition": "all 0.2s ease",
            },
            "nav-link-selected": {
                "background": "linear-gradient(135deg, #6366f1, #7c3aed)",
                "color": "white",
                "font-weight": "600",
                "box-shadow": "0 4px 16px rgba(99, 102, 241, 0.4)",
            },
        }
    )
    
    return selected
