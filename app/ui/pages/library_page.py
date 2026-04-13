"""Library page component with modern UI standards."""

import streamlit as st

from app.core import SessionKeys
from app.core.cache import (
    get_cached_database_manager,
)
from app.core.logger import logger
from app.ui.callbacks import (
    create_workspace_callback,
    delete_file_callback,
    delete_workspace_callback,
    get_cached_files,
    rename_workspace_callback,
    select_workspace_callback,
    upload_files_callback,
)
from app.ui.workspace import (
    render_document_stats,
    render_upload_zone,
)


def get_status_config(L):
    return {
        "processed": {
            "icon": "✅",
            "color": "#10b981",
            "bg": "rgba(16,185,129,0.1)",
            "border": "rgba(16,185,129,0.25)",
            "label": L.library.status_processed,
        },
        "processing": {
            "icon": "⚙️",
            "color": "#6366f1",
            "bg": "rgba(99,102,241,0.1)",
            "border": "rgba(99,102,241,0.25)",
            "label": L.library.status_processing,
        },
        "pending": {
            "icon": "⏳",
            "color": "#f59e0b",
            "bg": "rgba(245,158,11,0.1)",
            "border": "rgba(245,158,11,0.25)",
            "label": L.library.status_pending,
        },
        "error": {
            "icon": "❌",
            "color": "#ef4444",
            "bg": "rgba(239,68,68,0.1)",
            "border": "rgba(239,68,68,0.25)",
            "label": L.library.status_error,
        },
    }
FILE_ICONS = {"pdf": "📕", "txt": "📄", "docx": "📘", "md": "📝", "html": "🌐"}


def render_create_workspace_form():
    """Form content for creating a workspace."""
    L = st.session_state.locale
    new_name = st.text_input(L.workspace.name_placeholder, placeholder=L.workspace.example_name, key="inline_create_ws_name")
    if st.button(L.common.confirm, type="primary", use_container_width=True, key="inline_create_ws_btn"):
        if new_name.strip():
            create_workspace_callback(new_name)
            st.success(f"'{new_name}' {L.common.success}")
            st.rerun()
        else:
            st.error(L.common.error)

@st.dialog("Yeni Çalışma Alanı")
def create_workspace_dialog():
    """Dialog wrapper for workspace creation."""
    render_create_workspace_form()


def render_rename_workspace_form(workspace_id, current_name):
    """Form content for renaming a workspace."""
    L = st.session_state.locale
    new_name = st.text_input(L.workspace.rename_dialog_title, value=current_name, key=f"inline_ren_name_{workspace_id}")
    if st.button(L.common.update, type="primary", use_container_width=True, key=f"inline_ren_btn_{workspace_id}"):
        if new_name.strip():
            rename_workspace_callback(workspace_id, new_name)
            st.rerun()

@st.dialog("Çalışma Alanını Yeniden Adlandır")
def rename_workspace_dialog(workspace_id, current_name):
    """Dialog wrapper for workspace renaming."""
    render_rename_workspace_form(workspace_id, current_name)


def render_delete_workspace_form(workspace_id, name):
    """Form content for deleting a workspace."""
    L = st.session_state.locale
    st.warning(L.workspace.delete_confirm)
    st.info(L.common.info)
    if st.button(L.common.delete, type="primary", use_container_width=True, key=f"inline_del_btn_{workspace_id}"):
        delete_workspace_callback(workspace_id)
        st.rerun()

@st.dialog("Çalışma Alanını Sil")
def delete_workspace_confirm_dialog(workspace_id, name):
    """Dialog wrapper for workspace deletion."""
    render_delete_workspace_form(workspace_id, name)


def render_file_card_visual(file, on_delete):
    """Render a premium file card using native border container."""
    L = st.session_state.locale
    ext = (file.file_type or "").lower()
    file_icon = FILE_ICONS.get(ext, "📄")
    file_size_kb = file.size / 1024 if file.size else 0
    status_config = get_status_config(L)
    status = status_config.get(file.status, status_config["pending"])

    with st.container(border=True):
        c1, c2 = st.columns([1, 4], vertical_alignment="center")
        c1.markdown(f"### {file_icon}")
        with c2:
            st.markdown(f"**{file.original_name}**")
            # Using st.pills for status would be cool but here labels are fixed
            st.caption(f"{status['icon']} {status['label']} • {ext.upper()} • {file_size_kb:.1f} KB")

            # Show error message if processing failed
            if file.status == "error" and file.error_message:
                st.error(f"⚠️ {file.error_message}")

        # Tools row
        st.write("")
        col_del, _ = st.columns([1, 4])
        if col_del.button("🗑️", key=f"lib_del_{file.id}", help=L.common.delete, use_container_width=True, type="secondary"):
            on_delete(file.id)
            st.rerun()


