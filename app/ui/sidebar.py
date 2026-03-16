"""Sidebar components for settings."""
import streamlit as st
from typing import List, Optional, Callable, Dict, Any

from app.core.config import (
    LLM_MODEL_OPTIONS, 
    EMBED_MODEL_OPTIONS, 
    HF_EMBED_OPTIONS,
    get_ollama_models,
    get_ollama_llm_models
)
from app.core.constants import SessionKeys
from app.core.config import AppConfig
from app.ui.workspace import render_job_progress
from app.ui.callbacks import save_settings_callback


def render_llm_settings() -> Dict[str, Any]:
    """Render LLM settings in sidebar with clear provider separation."""
    st.subheader("🤖 LLM Ayarları")
    
    # Endpoint type selection using radio
    endpoint_type_options = ["Ollama Cloud", "Yerel Ollama", "Özel (OpenAI Compatible)"]
    config = AppConfig()
    current_type = st.session_state.get(SessionKeys.LAST_ENDPOINT_TYPE.value, config.DEFAULT_LLM_PROVIDER)
    index = endpoint_type_options.index(current_type) if current_type in endpoint_type_options else 0
    
    endpoint_type = st.radio(
        "Provider / Endpoint",
        endpoint_type_options,
        index=index,
        key="endpoint_type_radio",
        on_change=save_settings_callback
    )
    
    # Standardize session state keys
    current_api_key = st.session_state.get(SessionKeys.OLLAMA_API_KEY.value, "ollama")
    
    # Initialization of internal widgets to avoid state conflict
    if "llm_base_url_input" not in st.session_state:
        st.session_state.llm_base_url_input = st.session_state.get(SessionKeys.LLM_BASE_URL.value, "https://ollama.com/v1")
    if "ollama_api_key_input" not in st.session_state:
        st.session_state.ollama_api_key_input = current_api_key
    
    # Reactive URL logic for endpoint shifts
    if current_type != endpoint_type:
        st.session_state[SessionKeys.LAST_ENDPOINT_TYPE.value] = endpoint_type
        if endpoint_type == "Ollama Cloud":
            st.session_state.llm_base_url_input = "https://ollama.com/v1"
        elif endpoint_type == "Yerel Ollama":
            st.session_state.llm_base_url_input = "http://localhost:11434/v1"
        else:
            st.session_state.llm_base_url_input = st.session_state.get(SessionKeys.LLM_BASE_URL.value, "https://api.openai.com/v1")
        
        # Save immediately when provider changes reactively
        save_settings_callback()
    
    if endpoint_type == "Ollama Cloud":
        st.info("💡 Ollama Cloud için OpenAI-compatible bir endpoint kullanılmaktadır.")

    # Render inputs
    base_url = st.text_input("Base URL", key="llm_base_url_input", help="API endpoint adresi.", on_change=save_settings_callback)
    api_key = st.text_input("API Key / Token", type="password", key="ollama_api_key_input", help="Kimlik doğrulama anahtarı.", on_change=save_settings_callback)
    
    # Model Selection
    is_cloud = (endpoint_type == "Ollama Cloud")
    use_custom_model = st.checkbox("Özel model adı kullan", value=is_cloud, key="use_custom_llm_model", on_change=save_settings_callback)
    
    if use_custom_model:
        current_model = st.session_state.get(SessionKeys.LLM_MODEL.value, "deepseek-v3.1:671b-cloud")
        llm_model = st.text_input("Model Adı", value=current_model, key="llm_model_custom_input", on_change=save_settings_callback)
    else:
        ollama_url = st.session_state.get(SessionKeys.OLLAMA_URL.value, "http://localhost:11434")
        col1, col2 = st.columns([3, 1])
        with col1:
            if "ollama_llm_models" not in st.session_state:
                st.session_state.ollama_llm_models = get_ollama_llm_models(ollama_url)
            
            model_values = [m["value"] for m in st.session_state.ollama_llm_models]
            current_model = st.session_state.get(SessionKeys.LLM_MODEL.value)
            idx = model_values.index(current_model) if current_model in model_values else 0
            
            llm_model = st.selectbox("Model Seçin", options=model_values, index=idx, key="llm_model_select", on_change=save_settings_callback)
        with col2:
            st.write("")
            st.write("")
            if st.button("🔄", key="refresh_llm_models"):
                st.session_state.ollama_llm_models = get_ollama_llm_models(ollama_url)
                st.rerun()

    temperature = st.slider("Temperature", 0.0, 1.0, float(st.session_state.get(SessionKeys.LLM_TEMPERATURE.value, 0.3)), 0.1, key="llm_temp_slider", on_change=save_settings_callback)
    
    # Test Connection Button
    if st.button("🔌 Bağlantıyı Test Et", use_container_width=True):
        from app.core import create_llm
        try:
            with st.status("Bağlantı test ediliyor...", expanded=True) as status:
                test_llm = create_llm(
                    base_url=base_url,
                    api_key=api_key,
                    model=llm_model,
                    temperature=0.1,
                    streaming=False
                )
                response = test_llm.invoke("Sadece 'Bağlantı başarılı' de.")
                status.update(label="✅ Bağlantı Başarılı!", state="complete", expanded=False)
                st.success(f"Model cevabı: {response.content}")
        except Exception as e:
            st.error(f"❌ Bağlantı Hatası: {str(e)}")
    
    # Persistence
    st.session_state[SessionKeys.LLM_BASE_URL.value] = base_url
    st.session_state[SessionKeys.OLLAMA_API_KEY.value] = api_key
    st.session_state[SessionKeys.LLM_MODEL.value] = llm_model
    st.session_state[SessionKeys.LLM_TEMPERATURE.value] = temperature
    
    return {
        "model": llm_model,
        "base_url": base_url,
        "api_key": api_key,
        "temperature": temperature
    }


