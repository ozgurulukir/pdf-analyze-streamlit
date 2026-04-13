from datetime import datetime
from typing import cast

import streamlit as st

from app.core import Message
from app.core.chroma import ChromaManager, EmbeddingManager
from app.core.constants import SessionKeys
from app.core.container import (
    get_chroma,
    get_config,
    get_database,
    get_embedding_manager,
    get_rag_chain,
)
from app.core.locales import LocaleStrings
from app.core.logger import get_logger
from app.core.services.chat_service import ChatService
from app.ui.callbacks import add_alert
from app.ui.state import state

logger = get_logger(__name__)

def render_source_cards(sources: list[object], key_suffix: str = "") -> None:
    """Render retrieval sources using native st.pills component (Streamlit 1.40+)."""
    if not sources:
        return

    # Process sources to get clean labels
    src_labels: list[str] = []
    L: LocaleStrings = state.locale
    for s in sources:
        src_path = cast(dict[str, object], s).get("file", L.library.unknown) if isinstance(s, dict) else str(s)
        name = str(src_path).split("/")[-1].split("\\")[-1]
        src_labels.append(f"📄 {name}")

    if src_labels:
        _ = st.caption(L.chat.sources_title)
        # Provide a unique key to prevent ID collisions
        _ = st.pills(L.library.status, src_labels, label_visibility="collapsed",
                 selection_mode="single", disabled=False, key=f"pills_{key_suffix}")


def render_empty_chat() -> None:
    """Render modern empty chat state using pure native components."""
    L: LocaleStrings = state.locale
    with st.container():
        st.write("")
        st.write("")
        st.write("")

        _, col, _ = st.columns([1, 2, 1])
        with col:
            st.markdown("<h1 style='text-align: center; font-size: 4rem;'>💬</h1>", unsafe_allow_html=True)
            st.markdown(f"<h2 style='text-align: center;'>{L.chat.empty_title}</h2>", unsafe_allow_html=True)
            st.markdown(f"<p style='text-align: center; color: gray;'>{L.chat.empty_subtitle}</p>", unsafe_allow_html=True)

        st.write("")
        st.write("")


