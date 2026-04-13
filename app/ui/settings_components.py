import streamlit as st

from app.core.config import AppConfig, get_ollama_llm_models
from app.core.constants import SessionKeys
from app.ui.callbacks import (
    on_embed_type_change_callback,
    on_provider_change_callback,
    save_settings_callback,
    test_connections_callback,
)


def render_llm_settings(key_prefix: str = "") -> None:
    """Render LLM settings using native components."""
    L = st.session_state.locale
    config = AppConfig()
    current_type = st.session_state.get(
        SessionKeys.LAST_ENDPOINT_TYPE.value, config.DEFAULT_LLM_PROVIDER
    )

    endpoint_type = st.selectbox(
        L.settings.provider,
        ["Ollama Cloud", "Yerel Ollama", "Özel (OpenAI Compatible)"],
        index=["Ollama Cloud", "Yerel Ollama", "Özel (OpenAI Compatible)"].index(
            current_type
        )
        if current_type in ["Ollama Cloud", "Yerel Ollama", "Özel (OpenAI Compatible)"]
        else 0,
        key=SessionKeys.LAST_ENDPOINT_TYPE.value,
        on_change=on_provider_change_callback,
    )

    st.markdown(f"**{L.settings.api_connection}**")
    st.text_input(
        L.settings.base_url,
        key=SessionKeys.LLM_BASE_URL.value,
        on_change=save_settings_callback,
    )
    st.text_input(
        L.settings.api_key,
        type="password",
        key=SessionKeys.OLLAMA_API_KEY.value,
        on_change=save_settings_callback,
    )

    st.markdown(f"**{L.settings.model_settings}**")
    is_cloud = endpoint_type == "Ollama Cloud"
    use_custom = st.checkbox(
        L.settings.use_custom_model, value=is_cloud, key=f"{key_prefix}use_custom_llm"
    )

    if use_custom:
        st.text_input(
            L.settings.model_name,
            key=SessionKeys.LLM_MODEL.value,
            on_change=save_settings_callback,
        )
    else:
        ollama_url = st.session_state.get(
            SessionKeys.OLLAMA_URL.value, "http://localhost:11434"
        )
        if "ollama_llm_models" not in st.session_state:
            st.session_state.ollama_llm_models = get_ollama_llm_models(ollama_url)

        options = [m["value"] for m in st.session_state.ollama_llm_models]
        curr = st.session_state.get(SessionKeys.LLM_MODEL.value)
        idx = options.index(curr) if curr in options else 0
        st.selectbox(
            L.settings.select_model,
            options=options,
            index=idx,
            key=SessionKeys.LLM_MODEL.value,
            on_change=save_settings_callback,
        )

    st.slider(
        L.settings.temperature,
        0.0,
        1.0,
        step=0.1,
        key=SessionKeys.LLM_TEMPERATURE.value,
        on_change=save_settings_callback,
    )

    if st.button(L.settings.test_connection, key=f"{key_prefix}test_conn", use_container_width=True, on_click=test_connections_callback):
        pass

def render_embedding_settings(key_prefix: str = "") -> None:
    """Render embedding settings using modern components."""
    L = st.session_state.locale
    with st.container(border=True):
        from app.core.container import get_config
        config = get_config()
        use_hf = st.session_state.get(SessionKeys.USE_HUGGINGFACE.value, config.USE_HUGGINGFACE)
        st.radio(
            L.settings.provider,
            ["Ollama", "HuggingFace"],
            index=1 if use_hf else 0,
            horizontal=True,
            on_change=on_embed_type_change_callback,
            key="_temp_embed_type",
        )

        if use_hf:
            st.text_input(
                L.settings.hf_model,
                on_change=save_settings_callback,
                key=SessionKeys.HF_EMBED_MODEL.value,
            )
        else:
            st.text_input(
                L.settings.ollama_url,
                on_change=save_settings_callback,
                key=SessionKeys.OLLAMA_URL.value,
            )
            st.text_input(
                L.settings.embed_model_name,
                on_change=save_settings_callback,
                key=SessionKeys.EMBED_MODEL.value,
            )

        st.info(L.settings.model_change_warning)

def render_data_settings(key_prefix: str = "") -> None:
    """Render data & system settings using modern components."""
    L = st.session_state.locale
    with st.container(border=True):
        st.markdown(f"**{L.settings.paths_title}**")
        st.text_input(
            L.settings.data_dir,
            on_change=save_settings_callback,
            key=SessionKeys.DATA_DIR.value,
        )
        st.text_input(
            L.settings.chroma_path,
            on_change=save_settings_callback,
            key=SessionKeys.CHROMA_PATH.value,
        )

        from app.core.container import get_config
        _ = get_config()
        st.markdown(f"**{L.settings.chunking_title}**")
        c1, c2 = st.columns(2)
        c1.number_input(
            L.settings.chunk_size,
            100,
            5000,
            step=100,
            on_change=save_settings_callback,
            key=SessionKeys.CHUNK_SIZE.value,
        )
        c2.number_input(
            L.settings.chunk_overlap,
            0,
            1000,
            step=50,
            on_change=save_settings_callback,
            key=SessionKeys.CHUNK_OVERLAP.value,
        )
