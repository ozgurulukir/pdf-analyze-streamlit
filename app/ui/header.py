"""Header and navigation components."""
import streamlit as st
from streamlit_option_menu import option_menu


def render_header(
    title: str = "PDF Analyzer Pro",
    on_theme_toggle: callable = None,
    on_settings: callable = None
):
    """Render app header with title, theme toggle, and settings."""
    
    # Header container
    with st.container():
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        
        with col1:
            st.markdown(f"### 🎯 {title}")
        
        with col2:
            # Theme toggle (placeholder - Streamlit themes are set via config)
            theme = st.session_state.get("theme", "light")
            if st.button("🌙" if theme == "light" else "☀️", key="theme_toggle", help="Tema değiştir"):
                st.session_state.theme = "dark" if theme == "light" else "light"
                if on_theme_toggle:
                    on_theme_toggle()
        
        with col3:
            # Settings button
            if st.button("⚙️ Ayarlar", key="settings_btn"):
                if on_settings:
                    on_settings()
        
        with col4:
            # Help/Info button
            if st.button("ℹ️ Bilgi", key="help_btn"):
                st.info("""
                **Kullanım:**
                1. Çalışma alanı oluşturun veya seçin
                2. Belgeleri yükleyin
                3. Belgeler işlenirken bekleyin
                4. Belgeler hakkında sorular sorun
                """)


def render_tabs(
    tabs: list,
    default_index: int = 0
) -> str:
    """Render horizontal tabs using option_menu."""
    
    selected = option_menu(
        menu_title=None,
        options=tabs,
        icons=["chat", "folder", "chart-bar", "cog"],
        orientation="horizontal",
        default_index=default_index,
        styles={
            "container": {"padding": "0.5rem"},
            "nav-link": {
                "font-size": "1rem",
                "border-radius": "0.5rem",
            },
        }
    )
    
    return selected


def render_navigation(
    current_page: str,
    on_change: callable = None
):
    """Render main navigation menu."""
    
    pages = [
        "💬 Chat",
        "📁 Belgeler",
        "📊 Dashboard",
        "⚙️ Ayarlar"
    ]
    
    icons = ["chat", "folder", "chart-bar", "cog"]
    
    selected = option_menu(
        menu_title="Menu",
        options=pages,
        icons=icons,
        orientation="horizontal",
        default_index=pages.index(current_page) if current_page in pages else 0,
        styles={
            "container": {"padding": "0.5rem"},
            "nav-link": {
                "font-size": "1rem",
                "border-radius": "0.5rem",
            },
            "nav-link-selected": {
                "background-color": "#FF4B4B",
                "color": "white",
            },
        }
    )
    
    return selected


def render_sidebar_toggle_button(is_open: bool, on_toggle: callable):
    """Render sidebar toggle button."""
    
    if is_open:
        if st.button("◀️ Sidebarı Kapat", key="sidebar_toggle"):
            on_toggle(False)
    else:
        if st.button("▶️ Sidebarı Aç", key="sidebar_toggle"):
            on_toggle(True)


def render_settings_modal(is_open: bool, on_close: callable):
    """Render settings modal."""
    
    if not is_open:
        return
    
    with st.container():
        st.markdown("### ⚙️ Ayarlar")
        
        # Model selection
        model = st.selectbox(
            "🤖 Model",
            ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"],
            index=0
        )
        
        # Retriever
        retriever = st.selectbox(
            "🔍 Arama Yöntemi",
            ["similarity", "mmr"],
            index=0
        )
        
        # Chunk size
        chunk_size = st.slider(
            "📝 Chunk Boyutu",
            min_value=500,
            max_value=2000,
            value=1000,
            step=100
        )
        
        # Number of results
        k = st.slider(
            "📊 Sonuç Sayısı",
            min_value=1,
            max_value=10,
            value=4
        )
        
        st.divider()
        
        # Close button
        if st.button("Kapat"):
            on_close()


def render_confirm_dialog(
    is_open: bool,
    title: str,
    message: str,
    on_confirm: callable,
    on_cancel: callable
):
    """Render confirmation dialog."""
    
    if not is_open:
        return
    
    st.warning(f"### ⚠️ {title}")
    st.write(message)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Evet", key="confirm_yes", use_container_width=True):
            on_confirm()
    with col2:
        if st.button("❌ Hayır", key="confirm_no", use_container_width=True):
            on_cancel()
