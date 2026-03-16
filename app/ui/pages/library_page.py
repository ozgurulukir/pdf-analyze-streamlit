"""Library page component."""
import streamlit as st
from app.core import DatabaseManager
from app.core.constants import SessionKeys
from app.ui.callbacks import delete_file_callback

STATUS_CONFIG = {
    "processed": {"icon": "✅", "color": "#10b981", "bg": "rgba(16,185,129,0.1)", "border": "rgba(16,185,129,0.25)", "label": "İşlendi"},
    "processing": {"icon": "⚙️", "color": "#6366f1", "bg": "rgba(99,102,241,0.1)", "border": "rgba(99,102,241,0.25)", "label": "İşleniyor"},
    "pending": {"icon": "⏳", "color": "#f59e0b", "bg": "rgba(245,158,11,0.1)", "border": "rgba(245,158,11,0.25)", "label": "Bekliyor"},
    "error": {"icon": "❌", "color": "#ef4444", "bg": "rgba(239,68,68,0.1)", "border": "rgba(239,68,68,0.25)", "label": "Hata"},
}
FILE_ICONS = {"pdf": "📕", "txt": "📄", "docx": "📘", "md": "📝", "html": "🌐"}


def render_file_card_visual(file, on_delete):
    """Render a premium glassmorphism file card."""
    ext = (file.file_type or "").lower()
    file_icon = FILE_ICONS.get(ext, "📄")
    file_size_kb = file.size / 1024 if file.size else 0
    status = STATUS_CONFIG.get(file.status, STATUS_CONFIG["pending"])

    st.markdown(f"""
    <div style="
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(99, 102, 241, 0.15);
        border-radius: 14px;
        padding: 1.25rem;
        margin-bottom: 0.75rem;
        transition: all 0.2s ease;
        backdrop-filter: blur(8px);
    ">
        <div style="display:flex; align-items:flex-start; gap:12px;">
            <div style="
                width: 42px; height: 42px; flex-shrink: 0;
                background: linear-gradient(135deg, rgba(99,102,241,0.15), rgba(124,58,237,0.15));
                border: 1px solid rgba(99,102,241,0.2);
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
                        color: {status['color']};
                        background: {status['bg']};
                        border: 1px solid {status['border']};
                        border-radius: 20px; padding: 2px 8px;
                    ">{status['icon']} {status['label']}</span>
                    <span style="font-size: 0.7rem; color: #475569;">{ext.upper() or '?'} • {file_size_kb:.1f} KB • {file.chunk_count or 0} chunk</span>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🗑️ Sil", key=f"lib_del_{file.id}", use_container_width=True):
        on_delete(file.id)


def render_library_page(settings: dict):
    """Render the document library page with tabbed management view."""
    from app.ui.workspace import (
        render_workspace_selector, 
        render_upload_zone, 
        render_document_stats
    )
    from app.ui.callbacks import (
        create_workspace_callback,
        select_workspace_callback,
        delete_workspace_callback,
        rename_workspace_callback,
        upload_files_callback,
        delete_file_callback
    )
    
    # Page Header
    st.markdown("""
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
    """, unsafe_allow_html=True)

    db = DatabaseManager()
    active_ws_id = st.session_state.get(SessionKeys.ACTIVE_WORKSPACE_ID.value)
    active_ws = db.get_workspace(active_ws_id) if active_ws_id else None
    
    # Define Tabs
    tab_stats, tab_manage, tab_upload, tab_files = st.tabs([
        "📊 Özet", 
        "📁 Çalışma Alanları", 
        "📤 Yükleme", 
        "📄 Tüm Belgeler"
    ])

    with tab_stats:
        if active_ws:
            files = db.get_files(active_ws.id)
            render_document_stats(files, active_ws.id, active_ws.name)
        else:
            st.info("İstatistikleri görmek için bir çalışma alanı seçin.")

    with tab_manage:
        render_workspace_selector(
            workspaces=st.session_state.get(SessionKeys.WORKSPACES.value, []),
            active_workspace=active_ws,
            on_create=create_workspace_callback,
            on_select=select_workspace_callback,
            on_delete=delete_workspace_callback,
            on_rename=rename_workspace_callback
        )

    with tab_upload:
        if active_ws:
            st.markdown(f"#### 📤 '{active_ws.name}' Alanına Yükle")
            # Using standardized settings passed from main orchestration
            render_upload_zone(
                on_upload=lambda files: upload_files_callback(files, active_ws, settings)
            )
        else:
            st.warning("Dosya yüklemek için önce bir çalışma alanı seçin.")

    with tab_files:
        if not active_ws:
            st.info("Belgelerini listelemek için bir çalışma alanı seçin.")
        else:
            @st.fragment
            def render_filtered_file_list():
                files = db.get_files(active_ws.id)
                if not files:
                    st.info("Bu çalışma alanında henüz belge yok.")
                else:
                    # Filter bar
                    status_filter = st.selectbox(
                        "Duruma Göre Filtrele",
                        options=["Tümü", "processed", "pending", "processing", "error"],
                        key="lib_status_filter",
                        label_visibility="collapsed",
                    )
                    filtered = files if status_filter == "Tümü" else [f for f in files if f.status == status_filter]
                    st.markdown(f"<div style='color:#64748b; font-size:0.8rem; margin-bottom:0.75rem;'>{len(filtered)} belge gösteriliyor</div>", unsafe_allow_html=True)
                    
                    cols = st.columns(2)
                    for idx, file in enumerate(filtered):
                        with cols[idx % 2]:
                            render_file_card_visual(file, delete_file_callback)
            
            render_filtered_file_list()
