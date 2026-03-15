"""File upload component with drag and drop support."""
import streamlit as st
from streamlit_extras.card import card
from streamlit_extras.stylable_container import stylable_container

from app.core.loader import DocumentLoader


def render_upload_zone():
    """Render modern file upload zone."""

    st.subheader("📤 Dosya Yükle")

    # Accepted file types
    accepted_types = ["pdf", "txt", "md"]

    # Modern file uploader with drag & drop
    uploaded_files = st.file_uploader(
        "Belge yükleyin",
        type=accepted_types,
        accept_multiple_files=True,
        help="PDF, TXT veya MD dosyaları yükleyebilirsiniz",
        label_visibility="collapsed"
    )

    return uploaded_files


def render_uploaded_files(uploaded_files):
    """Render cards for uploaded files."""

    if not uploaded_files:
        return []

    st.markdown("### 📁 Yüklenen Dosyalar")

    cols = st.columns(min(len(uploaded_files), 3))

    for idx, file in enumerate(uploaded_files):
        col = cols[idx % 3]

        with col:
            # File info
            file_ext = file.name.split('.')[-1].upper()
            file_size = file.size / 1024  # KB

            # Icon based on type
            icon = "📄" if file_ext == "PDF" else "📝"

            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 10px;
                padding: 1rem;
                margin: 0.5rem 0;
                color: white;
            ">
                <div style="font-size: 2rem;">{icon}</div>
                <div style="font-weight: bold; margin-top: 0.5rem;">{file.name}</div>
                <div style="font-size: 0.8rem; opacity: 0.8;">
                    {file_ext} • {file_size:.1f} KB
                </div>
            </div>
            """, unsafe_allow_html=True)

    return uploaded_files


def render_process_button(uploaded_files, key: str = "process"):
    """Render process button with loading state."""

    if not uploaded_files:
        return False

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        process_btn = st.button(
            "🚀 Belgeleri İşle",
            type="primary",
            use_container_width=True,
            key=key
        )

    return process_btn


def render_processing_status(status: str, progress: float = None):
    """Render processing status with progress."""

    if progress is not None:
        progress_bar = st.progress(progress)
        st.text(status)
        return progress_bar
    else:
        return st.info(f"⏳ {status}")


def render_document_stats(documents):
    """Render document statistics."""

    if not documents:
        return

    total_chars = sum(len(doc.page_content) for doc in documents)
    total_docs = len(documents)

    # Get unique sources
    sources = list(set(doc.metadata.get("source", "Unknown") for doc in documents))

    # Display metrics
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("📄 Toplam Belge", total_docs)

    with col2:
        st.metric("📝 Toplam Karakter", f"{total_chars:,}")

    with col3:
        st.metric("📁 Benzersiz Dosya", len(sources))

    # Show sources
    with st.expander("📋 Kaynak Dosyalar"):
        for source in sources:
            st.write(f"- {source}")
