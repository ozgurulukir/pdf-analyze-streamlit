"""Workspace UI components - sidebar and file management."""
import streamlit as st
from typing import List, Optional, Callable
from datetime import datetime

from app.core.models import Workspace, FileMetadata, Job


def render_workspace_selector(
    workspaces: List[Workspace],
    active_workspace: Optional[Workspace],
    on_create: Callable,
    on_select: Callable,
    on_delete: Callable,
    on_rename: Callable
):
    """Render workspace selector in sidebar."""
    st.markdown("### 📁 Çalışma Alanları")
    
    # Workspace list
    for ws in workspaces:
        is_active = active_workspace and ws.id == active_workspace.id
        
        col1, col2 = st.columns([1, 4])
        with col1:
            if is_active:
                st.success("✅")
            else:
                if st.button("📂", key=f"sel_{ws.id}", help="Seç"):
                    on_select(ws.id)
        with col2:
            st.markdown(f"**{ws.name}**")
            st.caption(f"{ws.file_count} dosya • {ws.last_modified.strftime('%d/%m/%Y')}")
    
    st.divider()
    
    # Create new workspace
    with st.expander("➕ Yeni Çalışma Alanı", expanded=False):
        new_name = st.text_input("İsim", key="new_workspace_name")
        if st.button("Oluştur", key="create_workspace_btn"):
            if new_name.strip():
                on_create(new_name)


def render_file_card(
    file: FileMetadata,
    on_delete: Callable,
    on_revectorize: Callable,
    on_preview: Callable
):
    """Render a file card."""
    # Status icon
    status_icon = {
        "pending": "⏳",
        "processing": "⚙️",
        "processed": "✅",
        "error": "❌"
    }.get(file.status, "❓")
    
    with st.container():
        st.markdown(f"""
        <div class="file-card" style="
            background: white;
            border-radius: 12px;
            padding: 1rem;
            margin: 0.5rem 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        ">
            <div style="display: flex; align-items: center; gap: 10px;">
                <span style="font-size: 1.5rem;">📄</span>
                <div style="flex: 1;">
                    <strong>{file.original_name}</strong>
                    <br>
                    <small style="color: #666;">
                        {status_icon} {file.status} • {file.size // 1024} KB • {file.chunk_count} chunk
                    </small>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Action buttons
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("👁️ Önizleme", key=f"prev_{file.id}", use_container_width=True):
                on_preview(file)
        with col2:
            if st.button("🔄 Yeniden", key=f"rev_{file.id}", use_container_width=True, disabled=file.status != "processed"):
                on_revectorize(file.id)
        with col3:
            if st.button("🗑️ Sil", key=f"del_{file.id}", use_container_width=True):
                on_delete(file.id)


def render_file_list(
    files: List[FileMetadata],
    on_delete: Callable,
    on_revectorize: Callable,
    on_preview: Callable
):
    """Render list of files in workspace."""
    st.markdown(f"### 📄 Dosyalar ({len(files)})")
    
    if not files:
        st.info("Henüz dosya yok. Dosya yükleyin.")
        return
    
    for file in files:
        render_file_card(file, on_delete, on_revectorize, on_preview)


def render_upload_zone(
    on_upload: Callable,
    allowed_types: List[str] = None
):
    """Render file upload zone."""
    st.markdown("### 📤 Dosya Yükle")
    
    if allowed_types is None:
        allowed_types = ["pdf", "txt", "docx", "html", "md"]
    
    uploaded_files = st.file_uploader(
        "Dosya seçin",
        type=allowed_types,
        accept_multiple_files=True,
        help="PDF, TXT, DOCX, HTML veya MD dosyaları",
        label_visibility="collapsed"
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
        with st.expander(f"{'🔄' if job.status == 'running' else '⏳'} {job.job_type} - {job.progress:.0f}%"):
            render_job_progress(job)


def render_workspace_sidebar(
    workspace: Optional[Workspace],
    files: List[FileMetadata],
    jobs: List[Job],
    callbacks: dict
):
    """Render complete workspace sidebar."""
    
    if workspace:
        st.markdown(f"## 📂 {workspace.name}")
        st.caption(f"{workspace.file_count} dosya")
    else:
        st.markdown("## 📂 Çalışma Alanı")
        st.info("Çalışma alanı seçin veya oluşturun")
        return
    
    st.divider()
    
    # Jobs
    if jobs:
        render_active_jobs(jobs)
        st.divider()
    
    # Files
    render_file_list(
        files,
        on_delete=callbacks.get("on_delete_file"),
        on_revectorize=callbacks.get("on_revectorize"),
        on_preview=callbacks.get("on_preview")
    )
    
    st.divider()
    
    # Upload
    render_upload_zone(
        on_upload=callbacks.get("on_upload"),
        allowed_types=["pdf", "txt", "docx", "html", "md"]
    )


def render_workspace_modal(
    is_open: bool,
    workspaces: List[Workspace],
    on_create: Callable,
    on_select: Callable,
    on_delete: Callable
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
                if st.button(ws.name, key=f"modal_sel_{ws.id}", use_container_width=True):
                    on_select(ws.id)
            with col3:
                if st.button("🗑️", key=f"modal_del_{ws.id}"):
                    on_delete(ws.id)
        
        st.divider()
        
        # Create new
        new_name = st.text_input("Yeni çalışma alanı", key="modal_new_workspace")
        if st.button("➕ Oluştur", key="modal_create_btn"):
            if new_name.strip():
                on_create(new_name)