def render_library_page(settings: dict, is_dialog: bool = False):
    """Render the document library page with modern UI."""
    db = get_cached_database_manager()
    active_ws_id = st.session_state.get(SessionKeys.ACTIVE_WORKSPACE_ID.value)

    active_ws = None
    if active_ws_id:
        try:
            active_ws = db.workspaces.get_by_id(active_ws_id)
        except Exception as e:
            from app.core.exceptions import DatabaseError
            if isinstance(e, DatabaseError):
                logger.error(f"Failed to fetch active workspace {active_ws_id}: {e}")
            else:
                raise e

    L = st.session_state.locale

    # Page Header (Only in Page mode to save space in Dialog)
    if not is_dialog:
        with st.container(border=True):
            h_col1, h_col2 = st.columns([1, 8], vertical_alignment="center")
            h_col1.markdown("# 📚")
            with h_col2:
                st.subheader(L.library.header_subtitle)
                st.caption(L.library.header_caption)

    # Tabs
    tab_stats, tab_manage, tab_upload, tab_files = st.tabs(
        [L.library.stats_label, L.library.manage_tab, L.library.upload_tab, L.library.files_tab]
    )

    with tab_stats:
        if active_ws:
            files = get_cached_files(active_ws.id)
            render_document_stats(files, active_ws.id, active_ws.name)

            # Diagnostic Sync Button
            if st.button(L.library.sync_data, use_container_width=True, help=L.library.sync_help):
                from app.core.cache import (
                    invalidate_file_cache,
                    invalidate_workspace_cache,
                )
                invalidate_file_cache(active_ws.id)
                invalidate_workspace_cache(active_ws.id)
                # Force re-count in DB
                active_ws.file_count = db.files.count_by_workspace(active_ws.id)
                db.workspaces.update(active_ws)
                st.success(L.library.sync_success)
                st.rerun()
        else:
            st.info(L.library.no_files)

    with tab_manage:
        st.markdown(f"### {L.workspace.current_areas}")
        workspaces = st.session_state.get(SessionKeys.WORKSPACES.value, [])

        col_ws, col_create = st.columns([4, 1])
        with col_create:
            if st.button(L.common.edit, use_container_width=True, type="primary"):
                if is_dialog:
                    st.session_state.show_create_ws_inline = not st.session_state.get("show_create_ws_inline", False)
                else:
                    create_workspace_dialog()

        if st.session_state.get("show_create_ws_inline", False):
            with st.container(border=True):
                st.markdown(f"#### {L.workspace.new_workspace}")
                render_create_workspace_form()

        for ws in workspaces:
            is_active = active_ws and ws.id == active_ws.id
            with st.container(border=True):
                main_c, action_c = st.columns([0.7, 0.3], vertical_alignment="center")

                with main_c:
                    c1, c2 = st.columns([0.1, 0.9])
                    c1.markdown("### ✅" if is_active else "### 📂")
                    with c2:
                        st.markdown(f"**{ws.name}**")
                        st.caption(L.library.last_action.format(ws.last_modified.strftime('%d/%m/%Y')))

                with action_c:
                    sub1, sub2, sub3 = st.columns(3)
                    if sub1.button("📂", key=f"sel_{ws.id}", help=L.workspace.select, use_container_width=True):
                        select_workspace_callback(ws.id)
                        st.rerun()
                    if sub2.button("📝", key=f"ren_{ws.id}", help=L.workspace.rename, use_container_width=True):
                        if is_dialog:
                            st.session_state[f"show_ren_{ws.id}"] = not st.session_state.get(f"show_ren_{ws.id}", False)
                        else:
                            rename_workspace_dialog(ws.id, ws.name)
                    if sub3.button("🗑️", key=f"del_{ws.id}", help=L.common.delete, use_container_width=True):
                        if is_dialog:
                            st.session_state[f"show_del_{ws.id}"] = not st.session_state.get(f"show_del_{ws.id}", False)
                        else:
                            delete_workspace_confirm_dialog(ws.id, ws.name)

                # Inline forms for dialog mode
                if is_dialog:
                    if st.session_state.get(f"show_ren_{ws.id}", False):
                        with st.container(border=True):
                            render_rename_workspace_form(ws.id, ws.name)
                    if st.session_state.get(f"show_del_{ws.id}", False):
                        with st.container(border=True):
                            render_delete_workspace_form(ws.id, ws.name)

    with tab_upload:
        if active_ws:
            st.markdown(f"#### 📤 {L.library.upload_to.format(active_ws.name)}")
            render_upload_zone(
                on_upload=lambda files: upload_files_callback(
                    files, active_ws, settings
                )
            )
        else:
            st.warning(L.library.select_ws_to_upload)

    with tab_files:
        if not active_ws:
            st.info(L.library.select_ws_to_list)
        else:

            @st.fragment
            def render_filtered_file_list():
                L = st.session_state.locale
                from app.core.cache import invalidate_file_cache
                files = get_cached_files(active_ws.id)

                if not files:
                    st.info(L.library.no_files_ws)
                else:
                    # Filter & Actions bar
                    col_f, col_r = st.columns([3, 1])
                    with col_f:
                        status_filter = st.selectbox(
                            L.library.status,
                            options=[
                                L.library.status_all,
                                "processed",
                                "pending",
                                "processing",
                                "error",
                            ],
                            key="lib_status_filter",
                            label_visibility="collapsed",
                        )
                    with col_r:
                        if st.button(L.common.refresh, use_container_width=True):
                            invalidate_file_cache(active_ws.id)
                            st.rerun()

                    filtered = (
                        files
                        if status_filter == L.library.status_all
                        else [f for f in files if f.status == status_filter]
                    )
                    st.caption(L.library.listing_count.format(len(filtered)))
                    st.divider()

                    cols = st.columns(2)
                    for idx, file in enumerate(filtered):
                        with cols[idx % 2]:
                            render_file_card_visual(file, delete_file_callback)

            render_filtered_file_list()
