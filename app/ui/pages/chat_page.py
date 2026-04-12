import streamlit as st

from app.core import Message
from app.core.chroma import ChromaManager, EmbeddingManager
from app.core.constants import SessionKeys
from app.core.logger import get_logger
from app.core.services.chat_service import ChatService

logger = get_logger(__name__)

def render_source_cards(sources: list, key_suffix: str = ""):
    """Render retrieval sources using native st.pills component (Streamlit 1.40+)."""
    if not sources:
        return

    # Process sources to get clean labels
    src_labels = []
    for s in sources:
        src_path = s.get("file", "Bilinmeyen") if isinstance(s, dict) else str(s)
        name = src_path.split("/")[-1].split("\\")[-1]
        src_labels.append(f"📄 {name}")

    L = st.session_state.locale
    if src_labels:
        st.caption(L.chat.sources_title)
        # Provide a unique key to prevent ID collisions
        st.pills(L.library.status, src_labels, label_visibility="collapsed",
                 selection_mode="single", disabled=False, key=f"pills_{key_suffix}")


def render_empty_chat():
    """Render modern empty chat state using pure native components."""
    L = st.session_state.locale
    with st.container():
        # Large vertical spacing using empty rows or containers
        st.write("")
        st.write("")
        st.write("")

        _, col, _ = st.columns([1, 2, 1])
        with col:
            st.markdown("<h1 style='text-align: center; font-size: 4rem;'>💬</h1>", unsafe_allow_html=True) # Icon is fine as markdown
            st.markdown(f"<h2 style='text-align: center;'>{L.chat.empty_title}</h2>", unsafe_allow_html=True)
            st.markdown(f"<p style='text-align: center; color: gray;'>{L.chat.empty_subtitle}</p>", unsafe_allow_html=True)

        st.write("")
        st.write("")


