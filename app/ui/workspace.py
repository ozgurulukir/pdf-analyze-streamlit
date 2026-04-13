"""Workspace UI components - sidebar and file management."""

from collections.abc import Callable

import streamlit as st

from app.core.models import FileMetadata, Workspace


def render_workspace_selector(
    workspaces: list[Workspace],
    active_workspace: Workspace | None,
    on_create: Callable,
    on_select: Callable,
    on_delete: Callable,
    on_rename: Callable,
):
    """Render workspace selector in sidebar."""
    L = st.session_state.locale
    st.markdown(f"### {L.workspace.current_areas}")

    @st.fragment
    def render_workspaces_list():
        # Workspace list
        for ws in workspaces:
            is_active = active_workspace and ws.id == active_workspace.id

            col1, col2, col3 = st.columns([1, 4, 1])
            with col1:
                if is_active:
                    st.success("✅")
                else:
                    if st.button("📂", key=f"sel_{ws.id}", help=L.workspace.select):
                        on_select(ws.id)
                        st.rerun()
            with col2:
                st.markdown(f"**{ws.name}**")
                st.caption(
                    f"{ws.file_count} dosya • {ws.last_modified.strftime('%d/%m/%Y')}"
                )

                # Simple rename expander
                with st.expander(f"📝 {L.workspace.rename}", expanded=False):
                    new_name = st.text_input(
                        L.workspace.rename_dialog_title,
                        value=ws.name,
                        key=f"rename_input_{ws.id}",
                        label_visibility="collapsed",
                    )
                    if st.button(L.common.update, key=f"rename_btn_{ws.id}"):
                        on_rename(ws.id, new_name)
                        st.rerun()
            with col3:
                if st.button("🗑️", key=f"del_ws_{ws.id}", help="Sil"):
                    on_delete(ws.id)

    render_workspaces_list()
    st.divider()

    @st.fragment
    def render_create_workspace():
        # Create new workspace
        with st.expander(f"{L.workspace.new_workspace}", expanded=False):
            new_name = st.text_input(L.workspace.name_placeholder, key="new_workspace_name")
            if st.button(L.common.confirm, key="create_workspace_btn"):
                if new_name.strip():
                    on_create(new_name)
                    st.rerun()

    render_create_workspace()


def render_file_card(
    file: FileMetadata,
    on_delete: Callable,
    on_revectorize: Callable,
    on_preview: Callable,
):
    """Render a premium file card."""
    L = st.session_state.locale
    from streamlit_extras.stylable_container import stylable_container

    # Status styling
    status_map = {
        "pending": ("⏳", "#94a3b8"),
        "processing": ("⚙️", "#6366f1"),
        "processed": ("✅", "#10b981"),
        "error": ("❌", "#ef4444"),
    }
    icon, color = status_map.get(file.status, ("❓", "#94a3b8"))

    with stylable_container(
        key=f"file_{file.id}",
        css_styles="""
            {
                background: rgba(30, 41, 59, 0.4);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                padding: 1rem;
                margin-bottom: 1rem;
                transition: all 0.3s ease;
            }
        """,
    ):
        # File Info Row
        col_icon, col_text = st.columns([1, 6])
        with col_icon:
            st.markdown(
                "<div style='font-size: 2rem; text-align: center;'>📄</div>",
                unsafe_allow_html=True,
            )
        with col_text:
            st.markdown(f"**{file.original_name}**")
            st.markdown(
                f"<small style='color: {color}; font-weight: 600;'>{icon} {file.status.upper()}</small> | <small style='color: #94a3b8;'>{file.size // 1024} KB • {file.chunk_count} chunk</small>",
                unsafe_allow_html=True,
            )

        # Action buttons (Compact)
        st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
        btn_col1, btn_col2, btn_col3 = st.columns(3)
        with btn_col1:
            if st.button(f"👁️ {L.common.edit}", key=f"prev_{file.id}", use_container_width=True):
                on_preview(file)
        with btn_col2:
            if st.button(
                f"🔄 {L.library.sync_data}",
                key=f"rev_{file.id}",
                use_container_width=True,
                disabled=file.status != "processed",
            ):
                on_revectorize(file.id)
        with btn_col3:
            # Stylable container for delete button to make it red-themed
            with stylable_container(
                key=f"del_cont_{file.id}",
                css_styles="button { background: rgba(239, 68, 68, 0.1) !important; color: #ef4444 !important; border: 1px solid rgba(239, 68, 68, 0.2) !important; }",
            ):
                if st.button(f"🗑️ {L.common.delete}", key=f"del_{file.id}", use_container_width=True):
                    on_delete(file.id)
                    st.rerun()


