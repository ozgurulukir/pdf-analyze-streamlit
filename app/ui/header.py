import streamlit as st

from app.core.constants import ProcessingStatus, SessionKeys
from app.core.logger import logger
from app.ui.state import state


def render_header():
    """Render a premium Canvas Top-Nav with dialog triggers."""
    from app.core.constants import UIPages
    from app.core.database import DatabaseManager
    from app.ui.dialogs import (
        chat_sessions_dialog,
        document_library_dialog,
        global_settings_dialog,
        manage_workspaces_dialog,
    )

    # 0. Pure Streamlit Toaster (Handles messages across reruns)
    toast_data = state.pop_toast()
    if toast_data:
        st.toast(toast_data[0], icon=toast_data[1])

    active_id = state.active_workspace_id
    L = state.locale
    current_page = state.current_page

    db = DatabaseManager()
    active_ws = None
    if active_id:
        try:
            active_ws = db.workspaces.get_by_id(active_id)
        except Exception as e:
            logger.warning(f"Failed to load workspace {active_id}: {e}")
            active_ws = None

    active_sess_id = state.active_session_id
    active_sess = None
    if active_id and active_sess_id:
        try:
            active_sess = db.chat_sessions.get_by_id(active_sess_id)
        except Exception as e:
            logger.warning(f"Failed to load chat session {active_sess_id}: {e}")
            active_sess = None

    # Use native st.logo
    st.logo("💎", icon_image="💎")

    c1, c2, c3 = st.columns([2, 3, 2], vertical_alignment="center")

    with c1:
        # Workspace Switcher
        ws_label = active_ws.name if active_ws else L.common.edit
        sess_label = f" | {active_sess.title}" if active_sess else ""
        if st.button(f"📂 {ws_label}{sess_label}", key="trigger_ws", help=L.workspace.title):
            manage_workspaces_dialog()

    with c2:
        # View Switcher (Chat / Analysis / Knowledge)
        sub_cols = st.columns(3)
        nav_map = state.get("NAV_MAP", {})

        if sub_cols[0].button(f"💬 {L.chat.title}", key="nav_chat", use_container_width=True,
                              type="primary" if current_page == UIPages.CHAT else "secondary"):
            state.current_page = UIPages.CHAT
            if UIPages.CHAT in nav_map:
                st.switch_page(nav_map[UIPages.CHAT])

        if sub_cols[1].button(f"📊 {L.analysis.title}", key="nav_analysis", use_container_width=True,
                              type="primary" if current_page == UIPages.ANALYSIS else "secondary"):
            state.current_page = UIPages.ANALYSIS
            if UIPages.ANALYSIS in nav_map:
                st.switch_page(nav_map[UIPages.ANALYSIS])

        if sub_cols[2].button(f"⭐ {L.knowledge.title}", key="nav_knowledge", use_container_width=True,
                              type="primary" if current_page == UIPages.KNOWLEDGE else "secondary"):
            state.current_page = UIPages.KNOWLEDGE
            if UIPages.KNOWLEDGE in nav_map:
                st.switch_page(nav_map[UIPages.KNOWLEDGE])

    # Settings dictionary for dialogs
    settings = {
        "model": state.get(SessionKeys.LLM_MODEL),
        "temperature": state.get(SessionKeys.LLM_TEMPERATURE),
        "api_key": state.get(SessionKeys.OLLAMA_API_KEY),
        "base_url": state.get(SessionKeys.LLM_BASE_URL),
        "embedding": {
            "use_huggingface": state.get(SessionKeys.USE_HUGGINGFACE, False),
            "model_name": state.get(SessionKeys.HF_EMBED_MODEL) if state.get(SessionKeys.USE_HUGGINGFACE) else state.get(SessionKeys.EMBED_MODEL),
            "ollama_url": state.get(SessionKeys.OLLAMA_URL),
            "chunk_size": state.get(SessionKeys.CHUNK_SIZE),
            "chunk_overlap": state.get(SessionKeys.CHUNK_OVERLAP),
        }
    }

    with c3:
        # Tools Switcher
        tool_cols = st.columns(3)
        if tool_cols[0].button("💬", key="trigger_chat_sess", help=L.chat.sources_title, use_container_width=True):
            chat_sessions_dialog()
        if tool_cols[1].button("📚", key="trigger_lib", help=L.library.title, use_container_width=True):
            document_library_dialog(settings=settings)
        if tool_cols[2].button("⚙️", key="trigger_set", help=L.settings.title, use_container_width=True):
            # Reset confirmation flag so it doesn't open in 'reset' mode
            state.set("show_reset_confirm", False)
            global_settings_dialog()

    # 4. Minimalist Background Job Tracker (Fragment)
    from app.core.jobs import get_job_queue
    job_queue = get_job_queue()

    @st.fragment(run_every="2s")
    def render_job_progress():
        if active_id:
            # Force a fresh check from DB in the fragment
            active_jobs = job_queue.get_active_jobs(active_id)
            if active_jobs:
                job = active_jobs[0]
                progress_val = job.progress / 100.0 if job.progress <= 100 else 1.0
                
                with st.container(border=True):
                    # Status Headline
                    status_text = "Bekleniyor..."
                    if job.status == ProcessingStatus.RUNNING.value:
                        status_text = f"🔄 İşleniyor: {job.current}/{job.total} dosya"
                    elif job.status == ProcessingStatus.COMPLETED.value:
                        status_text = "✅ Başarıyla Tamamlandı"
                    elif job.status == ProcessingStatus.FAILED.value:
                        status_text = "❌ İşlem Başarısız"
                    
                    st.markdown(f"**{status_text}**")
                    st.progress(progress_val)
                    
                    # Details
                    msg = f"⚙️ {job.job_type} | %{job.progress:.0f}"
                    if job.status == ProcessingStatus.RUNNING.value:
                         msg += " | Lütfen bekleyiniz..."
                    st.caption(msg)

                    if job.status == ProcessingStatus.FAILED.value and job.error_message:
                        st.error(f"Hata Detayı: {job.error_message}")
                    elif job.status == ProcessingStatus.COMPLETED.value:
                        st.success("Tüm belgeler işlendi.")

    render_job_progress()

    st.markdown("<br>", unsafe_allow_html=True)
    return current_page