def render_chat_page(settings):
    """Render the focused canvas chat interface."""
    from app.core import DatabaseManager
    workspace_id = st.session_state.get(SessionKeys.ACTIVE_WORKSPACE_ID.value)
    session_id = st.session_state.get(SessionKeys.ACTIVE_SESSION_ID.value)
    L = st.session_state.locale

    # Sync History from DB if session changed or not yet loaded
    if "last_synced_session" not in st.session_state or st.session_state.get("last_synced_session") != session_id:
        if workspace_id:
            db = DatabaseManager()
            st.session_state.chat_history = db.messages.get_recent(workspace_id, session_id=session_id)
            st.session_state.last_synced_session = session_id

    # Chat Messages Container
    if not st.session_state.chat_history:
        render_empty_chat()
    else:
        i = 0
        db = DatabaseManager()
        history = st.session_state.chat_history
        while i < len(history):
            msg = history[i]
            next_msg = history[i+1] if i+1 < len(history) else None

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
                            st.session_state.chat_history.pop(i)
                            st.session_state.chat_history.pop(i) # pop 'i' again as it shifted
                        else:
                            st.session_state.chat_history.pop(i)
                        st.rerun()

                with col_content:
                    # Render Question
                    st.markdown(f"**👤 {msg.content}**")

                # Render Answer
                if next_msg and next_msg.role == "assistant":
                    st.divider()
                    st.markdown(next_msg.content)

                    if hasattr(next_msg, "sources") and next_msg.sources:
                        render_source_cards(next_msg.sources, key_suffix=f"hist_{i}")

                    # Bilgi Bankasına Ekle Butonu
                    btn_col1, btn_col2 = st.columns([1, 4])
                    if btn_col1.button(L.chat.add_to_kb, key=f"add_kb_{i}", help=L.chat.add_to_kb):
                        question = msg.content
                        with st.spinner(L.chat.kb_searching_tags):
                            from app.core.container import (
                                get_chroma,
                                get_database,
                                get_embedding_manager,
                                get_rag_chain,
                            )
                            rag_db = get_database()
                            rag = get_rag_chain(
                                db=rag_db,
                                chroma=get_chroma(),
                                embedding=get_embedding_manager(),
                                llm_config=settings,
                                workspace_id=workspace_id,
                                session_id=session_id
                            )
                            tags = rag.generate_tags(question, next_msg.content)

                            rag_db.qa.create_from_params(
                                workspace_id=workspace_id,
                                file_ids=[s.get("id") for s in (next_msg.sources or []) if isinstance(s, dict) and s.get("id")],
                                question=question,
                                answer=next_msg.content,
                                tags=tags
                            )
                            st.toast(f"{L.chat.kb_added_toast} Etiketler: {', '.join(tags)}", icon="✅")
                    i += 2
                else:
                    i += 1

    # Bottom spacing for fixed input
    st.markdown("<div style='height: 150px;'></div>", unsafe_allow_html=True)

    prompt = st.chat_input(L.chat.input_placeholder)

    # Handle Input
    final_prompt = prompt or st.session_state.get(SessionKeys.LAST_PROMPT.value)
    if SessionKeys.LAST_PROMPT.value in st.session_state:
        del st.session_state[SessionKeys.LAST_PROMPT.value]

    if final_prompt:
        user_msg = Message(role="user", content=final_prompt, session_id=session_id, workspace_id=workspace_id)
        st.session_state.chat_history.append(user_msg)
        st.session_state[SessionKeys.STREAMING_PROMPT.value] = final_prompt
        st.rerun()

    # Streaming Handler
    if SessionKeys.STREAMING_PROMPT.value in st.session_state:
        streaming_prompt = st.session_state.pop(SessionKeys.STREAMING_PROMPT.value)
        from app.core.container import get_config, get_database
        db = get_database()
        config = get_config()
        workspace_id = st.session_state.get(SessionKeys.ACTIVE_WORKSPACE_ID.value)

        if not workspace_id:
            st.warning("⚠️ Lütfen üst menüden bir çalışma alanı seçin.")
        else:
            try:
                from app.ui.callbacks import add_alert
                workspace = db.workspaces.get_by_id(workspace_id)
                if not workspace:
                    add_alert("❌ Çalışma alanı bulunamadı.", "error")
                    st.rerun()

                chroma = ChromaManager(persist_directory=st.session_state.get(SessionKeys.CHROMA_PATH.value, config.CHROMA_PERSIST_DIR))
                embedding = EmbeddingManager(
                    use_huggingface=st.session_state.get(SessionKeys.USE_HUGGINGFACE.value, False),
                    ollama_model=st.session_state.get(SessionKeys.EMBED_MODEL.value, "nomic-embed-text"),
                    ollama_url=st.session_state.get(SessionKeys.OLLAMA_URL.value, "http://localhost:11434"),
                    hf_model=st.session_state.get(SessionKeys.HF_EMBED_MODEL.value, "sentence-transformers/all-MiniLM-L6-v2"),
                )
                chat_service = ChatService(db, chroma, embedding)

                with st.container(border=True):
                    st.markdown(f"**👤 {streaming_prompt}**")
                    st.divider()

                    with st.status("🔍 İşleniyor...", expanded=True) as status:
                        pass
                    
                    response_placeholder = st.empty()
                    full_response = ""
                    sources: list[str] = []

                    for event in chat_service.stream_response(question=streaming_prompt, workspace=workspace, llm_config=settings, session_id=session_id):
                        etype = event.get("type")
                        content = event.get("content")

                        if etype == "status":
                            status.update(label=f"➡️ {content}")
                        elif etype == "token" and content:
                            full_response += str(content)
                            response_placeholder.markdown(full_response + "▌")
                            if status._container:
                                status.update(label="✅ Kaynaklar Tarandı", state="complete", expanded=False)
                        elif etype == "sources":
                            sources = content if isinstance(content, list) else []
                        elif etype == "error":
                            status.update(label="❌ Hata", state="error")
                            st.toast(str(content), icon="❌")

                    response_placeholder.markdown(full_response)
                    if sources:
                        render_source_cards(sources, key_suffix="current_stream")

                    # Persist (OUTSIDE IF SOURCES)
                    db_sources = [{"file": s} for s in sources]
                    assistant_msg = Message(role="assistant", content=full_response, sources=db_sources, session_id=session_id, workspace_id=workspace_id)
                    st.session_state.chat_history.append(assistant_msg)

                    from app.core import Message as DBMessage
                    db.messages.create(DBMessage(role="user", content=streaming_prompt, workspace_id=workspace_id, session_id=session_id))
                    db.messages.create(DBMessage(role="assistant", content=full_response, sources=db_sources, workspace_id=workspace_id, session_id=session_id))

                    # Update session's last_message_at
                    if session_id:
                        sess = db.chat_sessions.get_by_id(session_id)
                        if sess:
                            from datetime import datetime
                            sess.last_message_at = datetime.now()
                            db.chat_sessions.update(sess)

                st.rerun()
            except Exception as e:
                from app.ui.callbacks import add_alert
                logger.error(f"Chat execution failed: {e}")
                add_alert(f"Sohbet başlatılamadı: {str(e)}", "error")
                st.rerun()