def render_file_list(
    files: list[FileMetadata],
    on_delete: Callable,
    on_revectorize: Callable,
    on_preview: Callable,
):
    """Render list of files in workspace."""
    L = st.session_state.locale
    if not files:
        st.markdown(f"### {L.library.files_tab} (0)")
        st.info(L.library.no_files)
        return

    # Wrap file list in an expander for better space management
    with st.expander(f"📄 {L.library.files_tab} ({len(files)})", expanded=True):
        for file in files:
            render_file_card(file, on_delete, on_revectorize, on_preview)


def render_upload_zone(on_upload: Callable, allowed_types: list[str] | None = None):
    """Render file upload zone."""
    L = st.session_state.locale
    st.markdown(f"### {L.library.upload_label}")

    if allowed_types is None:
        allowed_types = ["pdf", "txt", "docx", "html", "md"]

    uploaded_files = st.file_uploader(
        L.library.upload_label,
        type=allowed_types,
        accept_multiple_files=True,
        help=L.library.upload_help,
        label_visibility="collapsed",
        key="main_file_uploader" # Stable key
    )

    if uploaded_files:
        st.write(L.library.listing_count.format(len(uploaded_files)))

        if st.button(L.library.upload_label, type="primary", use_container_width=True, key="main_upload_btn"):
            on_upload(uploaded_files)

        return uploaded_files

    return None


# Redundant progress rendering removed in favor of Global Header Progress Tracker


def render_workspace_modal(
    is_open: bool,
    workspaces: list[Workspace],
    on_create: Callable,
    on_select: Callable,
    on_delete: Callable,
):
    """Render workspace selector as modal/panel."""
    if not is_open:
        return

    with st.container():
        L = st.session_state.locale
        st.markdown(f"### {L.workspace.current_areas}")

        # List
        for ws in workspaces:
            col1, col2, col3 = st.columns([1, 3, 1])
            with col1:
                st.write("📂")
            with col2:
                if st.button(
                    ws.name, key=f"modal_sel_{ws.id}", use_container_width=True
                ):
                    on_select(ws.id)
            with col3:
                if st.button("🗑️", key=f"modal_del_{ws.id}"):
                    on_delete(ws.id)

        st.divider()

        # Create new
        st.text_input(L.workspace.new_workspace, key="modal_new_workspace")


def render_document_stats(
    files: list[FileMetadata], workspace_id: str, workspace_name: str
):
    """Render document statistics using native components."""
    L = st.session_state.locale
    if not files:
        st.warning(L.library.no_files_ws)
        return

    from app.core.container import get_chroma
    chroma_manager = get_chroma()
    chunk_count = chroma_manager.get_chunk_count(workspace_id, workspace_name)

    total_size = sum(f.size for f in files) / 1024  # KB
    processed = len([f for f in files if f.status == "processed"])

    with st.container(border=True):
        st.markdown(f"**{L.library.stats_label}: {workspace_name}**")
        c1, c2, c3 = st.columns(3)
        c1.metric(L.analysis.total_docs, len(files))
        c2.metric(L.analysis.processed, processed)
        c3.metric(L.analysis.avg_size, chunk_count) # Vektör sayısı avg_size alanını ödünç alıyor veya yeni alan eklemeli

        st.caption(f"{L.library.file_size}: {total_size:.1f} KB")

    if chunk_count == 0 and processed > 0:
        st.warning(L.settings.health_empty)