def render_chat_page() -> None:
    """Render the focused canvas chat interface using SSOT."""
    workspace_id = state.active_workspace_id
    session_id = state.active_session_id
    L: LocaleStrings = state.locale

    # Sync History from DB if session changed or not yet loaded
    last_synced = state.get("last_synced_session")
    if last_synced != session_id:
        if workspace_id:
            db = get_database()
            state.set("chat_history", db.messages.get_recent(workspace_id, session_id=session_id))
            state.set("last_synced_session", session_id)

    @st.fragment
    def render_interactive_chat() -> None:
        # Chat Messages Container
        chat_history = cast(list[Message], state.get("chat_history", []))
        if not chat_history:
            render_empty_chat()
        else:
            i = 0
            db = get_database()
            while i < len(chat_history):
                msg = chat_history[i]
                next_msg = chat_history[i+1] if i+1 < len(chat_history) else None

                with st.container(border=True):
                    # Header row with Delete button
                    col_content, col_actions = st.columns([0.9, 0.1])

                    with col_actions:
                        if st.button("🗑️", key=f"del_msg_{i}", help=L.common.delete):
                            # Delete from DB
                            if hasattr(msg, "id") and msg.id:
                                db.messages.delete(msg.id)
                            if next_msg and hasattr(next_msg, "id") and next_msg.id:
                                db.messages.delete(next_msg.id)

                            # Remove from session state
                            if next_msg and next_msg.role == "assistant":
                                chat_history.pop(i)
                                chat_history.pop(i)
                            else:
                                chat_history.pop(i)
                            state.set("chat_history", chat_history)
                            st.rerun(scope="fragment")

                    with col_content:
                        st.markdown(f"**👤 {msg.content}**")

                    # Render Answer
                    if next_msg and next_msg.role == "assistant":
                        st.divider()
                        st.markdown(next_msg.content)

                        if hasattr(next_msg, "sources") and next_msg.sources:
                            render_source_cards(cast(list[object], next_msg.sources), key_suffix=f"hist_{i}")

                        # Bilgi Bankasına Ekle Butonu
                        btn_col1, _ = st.columns([1, 4])
                        if btn_col1.button(L.chat.add_to_kb, key=f"add_kb_{i}"):
                            question = msg.content
                            with st.spinner(L.chat.kb_searching_tags):
                                # Pull LLM settings directly from Session State (SSOT)
                                llm_config = {
                                    "model": state.get(SessionKeys.LLM_MODEL.value),
                                    "base_url": state.get(SessionKeys.LLM_BASE_URL.value),
                                    "api_key": state.get(SessionKeys.OLLAMA_API_KEY.value),
                                    "temperature": state.get(SessionKeys.LLM_TEMPERATURE.value),
                                    "endpoint_type": state.get(SessionKeys.LAST_ENDPOINT_TYPE.value),
                                }
                                rag_db = get_database()
                                rag = get_rag_chain(
                                    db=rag_db,
                                    chroma=get_chroma(),
                                    embedding=get_embedding_manager(),
                                    llm_config=llm_config,
                                    workspace_id=workspace_id,
                                    session_id=session_id
                                )
                                tags = rag.generate_tags(question, next_msg.content)

                                rag_db.qa.create_from_params(
                                    workspace_id=workspace_id,
                                    file_ids=[cast(dict[str, object], s).get("id") for s in (next_msg.sources or []) if isinstance(s, dict) and s.get("id")],
                                    question=question,
                                    answer=next_msg.content,
                                    tags=tags
                                )
                                st.toast(f"{L.chat.kb_added_toast} {L.messages.tags_label.format(', '.join(tags))}", icon="✅")
                        i += 2
                    else:
                        i += 1

        # Bottom spacing for fixed input
        st.markdown("<div style='height: 150px;'></div>", unsafe_allow_html=True)
        prompt = st.chat_input(L.chat.input_placeholder)

        # Handle Interaction State
        final_prompt = prompt or state.get(SessionKeys.LAST_PROMPT.value)
        if state.get(SessionKeys.LAST_PROMPT.value):
            state.delete(SessionKeys.LAST_PROMPT.value)

        if final_prompt:
            user_msg = Message(role="user", content=final_prompt, session_id=session_id, workspace_id=workspace_id)
            chat_history.append(user_msg)
            state.set("chat_history", chat_history)
            state.set(SessionKeys.STREAMING_PROMPT.value, final_prompt)
            st.rerun(scope="fragment")

        # Streaming Handler
        if state.get(SessionKeys.STREAMING_PROMPT.value):
            streaming_prompt = state.get(SessionKeys.STREAMING_PROMPT.value)
            state.delete(SessionKeys.STREAMING_PROMPT.value)

            db = get_database()
            config = get_config()

            if not workspace_id:
                st.warning(f"⚠️ {L.workspace.no_active}")
            else:
                try:
                    workspace = db.workspaces.get_by_id(workspace_id)
                    if not workspace:
                        add_alert(f"❌ {L.workspace.not_found}", "error")
                        st.rerun(scope="fragment")

                    # Robust Service Initialization from SSOT
                    chroma_path = cast(str, state.get(SessionKeys.CHROMA_PATH.value, config.CHROMA_PERSIST_DIR))
                    chroma = ChromaManager(persist_directory=chroma_path)

                    embedding = EmbeddingManager(
                        use_huggingface=cast(bool, state.get(SessionKeys.USE_HUGGINGFACE.value, False)),
                        ollama_model=cast(str, state.get(SessionKeys.EMBED_MODEL.value, "nomic-embed-text")),
                        ollama_url=cast(str, state.get(SessionKeys.OLLAMA_URL.value, "http://localhost:11434")),
                        hf_model=cast(str, state.get(SessionKeys.HF_EMBED_MODEL.value, "sentence-transformers/all-MiniLM-L6-v2")),
                    )
                    
                    llm_config = {
                        "model": state.get(SessionKeys.LLM_MODEL.value),
                        "base_url": state.get(SessionKeys.LLM_BASE_URL.value),
                        "api_key": state.get(SessionKeys.OLLAMA_API_KEY.value),
                        "temperature": state.get(SessionKeys.LLM_TEMPERATURE.value),
                        "endpoint_type": state.get(SessionKeys.LAST_ENDPOINT_TYPE.value),
                    }
                    
                    chat_service = ChatService(db, chroma, embedding)

                    with st.container(border=True):
                        st.markdown(f"**👤 {streaming_prompt}**")
                        st.divider()

                        with st.status(f"🔍 {L.common.loading}", expanded=True) as status:
                            pass
                        response_placeholder = st.empty()
                        full_response = ""
                        sources: list[object] = []

                        for event in chat_service.stream_response(question=streaming_prompt, workspace=workspace, llm_config=llm_config, session_id=session_id):
                            etype = event.get("type")
                            content = event.get("content")

                            if etype == "status" and content:
                                status.update(label=f"➡️ {content}")
                            elif etype == "token" and content:
                                full_response += str(content)
                                response_placeholder.markdown(full_response + "▌")
                                if status and status._container:
                                    status.update(label="✅ Kaynaklar Tarandı", state="complete", expanded=False)
                            elif etype == "sources":
                                sources = cast(list[object], content if isinstance(content, list) else [])
                            elif etype == "error" and content:
                                status.update(label=L.common.error, state="error")
                                st.toast(str(content), icon="❌")

                        response_placeholder.markdown(full_response)
                        if sources:
                            render_source_cards(sources, key_suffix="current_stream")

                        # Persist to DB & State
                        db_sources = [{"file": s} for s in sources]
                        assistant_msg = Message(role="assistant", content=full_response, sources=db_sources, session_id=session_id, workspace_id=workspace_id)
                        chat_history.append(assistant_msg)
                        state.set("chat_history", chat_history)

                        db.messages.create(Message(role="user", content=streaming_prompt, workspace_id=workspace_id, session_id=session_id))
                        db.messages.create(Message(role="assistant", content=full_response, sources=db_sources, workspace_id=workspace_id, session_id=session_id))

                        if session_id:
                            sess = db.chat_sessions.get_by_id(session_id)
                            if sess:
                                sess.last_message_at = datetime.now()
                                db.chat_sessions.update(sess)

                    st.rerun(scope="fragment")
                except Exception as e:
                    logger.error(f"Chat execution failed: {e}")
                    add_alert(L.messages.chat_init_failed.format(str(e)), "error")
                    st.rerun(scope="fragment")

    render_interactive_chat()
