import streamlit as st

from app.core.constants import SessionKeys


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
    if "pending_toast" in st.session_state and st.session_state["pending_toast"]:
        msg, icon = st.session_state.pop("pending_toast")
        st.toast(msg, icon=icon)

    active_id = st.session_state.get(SessionKeys.ACTIVE_WORKSPACE_ID.value)
    L = st.session_state.locale
    current_page = st.session_state.get(SessionKeys.CURRENT_PAGE.value, UIPages.CHAT)

    db = DatabaseManager()
    active_ws = None
    if active_id:
        try:
            active_ws = db.workspaces.get_by_id(active_id)
        except Exception:
            active_ws = None

    active_sess_id = st.session_state.get(SessionKeys.ACTIVE_SESSION_ID.value)
    active_sess = None
    if active_id and active_sess_id:
        try:
            active_sess = db.chat_sessions.get_by_id(active_sess_id)
        except Exception:
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
        nav_map = st.session_state.get("NAV_MAP", {})

        if sub_cols[0].button(f"💬 {L.chat.title}", key="nav_chat", use_container_width=True,
                              type="primary" if current_page == UIPages.CHAT else "secondary"):
            st.session_state[SessionKeys.CURRENT_PAGE.value] = UIPages.CHAT
            if UIPages.CHAT in nav_map:
                st.switch_page(nav_map[UIPages.CHAT])

        if sub_cols[1].button(f"📊 {L.analysis.title}", key="nav_analysis", use_container_width=True,
                              type="primary" if current_page == UIPages.ANALYSIS else "secondary"):
            st.session_state[SessionKeys.CURRENT_PAGE.value] = UIPages.ANALYSIS
            if UIPages.ANALYSIS in nav_map:
                st.switch_page(nav_map[UIPages.ANALYSIS])

        if sub_cols[2].button(f"⭐ {L.knowledge.title}", key="nav_knowledge", use_container_width=True,
                              type="primary" if current_page == UIPages.KNOWLEDGE else "secondary"):
            st.session_state[SessionKeys.CURRENT_PAGE.value] = UIPages.KNOWLEDGE
            if UIPages.KNOWLEDGE in nav_map:
                st.switch_page(nav_map[UIPages.KNOWLEDGE])

    # Settings dictionary for dialogs
    settings = {
        "model": st.session_state.get(SessionKeys.LLM_MODEL.value),
        "temperature": st.session_state.get(SessionKeys.LLM_TEMPERATURE.value),
        "api_key": st.session_state.get(SessionKeys.OLLAMA_API_KEY.value),
        "base_url": st.session_state.get(SessionKeys.LLM_BASE_URL.value),
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
            st.session_state.show_reset_confirm = False
            global_settings_dialog()

    # 4. Minimalist Background Job Tracker (Fragment)
    from app.core.jobs import get_job_queue
    job_queue = get_job_queue()

    @st.fragment(run_every="3s")
    def render_job_progress():
        if active_id:
            active_jobs = job_queue.get_active_jobs(active_id)
            if active_jobs:
                # Show only the most advanced/latest job for minimalism
                job = active_jobs[0]
                progress_val = job.progress / 100.0
                # Use native st.progress and st.status or caption
                with st.container():
                    st.progress(progress_val)
                    st.caption(f"⚙️ {job.job_type}... %{job.progress:.0f}", help="Dosya işleme devam ediyor...")

    render_job_progress()

    st.markdown("<br>", unsafe_allow_html=True)
    return current_page