def render_embedding_settings() -> Dict[str, Any]:
    """Render embedding settings in sidebar."""
    st.subheader("🔢 Embedding Ayarları")
    
    # Provider selection
    embed_type = st.radio(
        "Embedding Türü",
        ["Ollama (Yerel)", "HuggingFace"],
        index=0 if not st.session_state.get(SessionKeys.USE_HUGGINGFACE.value, False) else 1,
        key="embed_type_radio",
        on_change=save_settings_callback
    )
    
    use_huggingface = (embed_type == "HuggingFace")
    st.session_state[SessionKeys.USE_HUGGINGFACE.value] = use_huggingface
    
    ollama_url = st.text_input("Ollama URL", value=st.session_state.get(SessionKeys.OLLAMA_URL.value, "http://localhost:11434"), key="ollama_url_input", on_change=save_settings_callback)
    st.session_state[SessionKeys.OLLAMA_URL.value] = ollama_url
    
    if use_huggingface:
        use_custom_hf = st.checkbox("Özel HF modeli kullan", value=False, key="use_custom_hf_model", on_change=save_settings_callback)
        if use_custom_hf:
            embed_model = st.text_input("HF Model Adı", value=st.session_state.get(SessionKeys.HF_EMBED_MODEL.value, ""), key="hf_embed_custom_input", on_change=save_settings_callback)
        else:
            hf_models = [m["value"] for m in HF_EMBED_OPTIONS]
            curr_hf = st.session_state.get(SessionKeys.HF_EMBED_MODEL.value, HF_EMBED_OPTIONS[0]["value"])
            idx = hf_models.index(curr_hf) if curr_hf in hf_models else 0
            embed_model = st.selectbox("HF Model", options=hf_models, index=idx, key="hf_embed_select", on_change=save_settings_callback)
        
        st.session_state[SessionKeys.HF_EMBED_MODEL.value] = embed_model
        st.session_state[SessionKeys.EMBED_MODEL.value] = embed_model
    else:
        use_custom_ollama = st.checkbox("Özel Ollama embedding kullan", value=False, key="use_custom_embed_model", on_change=save_settings_callback)
        if use_custom_ollama:
            embed_model = st.text_input("Ollama Embed Model", value=st.session_state.get(SessionKeys.EMBED_MODEL.value, ""), key="ollama_embed_custom_input", on_change=save_settings_callback)
        else:
            col1, col2 = st.columns([3, 1])
            with col1:
                if "ollama_embed_models" not in st.session_state:
                    st.session_state.ollama_embed_models = get_ollama_models(ollama_url)
                
                options = [m["value"] for m in st.session_state.ollama_embed_models]
                curr = st.session_state.get(SessionKeys.EMBED_MODEL.value)
                idx = options.index(curr) if curr in options else 0
                embed_model = st.selectbox("Ollama Modeli", options=options, index=idx, key="ollama_embed_select", on_change=save_settings_callback)
            with col2:
                st.write("")
                st.write("")
                if st.button("🔄", key="refresh_embed_models"):
                    st.session_state.ollama_embed_models = get_ollama_models(ollama_url)
                    st.rerun()
        
        st.session_state[SessionKeys.EMBED_MODEL.value] = embed_model
    
    return {
        "use_huggingface": use_huggingface,
        "embed_model": embed_model,
        "ollama_url": ollama_url
    }


