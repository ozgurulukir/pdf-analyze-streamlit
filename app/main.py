"""Main application - PDF Analyzer Pro with tilted-T layout + Ollama + Custom LLM."""
import os
import sys
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(
    page_title="PDF Analyzer Pro",
    page_icon="pdf",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import core modules
from app.core import (
    AppConfig, DatabaseManager, DocumentLoader, 
    Workspace, FileMetadata, Message, QAPair, UserPreferences,
    get_job_queue, create_embedding_job,
    ChromaManager, EmbeddingManager, ChunkManager, QUICK_PROMPTS,
    create_llm, RAGChain, PreferenceManager, QAManager
)

from app.ui.sidebar import (
    render_llm_settings,
    render_embedding_settings,
    render_data_settings,
    render_workspace_selector,
    render_file_list,
    render_job_progress
)
from app.ui.layout import apply_layout_styles

# ============= Session State =============

def init_session_state():
    defaults = {
        "active_workspace_id": None,
        "workspaces": [],
        "chat_history": [],
        "sidebar_open": True,
        "current_page": "chat",
        "preferences": UserPreferences(),
        # LLM defaults
        "llm_model": "deepseek-v3.1:671b-cloud",
        "llm_base_url": "https://ollama.com/v1",
        "llm_api_key": "ollama",
        "llm_temperature": 0.3,
        # Embedding defaults
        "use_huggingface": False,
        "embed_model": "nomic-embed-text",
        "ollama_url": "http://localhost:11434",
        "hf_embed_model": "sentence-transformers/all-MiniLM-L6-v2",
        # Data defaults
        "data_dir": "./data",
        "chroma_path": "./chroma_db",
        "chunk_size": 1000,
        "chunk_overlap": 200,
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# ============= Callback Functions =============

def process_directory_callback(directory_path, workspace):
    if not directory_path or not workspace:
        st.error("Dizin yolu ve Workspace seçilmelidir.")
        return
    
    with st.spinner("Dizin taranıyor..."):
        loader = DocumentLoader()
        documents = loader.load_directory(directory_path)
        
        if not documents:
            st.warning("Dizinde uygun belge bulunamadı.")
            return

        db = DatabaseManager()
        files_to_process = []
        
        for doc in documents:
            file_meta = FileMetadata(
                workspace_id=workspace.id,
                filename=os.path.basename(doc.metadata.get("source", "unknown")),
                original_name=os.path.basename(doc.metadata.get("source", "unknown")),
                file_type=doc.metadata.get("source", "").split('.')[-1].lower(),
                size=len(doc.page_content),
                status="pending"
            )
            db.create_file(file_meta)
            
            files_to_process.append({
                "id": file_meta.id,
                "filename": file_meta.filename,
                "text": doc.page_content,
                "file_metadata": file_meta
            })
        
        if files_to_process:
            create_embedding_job(
                files=files_to_process,
                workspace_id=workspace.id,
                workspace_name=workspace.name,
                db=db
            )
            st.success(f"{len(files_to_process)} belge kuyruğa eklendi!")
            st.rerun()

def send_message_callback(user_input, settings):
    if not user_input.strip():
        return
    
    if not st.session_state.active_workspace_id:
        st.error("Lütfen önce bir workspace seçin!")
        return
    
    # Add user message
    msg = Message(role="user", content=user_input)
    st.session_state.chat_history.append(msg)
    
    db = DatabaseManager()
    workspace = db.get_workspace(st.session_state.active_workspace_id)
    
    # Modern LCEL Chain usage
    rag_chain = RAGChain(
        base_url=settings["base_url"],
        api_key=settings["api_key"],
        model=settings["model"],
        temperature=settings["temperature"]
    )
    
    with st.spinner("Düşünüyor..."):
        try:
            answer, sources = rag_chain.query(
                question=user_input,
                workspace_id=workspace.id,
                workspace_name=workspace.name
            )
            
            msg = Message(role="assistant", content=answer, sources=sources)
            st.session_state.chat_history.append(msg)
            
            # Save to DB
            msg_db_user = Message(role="user", content=user_input, workspace_id=workspace.id)
            db.add_message(msg_db_user)
            msg_db_assistant = Message(role="assistant", content=answer, sources=sources, workspace_id=workspace.id)
            db.add_message(msg_db_assistant)
            
        except Exception as e:
            st.error(f"Hata: {e}")

# ============= Main layout rendering =============

def render_sidebar():
    settings = {}
    with st.sidebar:
        st.markdown("<h1 style='text-align: center; color: #6366f1;'>PREMIUM RAG</h1>", unsafe_allow_html=True)
        st.divider()
        
        # Model & API Settings
        with st.expander("🛠️ Model Ayarları", expanded=True):
            llm_settings = render_llm_settings()
            settings.update(llm_settings)
            
            embed_settings = render_embedding_settings()
            settings.update(embed_settings)
        
        st.divider()
        
        # Workspace Selection
        render_workspace_selector(
            workspaces=st.session_state.workspaces,
            active_workspace=None,
            on_create=lambda name: None, # Need to fix these callbacks in refactor
            on_select=lambda id: None,
            on_delete=lambda id: None
        )
        
        st.divider()
        
        # Data Management
        with st.expander("📂 Veri Yönetimi", expanded=False):
            data_settings = render_data_settings()
            settings.update(data_settings)
            
            st.markdown("---")
            dir_path = st.text_input("📁 Yerel Dizin Yolu", placeholder="/path/to/pdfs")
            if st.button("Dizini İndeksle", use_container_width=True):
                db = DatabaseManager()
                ws = db.get_workspace(st.session_state.active_workspace_id)
                process_directory_callback(dir_path, ws)
            
            st.markdown("---")
            uploaded = st.file_uploader("📄 Dosya Yükle", accept_multiple_files=True)
            if uploaded and st.button("Dosyaları İşle", type="primary", use_container_width=True):
                db = DatabaseManager()
                ws = db.get_workspace(st.session_state.active_workspace_id)
                # upload_files_callback logic here or as separate call
        
        st.divider()
        if st.button("🧹 Sohbeti Temizle", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()
            
    return settings

def main():
    init_session_state()
    apply_layout_styles()
    
    # Load and render sidebar
    from app.main import load_workspaces # Ensure this is accessible
    # load_workspaces() - This needs careful handling in real run
    settings = render_sidebar()
    
    # Navigation
    st.sidebar.markdown("---")
    selected_page = st.sidebar.selectbox("📍 Menü", ["Sohbet", "Belgeler", "Analiz"])
    
    if selected_page == "Sohbet":
        # Header
        st.markdown(f"""
            <div style='text-align: left; margin-bottom: 2rem;'>
                <h2 style='margin-bottom: 0;'>🤖 Belge Analiz Uzmanı</h2>
                <p style='color: #94a3b8;'>Model: {settings.get('model', 'N/A')} | Bağlam odaklı akıllı analiz</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Chat Messages Container
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        if not st.session_state.chat_history:
            st.info("Kayıtlı belge bulunamadı veya henüz soru sorulmadı. Analize başlamak için dosya yükleyin veya bir dizin belirtin.")
        else:
            for msg in st.session_state.chat_history:
                role_class = "user-msg" if msg.role == "user" else "assistant-msg"
                avatar = "👤" if msg.role == "user" else "🤖"
                with st.chat_message(msg.role):
                    st.markdown(msg.content)
                    if hasattr(msg, 'sources') and msg.sources:
                        with st.expander("📌 Kaynaklar"):
                            for s in msg.sources:
                                st.caption(s)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Input Bar Space
        st.markdown("<div style='height: 100px;'></div>", unsafe_allow_html=True)
        
        # Fixed Input Bar at bottom
        st.markdown('<div class="input-bar-container">', unsafe_allow_html=True)
        
        # Quick Prompts
        cols = st.columns(len(QUICK_PROMPTS))
        for idx, p in enumerate(QUICK_PROMPTS):
            with cols[idx]:
                if st.button(p, key=f"q_{idx}", use_container_width=True):
                    send_message_callback(p, settings)
                    st.rerun()

        prompt = st.chat_input("Belgelerinize bir soru sorun...")
        if prompt:
            send_message_callback(prompt, settings)
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    elif selected_page == "Belgeler":
        st.title("📚 Kütüphane")
        st.write("Yüklenen ve işlenen tüm belgelerin listesi.")
        # render_file_list implementation here
        
    elif selected_page == "Analiz":
        st.title("📊 Veri Analizi")
        st.info("Bu bölüm geliştirme aşamasındadır.")

if __name__ == "__main__":
    main()
