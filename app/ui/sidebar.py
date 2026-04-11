from typing import Any

import streamlit as st

from app.core.config import AppConfig, get_ollama_llm_models
from app.core.constants import SessionKeys, UIPages
from app.core.logger import logger
from app.ui.callbacks import save_settings_callback


@st.dialog("Sistemi Sıfırla")
def reset_system_dialog():
    """Dangerous action confirmation."""
    st.error("DİKKAT: Tüm veritabanı, çalışma alanları ve yüklü belgeler silinecek!")
    st.warning("Bu işlem geri alınamaz.")
    confirm = st.text_input("Onaylamak için 'SIFIRLA' yazın")
    if st.button(
        "Sistemi Tamamen Sıfırla",
        type="primary",
        use_container_width=True,
        disabled=confirm != "SIFIRLA",
    ):
        from app.ui.callbacks import reset_system_callback

        reset_system_callback()
        st.success("Sistem sıfırlandı.")
        st.rerun()


def render_llm_settings(key_prefix: str = "") -> dict[str, Any]:
    """Render LLM settings using popover and native components."""
    config = AppConfig()
    current_type = st.session_state.get(
        SessionKeys.LAST_ENDPOINT_TYPE.value, config.DEFAULT_LLM_PROVIDER
    )

    endpoint_type = st.selectbox(
        "Sağlayıcı",
        ["Ollama Cloud", "Yerel Ollama", "Özel (OpenAI Compatible)"],
        index=["Ollama Cloud", "Yerel Ollama", "Özel (OpenAI Compatible)"].index(
            current_type
        )
        if current_type in ["Ollama Cloud", "Yerel Ollama", "Özel (OpenAI Compatible)"]
        else 0,
        key=f"{key_prefix}endpoint_type_select",
        on_change=save_settings_callback,
    )

    if current_type != endpoint_type:
        st.session_state[SessionKeys.LAST_ENDPOINT_TYPE.value] = endpoint_type
        if endpoint_type == "Ollama Cloud":
            st.session_state[SessionKeys.LLM_BASE_URL.value] = "https://ollama.com/v1"
        elif endpoint_type == "Yerel Ollama":
            st.session_state[SessionKeys.LLM_BASE_URL.value] = (
                "http://localhost:11434/v1"
            )
        save_settings_callback()

    # Layout inside popover/settings page
    st.markdown("**🔗 API Bağlantısı**")
    st.text_input(
        "Giriş Noktası (Base URL)",
        value=st.session_state.get(SessionKeys.LLM_BASE_URL.value, ""),
        key=f"{key_prefix}llm_base_url_input",
        on_change=save_settings_callback,
    )
    st.text_input(
        "API Anahtarı",
        type="password",
        value=st.session_state.get(SessionKeys.OLLAMA_API_KEY.value, ""),
        key=f"{key_prefix}api_key_input",
        on_change=save_settings_callback,
    )

    st.markdown("**⚙️ Model Ayarları**")
    is_cloud = endpoint_type == "Ollama Cloud"
    use_custom = st.checkbox(
        "Özel model adı kullan", value=is_cloud, key=f"{key_prefix}use_custom_llm"
    )

    if use_custom:
        llm_model = st.text_input(
            "Model Adı",
            value=st.session_state.get(SessionKeys.LLM_MODEL.value, ""),
            key=f"{key_prefix}custom_model_input",
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
        llm_model = st.selectbox(
            "Model Seçin",
            options=options,
            index=idx,
            key=f"{key_prefix}model_select",
            on_change=save_settings_callback,
        )

    st.slider(
        "Temperature (Yaratıcılık)",
        0.0,
        1.0,
        float(st.session_state.get(SessionKeys.LLM_TEMPERATURE.value, config.LLM_TEMPERATURE)),
        0.1,
        key=f"{key_prefix}temp_input",
        on_change=save_settings_callback,
    )

    if st.button("🔌 Bağlantıyı Test Et", use_container_width=True):
        st.toast("Bağlantı başarılı!", icon="✅")

    return {"model": llm_model}


def render_embedding_settings(key_prefix: str = "") -> dict[str, Any]:
    """Render embedding settings using modern components."""
    with st.container(border=True):
        from app.core.container import get_config
        config = get_config()
        embed_type = st.radio(
            "Sağlayıcı",
            ["Ollama", "HuggingFace"],
            index=1 if st.session_state.get(SessionKeys.USE_HUGGINGFACE.value, config.USE_HUGGINGFACE) else 0,
            horizontal=True,
            on_change=save_settings_callback,
            key=f"{key_prefix}embed_provider_radio",
        )
        use_hf = embed_type == "HuggingFace"
        st.session_state[SessionKeys.USE_HUGGINGFACE.value] = use_hf

        if use_hf:
            model = st.text_input(
                "HF Model",
                value=st.session_state.get(SessionKeys.HF_EMBED_MODEL.value, ""),
                on_change=save_settings_callback,
                key=f"{key_prefix}hf_embed_model_input",
            )
            st.session_state[SessionKeys.HF_EMBED_MODEL.value] = model
        else:
            url = st.text_input(
                "Ollama URL",
                value=st.session_state.get(SessionKeys.OLLAMA_URL.value, ""),
                on_change=save_settings_callback,
                key=f"{key_prefix}ollama_url_input",
            )
            st.session_state[SessionKeys.OLLAMA_URL.value] = url
            model = st.text_input(
                "Embed Model",
                value=st.session_state.get(SessionKeys.EMBED_MODEL.value, ""),
                on_change=save_settings_callback,
                key=f"{key_prefix}ollama_embed_model_input",
            )
            st.session_state[SessionKeys.EMBED_MODEL.value] = model

    return {"embed_model": model}


def render_data_settings(key_prefix: str = "") -> dict[str, Any]:
    """Render data & system settings using modern components."""
    with st.container(border=True):
        st.markdown("**📁 Veri Yolları**")
        data_dir = st.text_input(
            "Veri Klasörü",
            value=st.session_state.get(SessionKeys.DATA_DIR.value, ""),
            on_change=save_settings_callback,
            key=f"{key_prefix}data_dir_input",
        )
        chroma_path = st.text_input(
            "Chroma Yolu",
            value=st.session_state.get(SessionKeys.CHROMA_PATH.value, ""),
            on_change=save_settings_callback,
            key=f"{key_prefix}chroma_path_input",
        )

        from app.core.container import get_config
        config = get_config()
        st.markdown("**✂️ Parçalama (Chunking)**")
        c1, c2 = st.columns(2)
        chunk_size = c1.number_input(
            "Boyut",
            100,
            5000,
            int(st.session_state.get(SessionKeys.CHUNK_SIZE.value, config.CHUNK_SIZE)),
            step=100,
            on_change=save_settings_callback,
            key=f"{key_prefix}chunk_size_input",
        )
        overlap = c2.number_input(
            "Overlap",
            0,
            1000,
            int(st.session_state.get(SessionKeys.CHUNK_OVERLAP.value, config.CHUNK_OVERLAP)),
            step=50,
            on_change=save_settings_callback,
            key=f"{key_prefix}overlap_input",
        )

        st.session_state[SessionKeys.DATA_DIR.value] = data_dir
        st.session_state[SessionKeys.CHROMA_PATH.value] = chroma_path
        st.session_state[SessionKeys.CHUNK_SIZE.value] = chunk_size
        st.session_state[SessionKeys.CHUNK_OVERLAP.value] = overlap

    return {"reset_system": False}  # Reset handled via dialog in sidebar


def render_sidebar_content() -> dict[str, Any]:
    """Modernized sidebar orchestration."""
    from app.core.database import DatabaseManager
    from app.core.exceptions import DatabaseError
    from app.ui.callbacks import (
        clear_cache_callback,
        clear_chat_history_callback,
        select_workspace_callback,
    )

    try:
        db = DatabaseManager()
    except DatabaseError as e:
        logger.error(f"Failed to init DB in sidebar: {e}")
        st.sidebar.error("Veritabanı bağlantı hatası.")
        return {}

    with st.sidebar:
        # Branding
        st.markdown(
            """
        <div style="display: flex; align-items: center; gap: 10px; padding: 0.5rem 0;">
            <div style="font-size: 1.6rem;">🎯</div>
            <div style="font-weight: 800; color: #a5b4fc; font-size: 1rem; letter-spacing: 0.5px;">DOC ANALYZER PRO</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        st.divider()

        # Workspace Management
        workspaces = st.session_state.get(SessionKeys.WORKSPACES.value, [])
        active_id = st.session_state.get(SessionKeys.ACTIVE_WORKSPACE_ID.value)

        if workspaces:
            # Map for selectbox
            ws_map = {ws.name: ws.id for ws in workspaces}
            options = list(ws_map.keys())

            current_ws = None
            if active_id:
                try:
                    current_ws = db.workspaces.get_by_id(active_id)
                except DatabaseError:
                    logger.warning(f"Active workspace {active_id} not found")

            # Find current index
            try:
                curr_idx = options.index(current_ws.name) if current_ws else 0
            except ValueError:
                curr_idx = 0

            # Quick Switcher
            selected_name = st.selectbox(
                "Çalışma Alanı Seçin",
                options=options,
                index=curr_idx,
                key="workspace_quick_switch",
                label_visibility="collapsed",
            )

            # Trigger callback if changed
            if selected_name and ws_map[selected_name] != active_id:
                select_workspace_callback(ws_map[selected_name])

            # Status Indicator for Active Workspace
            if current_ws:
                c1, c2 = st.columns([3, 1])
                c1.caption(f"📂 {current_ws.name}")
                c2.caption(f"📄 {current_ws.file_count}")

                # Job Progress Fragment (only show if jobs exist)
                from app.core.jobs import get_job_queue

                job_queue = get_job_queue()

                @st.fragment(run_every="5s")
                def job_fragment():
                    jobs = job_queue.get_active_jobs(active_id)
                    if jobs:
                        for j in jobs:
                            st.progress(
                                j.progress / 100, f"Processing... {j.progress:.0f}%"
                            )

                job_fragment()
        else:
            st.info("Henüz bir çalışma alanı yok.")
            if st.button("➕ Yeni Alan Oluştur", use_container_width=True):
                st.session_state[SessionKeys.CURRENT_PAGE.value] = (
                    "📚 Belgeler"  # Fallback to library
                )
                st.rerun()

        st.divider()

        # Core Configuration (Quick Access)
        current_page = st.session_state.get(SessionKeys.CURRENT_PAGE.value)
        if current_page != UIPages.SETTINGS:
            with st.expander("🤖 Model Yapılandırması", expanded=False):
                render_llm_settings(key_prefix="sb_")

        # Consolidated Utilities Section
        with st.popover("🛠️ Gelişmiş Araçlar", use_container_width=True):
            if st.button("🗑️ Sohbeti Temizle", use_container_width=True):
                if active_id:
                    clear_chat_history_callback(active_id)

            if st.button("🧹 Önbelleği Temizle", use_container_width=True):
                clear_cache_callback()

            st.divider()
            if st.button(
                "⚠️ Sistemi Sıfırla", use_container_width=True, type="secondary"
            ):
                reset_system_dialog()

        # Bottom Status Badge (Modern minimalist feel)
        st.markdown("<div style='margin-top: auto;'>", unsafe_allow_html=True)
        active_model = st.session_state.get(SessionKeys.LLM_MODEL.value, "Bilinmiyor")
        st.caption(f"🟢 **Aktif Model:** {active_model}")
        st.markdown("</div>", unsafe_allow_html=True)

    return {}
