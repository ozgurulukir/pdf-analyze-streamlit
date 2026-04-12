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


@st.dialog("Yeni Çalışma Alanı")
def create_workspace_dialog():
    """Dialog for creating a workspace."""
    L = st.session_state.locale
    new_name = st.text_input(L.workspace.name_placeholder, placeholder="Örn: Hukuki Belgeler")
    if st.button(L.common.confirm, type="primary", use_container_width=True):
        if new_name.strip():
            create_workspace_callback(new_name)
            st.success(f"'{new_name}' {L.common.success}")
            st.rerun()
        else:
            st.error(L.common.error)


@st.dialog("Çalışma Alanını Yeniden Adlandır")
def rename_workspace_dialog(workspace_id, current_name):
    """Dialog for renaming a workspace."""
    L = st.session_state.locale
    new_name = st.text_input(L.workspace.rename_dialog_title, value=current_name)
    if st.button(L.common.update, type="primary", use_container_width=True):
        if new_name.strip():
            rename_workspace_callback(workspace_id, new_name)
            st.rerun()


@st.dialog("Çalışma Alanını Sil")
def delete_workspace_confirm_dialog(workspace_id, name):
    """Confirm deletion."""
    L = st.session_state.locale
    st.warning(L.workspace.delete_confirm)
    st.info(L.common.info)
    if st.button(L.common.delete, type="primary", use_container_width=True):
        delete_workspace_callback(workspace_id)
        st.rerun()


def render_file_card_visual(file, on_delete):
    """Render a premium file card using native border container."""
    ext = (file.file_type or "").lower()
    file_icon = FILE_ICONS.get(ext, "📄")
    file_size_kb = file.size / 1024 if file.size else 0
    L = st.session_state.locale
    status_config = get_status_config(L)
    status = status_config.get(file.status, status_config["pending"])

    with st.container(border=True):
        c1, c2 = st.columns([1, 4], vertical_alignment="center")
        c1.markdown(f"### {file_icon}")
        with c2:
            st.markdown(f"**{file.original_name}**")
            # Using st.pills for status would be cool but here labels are fixed
            st.caption(f"{status['icon']} {status['label']} • {ext.upper()} • {file_size_kb:.1f} KB")

        # Tools row
        st.write("")
        col_del, _ = st.columns([1, 4])
        if col_del.button("🗑️", key=f"lib_del_{file.id}", help=L.common.delete, use_container_width=True, type="secondary"):
            on_delete(file.id)


def render_library_page(settings: dict):
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

    # Page Header (Native 1.40+)
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
                create_workspace_dialog()

        for ws in workspaces:
            is_active = active_ws and ws.id == active_ws.id
            with st.container(border=True):
                c1, c2, c3 = st.columns([0.1, 0.6, 0.3], vertical_alignment="center")
                with c1:
                    st.markdown("### ✅" if is_active else "### 📂")
                with c2:
                    st.markdown(f"**{ws.name}**")
                    st.caption(
                        f"{ws.file_count} belge • Son işlem: {ws.last_modified.strftime('%d/%m/%Y')}"
                    )
                with c3:
                    sub1, sub2, sub3 = st.columns(3)
                    sub1.button("📂", key=f"sel_{ws.id}", help="Seç", use_container_width=True, on_click=select_workspace_callback, args=(ws.id,))
                    sub2.button("📝", key=f"ren_{ws.id}", help="Ad değiştir", use_container_width=True, on_click=rename_workspace_dialog, args=(ws.id, ws.name))
                    sub3.button("🗑️", key=f"del_{ws.id}", help="Sil", use_container_width=True, on_click=delete_workspace_confirm_dialog, args=(ws.id, ws.name))

    with tab_upload:
        if active_ws:
            st.markdown(f"#### 📤 '{active_ws.name}' Alanına Yükle")
            render_upload_zone(
                on_upload=lambda files: upload_files_callback(
                    files, active_ws, settings
                )
            )
        else:
            st.warning("Dosya yüklemek için önce bir çalışma alanı seçin.")

    with tab_files:
        if not active_ws:
            st.info("Belgelerini listelemek için bir çalışma alanı seçin.")
        else:

            @st.fragment
            def render_filtered_file_list():
                L = st.session_state.locale
                from app.core.cache import invalidate_file_cache
                files = get_cached_files(active_ws.id)

                if not files:
                    st.info("Bu çalışma alanında henüz belge yok.")
                else:
                    # Filter & Actions bar
                    col_f, col_r = st.columns([3, 1])
                    with col_f:
                        status_filter = st.selectbox(
                            L.library.status,
                            options=[
                                "Tümü",
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
                        if status_filter == "Tümü"
                        else [f for f in files if f.status == status_filter]
                    )
                    st.caption(f"{len(filtered)} belge listeleniyor")
                    st.divider()

                    cols = st.columns(2)
                    for idx, file in enumerate(filtered):
                        with cols[idx % 2]:
                            render_file_card_visual(file, delete_file_callback)

            render_filtered_file_list()
