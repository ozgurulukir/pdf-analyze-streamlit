"""Sidebar components for settings."""
import streamlit as st
from typing import List, Optional, Callable

from app.core.config import (
    LLM_MODEL_OPTIONS, 
    EMBED_MODEL_OPTIONS, 
    HF_EMBED_OPTIONS,
    get_ollama_models,
    get_ollama_llm_models
)


def render_llm_settings():
    """Render LLM settings in sidebar."""
    st.subheader("🤖 LLM Ayarları")
    
    # Endpoint türü seçimi
    endpoint_type = st.radio(
        "Endpoint Türü",
        ["Ollama Cloud / Custom", "Yerel Ollama"],
        index=0,
        key="endpoint_type_radio"
    )
    
    # Get current Ollama URL
    ollama_url = st.session_state.get("ollama_url", "http://localhost:11434")
    
    # Base URL
    if endpoint_type == "Yerel Ollama":
        base_url = st.text_input(
            "Ollama URL",
            value=st.session_state.get("ollama_url", "http://localhost:11434"),
            key="llm_ollama_url_input",
            help="Yerel Ollama sunucu adresi"
        )
    else:
        base_url = st.text_input(
            "Base URL",
            value=st.session_state.get("llm_base_url", "https://ollama.com/v1"),
            key="llm_base_url_input",
            help="OpenAI-compatible API endpoint (Ollama Cloud, vLLM, Groq, Together vb.)"
        )
    
    st.session_state.llm_base_url = base_url
    
    # Model seçimi - dinamik olarak Ollama'dan çek
    col1, col2 = st.columns([3, 1])
    with col1:
        # Model seçim türü
        use_custom_model = st.checkbox("Özel model adı kullan", value=False, key="use_custom_llm_model")
        
        if use_custom_model:
            # Kullanıcı kendi model adını girer
            llm_model = st.text_input(
                "Model Adı",
                value=st.session_state.get("llm_model", ""),
                key="llm_model_custom_input",
                placeholder="örn: deepseek-v2:671b, qwen2.5:7b, llama3.1:8b"
            )
        else:
            # Refresh butonu için session state kontrolü
            if "ollama_llm_models" not in st.session_state:
                st.session_state.ollama_llm_models = get_ollama_llm_models(ollama_url)
            
            llm_models = st.session_state.ollama_llm_models
            model_labels = [m["value"] for m in llm_models]
            current_model = st.session_state.get("llm_model", llm_models[0]["value"] if llm_models else "deepseek-v2:671b")
            
            # Validate current model exists in list
            if current_model not in model_labels:
                current_model = llm_models[0]["value"] if llm_models else "deepseek-v2:671b"
                model_index = 0
            else:
                model_index = model_labels.index(current_model)
            
            llm_model = st.selectbox(
                "Model",
                options=model_labels,
                format_func=lambda x: next((m["label"] for m in llm_models if m["value"] == x), x),
                index=model_index,
                key="llm_model_select"
            )
    
    with col2:
        st.write("")  # Alignment
        st.write("")  
        if not use_custom_model:
            if st.button("🔄", key="refresh_llm_models", help="Modelleri yenile"):
                st.session_state.ollama_llm_models = get_ollama_llm_models(ollama_url)
                st.rerun()
    
    # API Key
    api_key = st.text_input(
        "API Key",
        type="password",
        value=st.session_state.get("llm_api_key", "ollama"),
        key="llm_api_key_input",
        help="API anahtarı (Ollama Cloud için gerekli)"
    )
    
    # Temperature
    temperature = st.slider(
        "Temperature",
        min_value=0.0,
        max_value=1.0,
        value=st.session_state.get("llm_temperature", 0.3),
        step=0.1,
        key="llm_temp_slider"
    )
    
    # Save to session
    st.session_state.llm_model = llm_model
    st.session_state.llm_api_key = api_key
    st.session_state.llm_temperature = temperature
    
    return {
        "model": llm_model,
        "base_url": base_url,
        "api_key": api_key,
        "temperature": temperature
    }