def render_data_settings() -> Dict[str, Any]:
    """Render data and system settings."""
    st.subheader("📁 Veri Ayarları")
    
    # Grid for path inputs
    config = AppConfig()
    data_dir = st.text_input("Veri Klasörü", value=st.session_state.get(SessionKeys.DATA_DIR.value, config.DATA_DIR), key="data_dir_input", on_change=save_settings_callback)
    chroma_path = st.text_input("Chroma Path", value=st.session_state.get(SessionKeys.CHROMA_PATH.value, config.CHROMA_PERSIST_DIR), key="chroma_path_input", on_change=save_settings_callback)
    
    col1, col2 = st.columns(2)
    with col1:
        chunk_size = st.number_input("Chunk Size", 100, 2000, int(st.session_state.get(SessionKeys.CHUNK_SIZE.value, 1000)), 100, key="chunk_size_input", on_change=save_settings_callback)
    with col2:
        chunk_overlap = st.number_input("Overlap", 0, 500, int(st.session_state.get(SessionKeys.CHUNK_OVERLAP.value, 200)), 50, key="chunk_overlap_input", on_change=save_settings_callback)
    
    # Persistence
    st.session_state[SessionKeys.DATA_DIR.value] = data_dir
    st.session_state[SessionKeys.CHROMA_PATH.value] = chroma_path
    st.session_state[SessionKeys.CHUNK_SIZE.value] = chunk_size
    st.session_state[SessionKeys.CHUNK_OVERLAP.value] = chunk_overlap
    
    st.divider()
    st.markdown("### ⚠️ Tehlikeli Bölge")
    
    reset_triggered = False
    from streamlit_extras.stylable_container import stylable_container
    with stylable_container(
        key="danger_zone",
        css_styles="button { background-color: #ef4444 !important; color: white !important; }",
    ):
        if st.checkbox("Sıfırlama Kilidini Aç", key="unlock_reset"):
            if st.button("❌ Tüm Sistemi Sıfırla", use_container_width=True):
                reset_triggered = True
    
    return {
        "data_dir": data_dir,
        "chroma_path": chroma_path,
        "chunk_size": chunk_size,
        "chunk_overlap": chunk_overlap,
        "reset_system": reset_triggered
    }

