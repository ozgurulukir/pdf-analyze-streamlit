"""Analysis page component."""

import streamlit as st

from app.core.constants import SessionKeys
from app.core.logger import logger


def render_preference_adjuster(preferences):
    """Render preference adjustment panel as Prompt Management."""
    L = st.session_state.locale
    if preferences is None:
        st.info(L.analysis.no_data)
        return

    from app.core.constants import DefaultPrompts

    st.markdown(f"### {L.analysis.pref_title}")
    st.caption(L.analysis.pref_subtitle)

    # Ensure structures exist
    if not hasattr(preferences, "weights") or not preferences.weights:
        preferences.weights = dict.fromkeys(DefaultPrompts.get_defaults().keys(), 0.5)

    if "prompt_texts" not in preferences.config:
        preferences.config["prompt_texts"] = DefaultPrompts.get_defaults()

    def update_pref(tag, is_active, text):
        from app.core.container import get_database
        db = get_database()

        # Mutual exclusion for Concise vs Detailed
        if is_active:
            if tag == "concise" and preferences.weights.get("detailed", 0) > 0.5:
                preferences.weights["detailed"] = 0.0
                if "pref_detailed" in st.session_state:
                    st.session_state["pref_detailed"] = False
                st.toast(L.analysis.pref_conflict_detailed)
            elif tag == "detailed" and preferences.weights.get("concise", 0) > 0.5:
                preferences.weights["concise"] = 0.0
                if "pref_concise" in st.session_state:
                    st.session_state["pref_concise"] = False
                st.toast(L.analysis.pref_conflict_concise)

        preferences.weights[tag] = 1.0 if is_active else 0.0
        preferences.config["prompt_texts"][tag] = text

        # Persist to DB
        db.preferences.save(preferences)
        st.toast(L.common.success)

    icons = {
        "concise": "📝",
        "detailed": "📖",
        "examples": "💡",
        "step_by_step": "🔢"
    }

    for tag, default_text in DefaultPrompts.get_defaults().items():
        weight = preferences.weights.get(tag, 0.5)
        current_text = preferences.config["prompt_texts"].get(tag, default_text)
        icon = icons.get(tag, "📌")

        with st.container(border=True):
            header_col1, header_col2 = st.columns([4, 1])
            with header_col1:
                st.markdown(f"#### {icon} {tag.replace('_', ' ').title()}")
            with header_col2:
                is_active = st.checkbox(
                    L.analysis.prompt_include,
                    value=bool(weight > 0.5),
                    key=f"pref_{tag}",
                    label_visibility="collapsed"
                )
                if is_active:
                    st.caption(f"✅ {L.analysis.prompt_include}")

            new_text = st.text_area(
                L.analysis.prompt_label,
                value=current_text,
                key=f"text_{tag}",
                height=100,
                help=f"{tag} için kullanılacak sistem promptu parçası."
            )

            # Save button for this specific fragment
            if st.button(L.common.save, key=f"save_{tag}", use_container_width=True, type="secondary"):
                update_pref(tag, is_active, new_text)


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
            st.error(L.messages.db_error.format(str(e)))
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
            st.markdown(f"### {L.analysis.stats_title}")
            if files:
                total_docs = len(files)
                sources = list({f.original_name for f in files})

                with st.container(border=True):
                    st.caption(L.analysis.detail_analysis)
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
