"""Analysis page component."""

import streamlit as st

from app.core import DatabaseManager
from app.core.constants import SessionKeys
from app.core.logger import logger


def render_preference_adjuster(preferences):
    """Render preference adjustment panel."""
    L = st.session_state.locale
    if preferences is None:
        st.info(L.analysis.no_data)
        return

    st.markdown(f"### {L.analysis.pref_title}")
    st.caption(L.analysis.pref_subtitle)

    if not hasattr(preferences, "weights"):
        preferences.weights = {
            "concise": 0.5,
            "detailed": 0.5,
            "examples": 0.5,
            "step_by_step": 0.5,
        }


    def save_weight_change(tag_to_update):
        db = DatabaseManager()
        is_active = st.session_state[f"pref_{tag_to_update}"]

        # Çelişki kontrolü (Mutual Exclusion): Concise vs Detailed
        if is_active:
            if tag_to_update == "concise":
                if preferences.weights.get("detailed", 0) > 0.5:
                    db.preferences.update_weights({"detailed": 0.0})
                    preferences.weights["detailed"] = 0.0
                    st.session_state["pref_detailed"] = False # Session state'i de güncelle!
                    st.toast("⚠️ Detaylı anlatım kapatıldı (Çelişki önlendi).")
            elif tag_to_update == "detailed":
                if preferences.weights.get("concise", 0) > 0.5:
                    db.preferences.update_weights({"concise": 0.0})
                    preferences.weights["concise"] = 0.0
                    st.session_state["pref_concise"] = False # Session state'i de güncelle!
                    st.toast("⚠️ Kısa yanıt kapatıldı (Çelişki önlendi).")

        new_val = 1.0 if is_active else 0.0
        preferences.weights[tag_to_update] = new_val
        # DB'ye kaydet
        db.preferences.update_weights({tag_to_update: new_val})
        status_label = L.common.active_label if is_active else L.common.passive_label
        st.toast(f"ℹ️ {tag_to_update.replace('_', ' ').title()} {status_label}.")

        # Eğer bir çelişki çözüldüyse, diğer toggle'ın görsel olarak kapanması için sayfayı yenile
        st.rerun()

    for tag, weight in preferences.weights.items():
        st.toggle(
            tag.replace("_", " ").title(),
            value=bool(weight > 0.5),
            key=f"pref_{tag}",
            on_change=save_weight_change,
            args=(tag,)
        )


def render_analysis_page():
    """Render the analysis dashboard page with modern native UI."""
    L = st.session_state.locale
    # Page Header using native components
    with st.container(border=True):
        col_icon, col_text = st.columns([1, 8])
        col_icon.markdown("# 📊")
        with col_text:
            st.subheader(L.analysis.title)
            st.caption(L.analysis.header_caption)

    try:
        from app.core.container import get_database

        db = get_database()
    except Exception as e:
        from app.core.exceptions import DatabaseError
        if isinstance(e, DatabaseError):
            logger.error(f"Failed to init DB in analysis page: {e}")
            st.error("Veritabanı bağlantı hatası.")
            return
        raise e

    active_ws_id = st.session_state.get(SessionKeys.ACTIVE_WORKSPACE_ID.value)

    if active_ws_id:
        try:
            files = db.files.get_by_workspace(active_ws_id)
        except Exception:
            files = []
        processed_count = len([f for f in files if f.status == "processed"])

        # Statistics Grid
        with st.container(border=True):
            st.caption(f"📈 {L.library.stats_label}")
            m_col1, m_col2, m_col3 = st.columns(3)
            m_col1.metric(L.analysis.total_docs, len(files))
            m_col2.metric(L.analysis.processed, processed_count, delta=f"{processed_count/len(files):.0%}" if files else "0%")
            m_col3.metric(L.analysis.queued, len(files) - processed_count)

        st.divider()

        tab1, tab2 = st.tabs([L.analysis.stats_tab, L.analysis.pref_tab])

        with tab1:
            st.markdown("### 📈 Workspace İstatistikleri")
            if files:
                total_docs = len(files)
                sources = list({f.original_name for f in files})

                with st.container(border=True):
                    st.caption("📋 Detaylı Boyut Analizi")
                    c1, c2, c3 = st.columns(3)
                    c1.metric(L.analysis.total_docs, total_docs)
                    c2.metric(L.analysis.unique_sources, len(sources))
                    c3.metric(
                        L.analysis.avg_size,
                        f"{sum(f.size for f in files) / (total_docs * 1024):.1f} KB"
                        if total_docs > 0
                        else "0 KB",
                    )

                with st.expander(L.chat.sources_title):
                    for source in sources:
                        st.write(f"- {source}")
            else:
                st.info(L.analysis.no_data)

        with tab2:
            prefs = st.session_state.get(SessionKeys.PREFERENCES.value)
            render_preference_adjuster(prefs)
    else:
        st.warning(L.workspace.no_active)
