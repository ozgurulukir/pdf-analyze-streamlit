"""Header component for application navigation."""

import streamlit as st

from app.core.constants import SessionKeys


def render_header():
    """Render a premium application header with popover info and navigation."""
    from app.core.constants import UIPages

    # Map display names to UIPages identifiers
    tabs = {
        f"💬 {UIPages.CHAT}": UIPages.CHAT,
        f"📚 {UIPages.DOCUMENTS}": UIPages.DOCUMENTS,
        f"📊 {UIPages.ANALYSIS}": UIPages.ANALYSIS,
        f"⚙️ {UIPages.SETTINGS}": UIPages.SETTINGS,
    }

    current_page = st.session_state.get(
        SessionKeys.CURRENT_PAGE.value, list(tabs.keys())[0]
    )

    # Header Container
    st.markdown(
        """
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; padding: 0.5rem 0;">
            <div style="display: flex; align-items: center; gap: 12px;">
                <div style="font-size: 1.8rem;">💎</div>
                <div>
                    <div style="font-weight: 800; font-size: 1.2rem; color: #fff; line-height: 1;">DOC ANALYZER PRO</div>
                    <div style="font-size: 0.75rem; color: #6366f1; font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em; margin-top: 2px;">Intelligence v2.1</div>
                </div>
            </div>
        </div>
    """,
        unsafe_allow_html=True,
    )

    # Horizontal Navigation using columns and buttons
    cols = st.columns([1, 1, 1, 1, 2])

    for i, (label, page_id) in enumerate(tabs.items()):
        with cols[i]:
            # Check if current_page matches this label or page_id
            is_active = current_page == label or current_page == page_id
            btn_type = "primary" if is_active else "secondary"
            if st.button(
                label, key=f"nav_{page_id}", use_container_width=True, type=btn_type
            ):
                st.session_state[SessionKeys.CURRENT_PAGE.value] = page_id
                st.rerun()

    with cols[4]:
        with st.popover("ℹ️ Bilgi & Yardım", use_container_width=True):
            st.markdown("""
            ### 🚀 Doc Analyzer Pro
            Bu uygulama, modern RAG tekniklerini kullanarak belgelerinizden anlamlı veriler çıkarmanıza yardımcı olur.

            **Özellikler:**
            - 📑 Çoklu Dosya Desteği (PDF, Docx, MD)
            - 🧠 Yerel LLM Desteği (Ollama)
            - ⚡ Hızlı Vektör Arama (ChromaDB)
            - 💬 Bağlamsal Sohbet Geçmişi

            **Sürüm:** `2.1.0-modern`
            """)
            st.info(
                "Herhangi bir sorun için sistem ayarlarından 'Önbelleği Temizle' butonunu kullanabilirsiniz."
            )

    st.divider()
    return current_page
