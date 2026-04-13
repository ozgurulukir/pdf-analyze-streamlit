import streamlit as st

from app.core.config import AppConfig
from app.core.constants import SessionKeys
from app.ui.callbacks import (
    on_embed_type_change_callback,
    on_provider_change_callback,
    save_settings_callback,
    test_connections_callback,
)


def render_llm_settings() -> None:
    """Render LLM settings using native components."""
    L = st.session_state.locale
    config = AppConfig()
    current_type = st.session_state.get(
        SessionKeys.LAST_ENDPOINT_TYPE.value, config.DEFAULT_LLM_PROVIDER
    )
    # Map internal keys to localized labels
    provider_map = {
        "cloud": L.settings.provider_cloud,
        "ollama": L.settings.provider_ollama,
        "custom": L.settings.provider_custom
    }
    options = list(provider_map.keys())

    # Ensure current_type is a valid key
    if current_type not in options:
        current_type = "ollama"

    st.selectbox(
        L.settings.provider,
        options,
        format_func=lambda x: provider_map.get(x, x),
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

    # Checkbox for custom model input
    st.checkbox(
        L.settings.use_custom_model,
        key="use_custom_llm_flag", # Standardized internal flag
    )

    if st.session_state.get("use_custom_llm_flag", False):
        st.text_input(
            L.settings.model_name,
            key=SessionKeys.LLM_MODEL.value,
            on_change=save_settings_callback,
        )
    else:
        # Selectbox from Ollama list
        ollama_llm_models = st.session_state.get(SessionKeys.OLLAMA_LLM_MODELS.value, [])
        options = [m["value"] for m in ollama_llm_models]

        st.selectbox(
            L.settings.select_model,
            options=options,
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

    if st.button(L.settings.test_connection, key="test_llm_conn_btn", use_container_width=True, on_click=test_connections_callback):
        pass

def render_embedding_settings() -> None:
    """Render embedding settings using modern components."""
    L = st.session_state.locale
    with st.container(border=True):
        embed_options = ["ollama", "hf"]
        st.radio(
            L.settings.provider,
            embed_options,
            format_func=lambda x: "Ollama" if x == "ollama" else "HuggingFace",
            key="_temp_embed_type",
            on_change=on_embed_type_change_callback,
            horizontal=True
        )

        use_hf = st.session_state.get(SessionKeys.USE_HUGGINGFACE.value, False)
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
            # Embedding model selection
            ollama_embed_models = st.session_state.get(SessionKeys.OLLAMA_EMBED_MODELS.value, [])
            embed_options_list = [m["value"] for m in ollama_embed_models]

            st.selectbox(
                L.settings.embed_model_name,
                options=embed_options_list,
                key=SessionKeys.EMBED_MODEL.value,
                on_change=save_settings_callback,
            )

        st.info(L.settings.model_change_warning)

def render_data_settings() -> None:
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

        st.markdown(f"**{L.settings.chunking_title}**")
        c1, c2 = st.columns(2)
        c1.number_input(
            L.settings.chunk_size,
            min_value=100,
            max_value=5000,
            step=100,
            on_change=save_settings_callback,
            key=SessionKeys.CHUNK_SIZE.value,
        )
        c2.number_input(
            L.settings.chunk_overlap,
            min_value=0,
            max_value=1000,
            step=50,
            on_change=save_settings_callback,
            key=SessionKeys.CHUNK_OVERLAP.value,
        )