def render_embedding_settings():
    """Render embedding settings in sidebar."""
    st.subheader("🔢 Embedding Ayarları")
    
    # Embedding türü seçimi
    embed_type = st.radio(
        "Embedding Türü",
        ["Ollama (Yerel)", "HuggingFace"],
        index=0 if not st.session_state.get("use_huggingface", False) else 1,
        key="embed_type_radio"
    )
    
    use_huggingface = (embed_type == "HuggingFace")
    st.session_state.use_huggingface = use_huggingface
    
    # Ollama URL input
    ollama_url = st.text_input(
        "Ollama URL",
        value=st.session_state.get("ollama_url", "http://localhost:11434"),
        key="ollama_url_input",
        help="Ollama sunucu adresi"
    )
    st.session_state.ollama_url = ollama_url
    
    if use_huggingface:
        # HuggingFace - custom model desteği
        use_custom_hf = st.checkbox("Özel HuggingFace modeli kullan", value=False, key="use_custom_hf_model")
        
        if use_custom_hf:
            embed_model = st.text_input(
                "Model Adı",
                value=st.session_state.get("hf_embed_model", ""),
                key="hf_embed_custom_input",
                placeholder="örn: sentence-transformers/all-MiniLM-L6-v2"
            )
        else:
            hf_index = 0
            hf_models = [m["value"] for m in HF_EMBED_OPTIONS]
            current_hf = st.session_state.get("hf_embed_model", HF_EMBED_OPTIONS[0]["value"])
            if current_hf in hf_models:
                hf_index = hf_models.index(current_hf)
            
            embed_model = st.selectbox(
                "HuggingFace Model",
                options=[m["value"] for m in HF_EMBED_OPTIONS],
                format_func=lambda x: next((m["label"] for m in HF_EMBED_OPTIONS if m["value"] == x), x),
                index=hf_index,
                key="hf_embed_select"
            )
        
        st.session_state.hf_embed_model = embed_model
        st.session_state.embed_model = embed_model
    else:
        # Ollama - custom model desteği
        use_custom_ollama = st.checkbox("Özel Ollama embedding modeli kullan", value=False, key="use_custom_embed_model")
        
        if use_custom_ollama:
            embed_model = st.text_input(
                "Embedding Model Adı",
                value=st.session_state.get("embed_model", ""),
                key="ollama_embed_custom_input",
                placeholder="örn: nomic-embed-text, mxbai-embed-large"
            )
        else:
            # Ollama model seçimi - dinamik
            col1, col2 = st.columns([3, 1])
            with col1:
                # Refresh butonu için session state kontrolü
                if "ollama_embed_models" not in st.session_state:
                    st.session_state.ollama_embed_models = get_ollama_models(ollama_url)
                
                embed_models = st.session_state.ollama_embed_models
                embed_labels = [m["value"] for m in embed_models]
                current_ollama = st.session_state.get("embed_model", embed_models[0]["value"] if embed_models else "nomic-embed-text")
                
                # Validate current model exists in list
                if current_ollama not in embed_labels:
                    current_ollama = embed_models[0]["value"] if embed_models else "nomic-embed-text"
                    ollama_index = 0
                else:
                    ollama_index = embed_labels.index(current_ollama)
                
                embed_model = st.selectbox(
                    "Ollama Embedding Modeli",
                    options=embed_labels,
                    format_func=lambda x: next((m["label"] for m in embed_models if m["value"] == x), x),
                    index=ollama_index,
                    key="ollama_embed_select"
                )
            
            with col2:
                st.write("")  # Alignment
                st.write("")  
                if st.button("🔄", key="refresh_embed_models", help="Modelleri yenile"):
                    st.session_state.ollama_embed_models = get_ollama_models(ollama_url)
                    st.rerun()
        
        st.session_state.embed_model = embed_model
    
    return {
        "use_huggingface": use_huggingface,
        "embed_model": embed_model,
        "ollama_url": ollama_url
    }


def render_data_settings():
    """Render data settings in sidebar."""
    st.subheader("📁 Veri Ayarları")
    
    data_dir = st.text_input(
        "Veri Klasörü",
        value=st.session_state.get("data_dir", "./data"),
        key="data_dir_input",
        help="Belgelerin bulunduğu klasör"
    )
    
    chroma_path = st.text_input(
        "Chroma Path",
        value=st.session_state.get("chroma_path", "./chroma_db"),
        key="chroma_path_input",
        help="Vector store klasörü"
    )
    
    chunk_size = st.number_input(
        "Chunk Size",
        min_value=100,
        max_value=2000,
        value=st.session_state.get("chunk_size", 1000),
        step=100,
        key="chunk_size_input"
    )
    
    chunk_overlap = st.number_input(
        "Chunk Overlap",
        min_value=0,
        max_value=500,
        value=st.session_state.get("chunk_overlap", 200),
        step=50,
        key="chunk_overlap_input"
    )
    
    # Save to session
    st.session_state.data_dir = data_dir
    st.session_state.chroma_path = chroma_path
    st.session_state.chunk_size = chunk_size
    st.session_state.chunk_overlap = chunk_overlap
    
    return {
        "data_dir": data_dir,
        "chroma_path": chroma_path,
        "chunk_size": chunk_size,
        "chunk_overlap": chunk_overlap
    }


def render_workspace_selector(
    workspaces: List,
    active_workspace: Optional,
    on_create: Callable,
    on_select: Callable,
    on_delete: Callable
):
    """Render workspace selector."""
    st.markdown("### 📁 Çalışma Alanları")
    
    for ws in workspaces:
        is_active = active_workspace and ws.id == active_workspace.id
        
        col1, col2 = st.columns([1, 4])
        with col1:
            if is_active:
                st.success("✅")
            else:
                if st.button("📂", key=f"sel_{ws.id}"):
                    on_select(ws.id)
        with col2:
            st.markdown(f"**{ws.name}**")
            st.caption(f"{ws.file_count} dosya")
    
    st.divider()
    
    with st.expander("➕ Yeni Çalışma Alanı", expanded=False):
        new_name = st.text_input("İsim", key="new_workspace_name")
        if st.button("Oluştur", key="create_workspace_btn"):
            if new_name.strip():
                on_create(new_name)


def render_file_list(files: List, on_delete: Callable):
    """Render file list."""
    st.markdown(f"### 📄 Dosyalar ({len(files)})")
    
    for file in files:
        status_icon = {
            "pending": "⏳",
            "processing": "⚙️",
            "processed": "✅",
            "error": "❌"
        }.get(file.status, "❓")
        
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"📄 **{file.original_name}**")
            st.caption(f"{status_icon} {file.status} • {file.size // 1024} KB")
        with col2:
            if st.button("🗑️", key=f"del_{file.id}"):
                on_delete(file.id)


def render_job_progress(job):
    """Render job progress."""
    if job.status in ("pending", "running"):
        st.progress(job.progress / 100, text=f"{job.status}... {job.progress:.0f}%")
    elif job.status == "completed":
        st.success("✅ Tamamlandı")
    elif job.status == "failed":
        st.error(f"❌ Başarısız: {job.error_message}")