def render_sidebar_branding():
    """Render application branding in sidebar."""
    st.markdown("""
    <div style="text-align:center; padding: 1rem 0 0.5rem;">
        <div style="
            width: 48px; height: 48px;
            background: linear-gradient(135deg, #6366f1, #7c3aed);
            border-radius: 14px;
            display: flex; align-items: center; justify-content: center;
            font-size: 1.5rem;
            margin: 0 auto 0.75rem;
            box-shadow: 0 6px 20px rgba(99,102,241,0.4);
        ">🎯</div>
        <div style="
            font-size: 1rem; font-weight: 800;
            background: linear-gradient(to right, #a5b4fc, #e0e7ff);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            letter-spacing: -0.03em;
        ">PDF ANALYZER PRO</div>
        <div style="font-size: 0.65rem; color: #64748b; margin-top:2px; letter-spacing: 0.08em; text-transform: uppercase;">AI Document Intelligence</div>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

def render_active_workspace_summary(db):
    """Render summary of the active workspace and its processing status."""
    from app.core.jobs import get_job_queue
    
    active_id = st.session_state.get(SessionKeys.ACTIVE_WORKSPACE_ID.value)
    active_ws = db.get_workspace(active_id) if active_id else None
    
    if active_ws:
        st.markdown(f"""
        <div style="background: rgba(99, 102, 241, 0.1); border-radius: 10px; padding: 0.75rem; border: 1px solid rgba(99, 102, 241, 0.2); margin-bottom: 1rem;">
            <div style="font-size: 0.7rem; color: #a5b4fc; font-weight: bold; margin-bottom: 4px;">AKTİF ÇALIŞMA ALANI</div>
            <div style="font-size: 0.9rem; color: #f8fafc; font-weight: 600;">📂 {active_ws.name}</div>
            <div style="font-size: 0.7rem; color: #94a3b8; margin-top: 2px;">{active_ws.file_count} belge yüklü</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Background Job Progress with Fragment for auto-refresh
        job_queue = get_job_queue()
        
        @st.fragment(run_every="3s")
        def job_progress_fragment():
            active_jobs = job_queue.get_active_jobs(active_id)
            if active_jobs:
                st.caption("⚙️ İşlenen Belgeler")
                for job in active_jobs:
                    render_job_progress(job)
                st.divider()
        
        job_progress_fragment()
    else:
        st.info("Çalışma alanı seçilmedi.")
        if st.button("📁 Yönetime Git", use_container_width=True):
            st.session_state[SessionKeys.CURRENT_PAGE.value] = "📁 Belgeler"
            st.rerun()

def render_sidebar_content() -> Dict[str, Any]:
    """
    Consolidated sidebar rendering function.
    
    Returns:
        Dict: Current application settings.
    """
    from app.core.database import DatabaseManager
    db = DatabaseManager()
    config = AppConfig()
    
    with st.sidebar:
        render_sidebar_branding()
        render_active_workspace_summary(db)
        
        # Quick Actions
        st.markdown("<div style='margin-top: auto;'>", unsafe_allow_html=True)
        if st.button("🧹 Sohbeti Temizle", use_container_width=True):
            st.session_state[SessionKeys.CHAT_HISTORY.value] = []
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
            
    # Compile current settings dict for main orchestration
    return {
        "model": st.session_state.get(SessionKeys.LLM_MODEL.value),
        "base_url": st.session_state.get(SessionKeys.LLM_BASE_URL.value),
        "api_key": st.session_state.get(SessionKeys.OLLAMA_API_KEY.value),
        "temperature": st.session_state.get(SessionKeys.LLM_TEMPERATURE.value),
        "chroma_path": st.session_state.get(SessionKeys.CHROMA_PATH.value, config.CHROMA_PERSIST_DIR),
        "data_dir": st.session_state.get(SessionKeys.DATA_DIR.value, config.DATA_DIR),
        "chunk_size": st.session_state.get(SessionKeys.CHUNK_SIZE.value, config.CHUNK_SIZE),
        "chunk_overlap": st.session_state.get(SessionKeys.CHUNK_OVERLAP.value, config.CHUNK_OVERLAP),
        "embedding": {
            "use_huggingface": st.session_state.get(SessionKeys.USE_HUGGINGFACE.value),
            "model_name": st.session_state.get(SessionKeys.EMBED_MODEL.value) if not st.session_state.get(SessionKeys.USE_HUGGINGFACE.value) else st.session_state.get(SessionKeys.HF_EMBED_MODEL.value),
            "ollama_url": st.session_state.get(SessionKeys.OLLAMA_URL.value),
            "chunk_size": st.session_state.get(SessionKeys.CHUNK_SIZE.value, config.CHUNK_SIZE),
            "chunk_overlap": st.session_state.get(SessionKeys.CHUNK_OVERLAP.value, config.CHUNK_OVERLAP)
        }
    }
