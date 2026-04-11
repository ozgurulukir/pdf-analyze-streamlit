"""Workspace UI components - sidebar and file management."""

from datetime import datetime
from typing import Callable, List, Optional

import streamlit as st

from app.core.models import FileMetadata, Job, Workspace


def render_workspace_selector(
    workspaces: List[Workspace],
    active_workspace: Optional[Workspace],
    on_create: Callable,
    on_select: Callable,
    on_delete: Callable,
    on_rename: Callable,
):
    """Render workspace selector in sidebar."""
    st.markdown("### 📁 Çalışma Alanları")

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
                    if st.button("📂", key=f"sel_{ws.id}", help="Seç"):
                        on_select(ws.id)
            with col2:
                st.markdown(f"**{ws.name}**")
                st.caption(
                    f"{ws.file_count} dosya • {ws.last_modified.strftime('%d/%m/%Y')}"
                )

                # Simple rename expander
                with st.expander("📝 İsmi Değiştir", expanded=False):
                    new_name = st.text_input(
                        "Yeni İsim",
                        value=ws.name,
                        key=f"rename_input_{ws.id}",
                        label_visibility="collapsed",
                    )
                    if st.button("Güncelle", key=f"rename_btn_{ws.id}"):
                        on_rename(ws.id, new_name)
            with col3:
                if st.button("🗑️", key=f"del_ws_{ws.id}", help="Sil"):
                    on_delete(ws.id)

    render_workspaces_list()
    st.divider()

    @st.fragment
    def render_create_workspace():
        # Create new workspace
        with st.expander("➕ Yeni Çalışma Alanı", expanded=False):
            new_name = st.text_input("İsim", key="new_workspace_name")
            if st.button("Oluştur", key="create_workspace_btn"):
                if new_name.strip():
                    on_create(new_name)

    render_create_workspace()


def render_file_card(
    file: FileMetadata,
    on_delete: Callable,
    on_revectorize: Callable,
    on_preview: Callable,
):
    """Render a premium file card."""
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
        css_styles=f"""
            {{
                background: rgba(30, 41, 59, 0.4);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                padding: 1rem;
                margin-bottom: 1rem;
                transition: all 0.3s ease;
            }}
        """,
    ):
        # File Info Row
        col_icon, col_text = st.columns([1, 6])
        with col_icon:
            st.markdown(
                f"<div style='font-size: 2rem; text-align: center;'>📄</div>",
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
            if st.button("👁️ İzle", key=f"prev_{file.id}", use_container_width=True):
                on_preview(file)
        with btn_col2:
            if st.button(
                "🔄 Sync",
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
                if st.button("🗑️ Sil", key=f"del_{file.id}", use_container_width=True):
                    on_delete(file.id)


def render_file_list(
    files: List[FileMetadata],
    on_delete: Callable,
    on_revectorize: Callable,
    on_preview: Callable,
):
    """Render list of files in workspace."""
    if not files:
        st.markdown(f"### 📄 Dosyalar (0)")
        st.info("Henüz dosya yok. Dosya yükleyin.")
        return

    # Wrap file list in an expander for better space management
    with st.expander(f"📄 Mevcut Dosyalar ({len(files)})", expanded=True):
        for file in files:
            render_file_card(file, on_delete, on_revectorize, on_preview)


def render_upload_zone(on_upload: Callable, allowed_types: List[str] = None):
    """Render file upload zone."""
    st.markdown("### 📤 Dosya Yükle")

    if allowed_types is None:
        allowed_types = ["pdf", "txt", "docx", "html", "md"]

    uploaded_files = st.file_uploader(
        "Dosya seçin",
        type=allowed_types,
        accept_multiple_files=True,
        help="PDF, TXT, DOCX, HTML veya MD dosyaları",
        label_visibility="collapsed",
    )

    if uploaded_files:
        st.write(f"{len(uploaded_files)} dosya seçildi")

        if st.button("📤 Yükle ve İşle", type="primary", use_container_width=True):
            on_upload(uploaded_files)

        return uploaded_files

    return None


def render_job_progress(job: Job):
    """Render job progress bar."""
    if job.status in ("pending", "running"):
        st.progress(job.progress / 100, text=f"{job.status}... {job.progress:.0f}%")
    elif job.status == "completed":
        st.success("✅ Tamamlandı")
    elif job.status == "failed":
        st.error(f"❌ Başarısız: {job.error_message}")


def render_active_jobs(jobs: List[Job]):
    """Render active jobs in workspace."""
    if not jobs:
        return

    st.markdown("### ⚙️ İşlemler")

    for job in jobs:
        with st.expander(
            f"{'🔄' if job.status == 'running' else '⏳'} {job.job_type} - {job.progress:.0f}%"
        ):
            render_job_progress(job)


def render_workspace_modal(
    is_open: bool,
    workspaces: List[Workspace],
    on_create: Callable,
    on_select: Callable,
    on_delete: Callable,
):
    """Render workspace selector as modal/panel."""
    if not is_open:
        return

    with st.container():
        st.markdown("### 📁 Çalışma Alanları")

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
        new_name = st.text_input("Yeni çalışma alanı", key="modal_new_workspace")


def render_document_stats(
    files: List[FileMetadata], workspace_id: str, workspace_name: str
):
    """Render document statistics and vector store info."""
    if not files:
        st.warning("⚠️ Bu çalışma alanında henüz belge yok.")
        return

    from app.core.chroma import ChromaManager

    chroma_manager = ChromaManager()
    chunk_count = chroma_manager.get_chunk_count(workspace_id, workspace_name)

    total_size = sum(f.size for f in files) / 1024  # KB
    processed = len([f for f in files if f.status == "processed"])

    st.markdown(
        f"""
    <div style="background: rgba(30, 41, 59, 0.6); border-radius: 12px; padding: 1rem; border: 1px solid rgba(255, 255, 255, 0.1);">
        <div style="font-size: 0.8rem; color: #6366f1; font-weight: bold; margin-bottom: 8px;">📊 ÇALIŞMA ALANI ÖZETİ</div>
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span style="color: #f8fafc;">📁 Toplam Belge</span>
            <span style="color: #f8fafc; font-weight: 600;">{len(files)}</span>
        </div>
        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 4px;">
            <span style="color: #10b981;">✅ İşlenen</span>
            <span style="color: #10b981; font-weight: 600;">{processed}</span>
        </div>
        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 4px;">
            <span style="color: #06b6d4;">🧬 Vektör Sayısı</span>
            <span style="color: #06b6d4; font-weight: 600;">{chunk_count}</span>
        </div>
        <div style="font-size: 0.75rem; color: #94a3b8; margin-top: 10px; border-top: 1px solid rgba(255, 255, 255, 0.05); padding-top: 8px;">
            Boyut: {total_size:.1f} KB &nbsp;•&nbsp; {workspace_name}
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    if chunk_count == 0 and processed > 0:
        st.warning(
            "⚠️ Belgeler işlenmiş görünüyor ama vektör veritabanı boş. Lütfen 'Belgeler' sayfasından tekrar işlemeyi deneyin."
        )
