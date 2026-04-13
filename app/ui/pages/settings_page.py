"""Settings page component."""

import streamlit as st

from app.ui.settings_components import (
    render_data_settings,
    render_embedding_settings,
    render_llm_settings,
)


def render_settings_page():
    """Render the settings page with tabbed interface."""
    st.markdown(
        """
    <div style="
        display: flex; align-items: center; gap: 14px;
        padding: 1.25rem 1.5rem;
        background: rgba(99, 102, 241, 0.05);
        border: 1px solid rgba(99, 102, 241, 0.15);
        border-radius: 14px; margin-bottom: 1.5rem;
    ">
        <div style="
            width: 44px; height: 44px;
            background: linear-gradient(135deg, #6366f1, #7c3aed);
            border-radius: 12px;
            display: flex; align-items: center; justify-content: center;
            font-size: 1.4rem; flex-shrink: 0;
            box-shadow: 0 4px 12px rgba(99,102,241,0.3);
        ">⚙️</div>
        <div>
            <div style="font-size: 1.05rem; font-weight: 700; color: #e0e7ff; letter-spacing: -0.02em;">Sistem Ayarları</div>
            <div style="font-size: 0.78rem; color: #64748b; margin-top: 1px;">Model, embedding ve veri parametrelerini yapılandırın</div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    tab_llm, tab_embed, tab_data = st.tabs(
        ["🤖 LLM", "🔢 Embedding", "📁 Veri & Sistem"]
    )

    with tab_llm:
        render_llm_settings()

    with tab_embed:
        render_embedding_settings()

    with tab_data:
        render_data_settings()
