"""Knowledge Base page component with advanced filtering and professional UI."""

import streamlit as st

from app.core.constants import SessionKeys
from app.core.logger import get_logger

logger = get_logger(__name__)


def render_qa_card(qa, question_text=None):
    """Render a professional Q&A card using central CSS classes."""
    L = st.session_state.locale
    with st.container(border=True):
        question = question_text or getattr(qa, "question", "N/A")
        full_answer = getattr(qa, "answer", L.knowledge.no_results)

        # Header Area
        col_q, col_actions = st.columns([9, 1])
        with col_q:
            st.markdown(f"#### ❓ {question}")

            # Use central .kb-tag class
            if hasattr(qa, "tags") and qa.tags:
                tag_html = "".join([f'<span class="kb-tag"># {t}</span>' for t in qa.tags])
                st.markdown(tag_html, unsafe_allow_html=True)

        with col_actions:
            if st.button("🗑️", key=f"del_{qa.id}", help=L.common.delete):
                from app.core.container import get_database
                db = get_database()
                db.qa.delete(qa.id)
                st.toast(L.knowledge.delete_confirm, icon="🗑️")
                st.rerun()

        # Peaceful Truncation
        truncated = (full_answer[:250] + "...") if len(full_answer) > 250 else full_answer
        st.markdown(f'<div class="kb-answer-text">{truncated}</div>', unsafe_allow_html=True)

        # Detail View
        with st.expander(f"📝 {L.common.info}"):
            st.markdown("---")
            st.markdown(full_answer)

            if hasattr(qa, "sources") and qa.sources:
                st.markdown(f"##### {L.chat.sources_title}")
                source_names = []
                for s in qa.sources:
                    if isinstance(s, dict):
                        path = s.get("file", "Bilinmeyen")
                        name = path.split("/")[-1].split("\\")[-1]
                        source_names.append(name)
                    else:
                        source_names.append(str(s))

                for name in set(source_names):
                    st.markdown(f"- `{name}`")

            st.caption(f"{L.knowledge.date_label}: {qa.created_at.strftime('%d.%m.%Y %H:%M')}")


def render_knowledge_page():
    """Render the Knowledge Base using Pure Streamlit + Centralized CSS."""
    L = st.session_state.locale

    # Premium Header
    st.markdown(f"""
        <div class="kb-header-box">
            <h1 style='margin: 0; color: #f8f9fa;'>{L.knowledge.title}</h1>
        </div>
    """, unsafe_allow_html=True)

    from app.core.container import get_database
    db = get_database()
    active_ws_id = st.session_state.get(SessionKeys.ACTIVE_WORKSPACE_ID.value)

    if not active_ws_id:
        st.info(f"💡 {L.library.no_files}")
        return

    # 1. Filters
    with st.container(border=True):
        c1, c2 = st.columns([1, 1])
        all_qas = db.qa.get_by_workspace(active_ws_id)

        with c1:
            search_query = st.text_input(L.knowledge.search_label, placeholder=L.knowledge.search_placeholder, key="kb_search")
        with c2:
            all_tags = set()
            for qa in all_qas:
                if hasattr(qa, "tags") and qa.tags:
                    all_tags.update(qa.tags)

            selected_tags = st.multiselect(
                L.knowledge.tag_filter_label,
                options=sorted(all_tags),
                placeholder="Etiket seçin...",
                key="kb_tags_filter"
            )

    # 2. Logic
    filtered_qas = all_qas
    if search_query:
        q = search_query.lower()
        filtered_qas = [qa for qa in filtered_qas if q in qa.question.lower() or q in qa.answer.lower()]

    if selected_tags:
        filtered_qas = [qa for qa in filtered_qas if any(t in (qa.tags or []) for t in selected_tags)]

    st.markdown(f"🔍 **{len(filtered_qas)}** Uzman Cevap")

    # 3. Render
    if filtered_qas:
        for sqa in filtered_qas:
            render_qa_card(sqa)
    else:
        st.markdown(f'<div class="kb-empty-state"><h3>{L.knowledge.no_results}</h3></div>', unsafe_allow_html=True)
