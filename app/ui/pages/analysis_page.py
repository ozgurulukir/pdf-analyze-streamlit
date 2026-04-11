"""Analysis page component."""

import streamlit as st

from app.core import DatabaseManager, UserPreferences
from app.core.constants import SessionKeys


def render_qa_card(qa, on_like, on_dislike):
    """Render a single Q&A card from legacy dashboard."""
    with st.container():
        st.markdown(f"**❓ Soru:** {qa.content if hasattr(qa, 'content') else 'N/A'}")
        with st.expander("💡 Cevabı Gör"):
            st.markdown(qa.answer if hasattr(qa, "answer") else "Cevap yok.")
            if hasattr(qa, "sources") and qa.sources:
                st.caption(f"Kaynaklar: {', '.join(qa.sources)}")

        col1, col2, _ = st.columns([1, 1, 4])
        with col1:
            st.button(f"👍", key=f"like_{id(qa)}")
        with col2:
            st.button(f"👎", key=f"dislike_{id(qa)}")
    st.divider()


def render_preference_adjuster(preferences):
    """Render preference adjustment panel from legacy dashboard."""
    st.markdown("### ⚖️ Tercihlerinizi Ayarlayın")
    st.caption("Cevap tarzınızı özelleştirin")

    if not hasattr(preferences, "weights"):
        preferences.weights = {
            "concise": 0.5,
            "detailed": 0.5,
            "examples": 0.5,
            "step_by_step": 0.5,
        }

    for tag, weight in preferences.weights.items():
        st.slider(
            tag.replace("_", " ").title(),
            min_value=0.0,
            max_value=1.0,
            value=float(weight),
            step=0.1,
            key=f"pref_{tag}",
        )


def render_analysis_page():
    """Render the analysis dashboard page with legacy features."""
    # Premium Page Header
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
        ">📊</div>
        <div>
            <div style="font-size: 1.05rem; font-weight: 700; color: #e0e7ff; letter-spacing: -0.02em;">Veri Analiz Paneli</div>
            <div style="font-size: 0.78rem; color: #64748b; margin-top: 1px;">Çalışma alanı istatistikleri ve geçmiş sorgular</div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    db = DatabaseManager()

    if st.session_state.get(SessionKeys.ACTIVE_WORKSPACE_ID.value):
        files = db.get_files(
            st.session_state.get(SessionKeys.ACTIVE_WORKSPACE_ID.value)
        )
        processed_count = len([f for f in files if f.status == "processed"])

        col1, col2, col3 = st.columns(3)
        col1.metric("Toplam Belge", len(files))
        col2.metric("İşlenen", processed_count)
        col3.metric("Kuyrukta", len(files) - processed_count)

        st.divider()

        tab1, tab2 = st.tabs(["📈 İstatistikler", "🎯 Tercihler & Geçmiş"])

        with tab1:
            st.markdown("### 📈 Workspace İstatistikleri")
            # Adaptive document stats from upload.py
            if files:
                total_chars = sum(
                    len(f.filename) * 100 for f in files
                )  # Simulated char count for demo or use real if available
                total_docs = len(files)
                sources = list(set(f.original_name for f in files))

                c1, c2, c3 = st.columns(3)
                c1.metric("📄 Toplam Belge", total_docs)
                c2.metric("📝 Özgün Kaynaklar", len(sources))
                c3.metric(
                    "💾 Ortalama Boyut",
                    (
                        f"{sum(f.size for f in files)/(total_docs*1024):.1f} KB"
                        if total_docs > 0
                        else "0 KB"
                    ),
                )

                with st.expander("📋 Kaynak Dosya Listesi"):
                    for source in sources:
                        st.write(f"- {source}")
            else:
                st.info("İstatistik gösterilecek belge bulunamadı.")

        with tab2:
            render_preference_adjuster(
                st.session_state.get(SessionKeys.PREFERENCES.value)
            )
            st.divider()
            st.markdown("### 💬 Son Soru-Cevaplar")
            # In a real scenario, we would fetch QAPairs from DB
            # For now, we show a subset of chat history if it matches
            if st.session_state.get(SessionKeys.CHAT_HISTORY.value):
                for msg in st.session_state.get(SessionKeys.CHAT_HISTORY.value):
                    if msg.role == "assistant":
                        render_qa_card(msg, None, None)
            else:
                st.info("Henüz geçmiş bulunmuyor.")
    else:
        st.warning("Lütfen sidebar'dan bir çalışma alanı seçin.")
