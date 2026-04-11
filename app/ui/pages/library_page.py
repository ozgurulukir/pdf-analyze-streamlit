"""Library page component with modern UI standards."""

import streamlit as st

from app.core import SessionKeys
from app.core.cache import (
    get_cached_database_manager,
    invalidate_file_cache,
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

STATUS_CONFIG = {
    "processed": {
        "icon": "✅",
        "color": "#10b981",
        "bg": "rgba(16,185,129,0.1)",
        "border": "rgba(16,185,129,0.25)",
        "label": "İşlendi",
    },
    "processing": {
        "icon": "⚙️",
        "color": "#6366f1",
        "bg": "rgba(99,102,241,0.1)",
        "border": "rgba(99,102,241,0.25)",
        "label": "İşleniyor",
    },
    "pending": {
        "icon": "⏳",
        "color": "#f59e0b",
        "bg": "rgba(245,158,11,0.1)",
        "border": "rgba(245,158,11,0.25)",
        "label": "Bekliyor",
    },
    "error": {
        "icon": "❌",
        "color": "#ef4444",
        "bg": "rgba(239,68,68,0.1)",
        "border": "rgba(239,68,68,0.25)",
        "label": "Hata",
    },
}
FILE_ICONS = {"pdf": "📕", "txt": "📄", "docx": "📘", "md": "📝", "html": "🌐"}


@st.dialog("Yeni Çalışma Alanı")
def create_workspace_dialog():
    """Dialog for creating a workspace."""
    new_name = st.text_input("Çalışma alanı ismi", placeholder="Örn: Hukuki Belgeler")
    if st.button("Oluştur", type="primary", use_container_width=True):
        if new_name.strip():
            create_workspace_callback(new_name)
            st.success(f"'{new_name}' oluşturuldu.")
            st.rerun()
        else:
            st.error("Lütfen bir isim girin.")


@st.dialog("Hücreyi Yeniden Adlandır")
def rename_workspace_dialog(workspace_id, current_name):
    """Dialog for renaming a workspace."""
    new_name = st.text_input("Yeni isim", value=current_name)
    if st.button("Güncelle", type="primary", use_container_width=True):
        if new_name.strip():
            rename_workspace_callback(workspace_id, new_name)
            st.success("İsim güncellendi.")
            st.rerun()


@st.dialog("Çalışma Alanını Sil")
def delete_workspace_confirm_dialog(workspace_id, name):
    """Confirm deletion."""
    st.warning(
        f"'{name}' çalışma alanını ve içindeki TÜM belgeleri silmek istediğinizden emin misiniz?"
    )
    st.info("Bu işlem geri alınamaz.")
    if st.button("Evet, Her Şeyi Sil", type="primary", use_container_width=True):
        delete_workspace_callback(workspace_id)
        st.success("Çalışma alanı silindi.")
        st.rerun()


def render_file_card_visual(file, on_delete):
    """Render a premium file card using native border container."""
    ext = (file.file_type or "").lower()
    file_icon = FILE_ICONS.get(ext, "📄")
    file_size_kb = file.size / 1024 if file.size else 0
    status = STATUS_CONFIG.get(file.status, STATUS_CONFIG["pending"])

    with st.container(border=True):
        st.markdown(
            f"""
        <div style="display:flex; align-items:flex-start; gap:12px;">
            <div style="
                width: 42px; height: 42px; flex-shrink: 0;
                background: linear-gradient(135deg, rgba(99,102,241,0.15), rgba(124,58,237,0.15));
                border: 1px solid rgba(99, 102, 241, 0.2);
                border-radius: 10px;
                display: flex; align-items: center; justify-content: center;
                font-size: 1.3rem;
            ">{file_icon}</div>
            <div style="flex:1; min-width:0;">
                <div style="
                    font-weight: 600; color: #e2e8f0;
                    font-size: 0.9rem;
                    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
                ">{file.original_name}</div>
                <div style="display:flex; gap:8px; margin-top:6px; flex-wrap:wrap; align-items:center;">
                    <span style="
                        font-size: 0.7rem; font-weight: 600;
                        color: {status["color"]};
                        background: {status["bg"]};
                        border: 1px solid {status["border"]};
                        border-radius: 20px; padding: 2px 8px;
                    ">{status["icon"]} {status["label"]}</span>
                    <span style="font-size: 0.7rem; color: #475569;">{ext.upper() or "?"} • {file_size_kb:.1f} KB</span>
                </div>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        col_space, col_del = st.columns([3, 1])
        with col_del:
            if st.button(
                "🗑️",
                key=f"lib_del_{file.id}",
                help="Dosyayı sil",
                use_container_width=True,
            ):
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

    # Page Header
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
        ">📚</div>
        <div>
            <div style="font-size: 1.05rem; font-weight: 700; color: #e0e7ff; letter-spacing: -0.02em;">Belge & Çalışma Alanı Yönetimi</div>
            <div style="font-size: 0.78rem; color: #64748b; margin-top: 1px;">Sistemi yapılandırın ve belgelerinizi yönetin</div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Tabs
    tab_stats, tab_manage, tab_upload, tab_files = st.tabs(
        ["📊 Özet", "📁 Çalışma Alanları", "📤 Yükleme", "📄 Tüm Belgeler"]
    )

    with tab_stats:
        if active_ws:
            files = get_cached_files(active_ws.id)
            render_document_stats(files, active_ws.id, active_ws.name)
        else:
            st.info("İstatistikleri görmek için bir çalışma alanı seçin.")

    with tab_manage:
        st.markdown("### 📁 Mevcut Çalışma Alanları")
        workspaces = st.session_state.get(SessionKeys.WORKSPACES.value, [])

        col_ws, col_create = st.columns([4, 1])
        with col_create:
            if st.button("➕ Yeni Alan", use_container_width=True, type="primary"):
                create_workspace_dialog()

        for ws in workspaces:
            is_active = active_ws and ws.id == active_ws.id
            with st.container(border=True):
                c1, c2, c3 = st.columns([0.1, 0.6, 0.3])
                with c1:
                    st.write("✅" if is_active else "📂")
                with c2:
                    st.markdown(f"**{ws.name}**")
                    st.caption(
                        f"{ws.file_count} belge • Son işlem: {ws.last_modified.strftime('%d/%m/%Y')}"
                    )
                with c3:
                    sub1, sub2, sub3 = st.columns(3)
                    with sub1:
                        if st.button("📂", key=f"sel_{ws.id}", help="Seç"):
                            select_workspace_callback(ws.id)
                    with sub2:
                        if st.button("📝", key=f"ren_{ws.id}", help="Ad değiştir"):
                            rename_workspace_dialog(ws.id, ws.name)
                    with sub3:
                        if st.button("🗑️", key=f"del_{ws.id}", help="Sil"):
                            delete_workspace_confirm_dialog(ws.id, ws.name)

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
                files = get_cached_files(active_ws.id)

                if not files:
                    st.info("Bu çalışma alanında henüz belge yok.")
                else:
                    # Filter & Actions bar
                    col_f, col_r = st.columns([3, 1])
                    with col_f:
                        status_filter = st.selectbox(
                            "Duruma Göre Filtrele",
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
                        if st.button("🔄 Yenile", use_container_width=True):
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
