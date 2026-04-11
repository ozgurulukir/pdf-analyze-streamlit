import streamlit as st
from streamlit_extras.stylable_container import stylable_container

from app.core import QUICK_PROMPTS, DatabaseManager, Message
from app.core.chroma import ChromaManager, EmbeddingManager
from app.core.config import AppConfig
from app.core.constants import SessionKeys
from app.core.services.chat_service import ChatService


@st.dialog("Sohbeti Temizle")
def confirm_clear_chat():
    """Dialog to confirm chat deletion."""
    st.write("Tüm sohbet geçmişiniz silinecek. Bu işlem geri alınamaz.")
    if st.button("Evet, Geçmişi Temizle", type="primary", use_container_width=True):
        st.session_state[SessionKeys.CHAT_HISTORY.value] = []
        st.success("Sohbet geçmişi temizlendi.")
        st.rerun()


def render_empty_chat():
    """Render premium empty chat state with animated hint."""
    st.markdown(
        """
    <div class="empty-state-container" style="text-align:center; padding: 3rem 1rem;">
        <div style="
            width: 72px; height: 72px;
            background: linear-gradient(135deg, rgba(99,102,241,0.15), rgba(124,58,237,0.15));
            border: 1px solid rgba(99, 102, 241, 0.3);
            border-radius: 20px;
            display: flex; align-items: center; justify-content: center;
            font-size: 2rem;
            margin: 0 auto 1.5rem;
            box-shadow: 0 8px 30px rgba(99,102,241,0.15);
        ">💬</div>
        <h3 style="
            color: #c7d2fe;
            font-weight: 700;
            font-size: 1.3rem;
            letter-spacing: -0.02em;
            margin-bottom: 0.5rem;
        ">Belge Analiz Uzmanı hazır</h3>
        <p style="color: #475569; font-size: 0.9rem; max-width: 360px; margin: 0 auto 1.5rem;">
            Soldaki panelden bir çalışma alanı seçin veya oluşturun, belgelerinizi yükleyin ve analiz etmeye başlayın.
        </p>
        <div style="display:flex; gap:10px; justify-content:center; flex-wrap:wrap;">
            <span style="
                font-size: 0.75rem; color: #6366f1;
                background: rgba(99,102,241,0.08); border: 1px solid rgba(99,102,241,0.2);
                border-radius: 20px; padding: 4px 12px;
            ">📄 PDF / TXT / DOCX</span>
            <span style="
                font-size: 0.75rem; color: #8b5cf6;
                background: rgba(139,92,246,0.08); border: 1px solid rgba(139,92,246,0.2);
                border-radius: 20px; padding: 4px 12px;
            ">🤖 AI Destekli Sorgulama</span>
            <span style="
                font-size: 0.75rem; color: #06b6d4;
                background: rgba(6,182,212,0.08); border: 1px solid rgba(6,182,212,0.2);
                border-radius: 20px; padding: 4px 12px;
            ">📊 Kaynak Gösterimi</span>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )


def render_chat_page(settings):
    """Render the chat interface with modern components."""
    # Premium Page Header with built-in actions
    col_title, col_actions = st.columns([4, 1])

    with col_title:
        st.markdown(
            f"""
        <div style="
            display: flex; align-items: center; gap: 14px;
            padding: 0.5rem 0;
        ">
            <div style="
                width: 44px; height: 44px;
                background: linear-gradient(135deg, #6366f1, #7c3aed);
                border-radius: 12px;
                display: flex; align-items: center; justify-content: center;
                font-size: 1.4rem;
                flex-shrink: 0;
                box-shadow: 0 4px 12px rgba(99,102,241,0.3);
            ">🤖</div>
            <div>
                <div style="font-size: 1.05rem; font-weight: 700; color: #e0e7ff; letter-spacing: -0.02em;">Belge Analiz Uzmanı</div>
                <div style="font-size: 0.78rem; color: #64748b; margin-top: 1px;">
                    Model: <span style="color:#a5b4fc">{settings.get("model", "N/A")}</span>
                </div>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col_actions:
        st.write("")  # Alignment
        if st.button("🧹 Temizle", key="clear_chat_inline", use_container_width=True):
            confirm_clear_chat()

    st.divider()

    # Chat Messages Container
    if not st.session_state.chat_history:
        render_empty_chat()
    else:
        for msg in st.session_state.chat_history:
            avatar = "🤖" if msg.role == "assistant" else "👤"
            with st.chat_message(msg.role, avatar=avatar):
                st.markdown(msg.content)
                if hasattr(msg, "sources") and msg.sources:
                    with st.expander("📌 Kaynaklar"):
                        for s in msg.sources:
                            st.caption(s)

    # Bottom spacing for fixed input
    st.markdown("<div style='height: 120px;'></div>", unsafe_allow_html=True)

    # Quick Prompts with Fragment isolation
    if st.session_state.get(SessionKeys.ACTIVE_WORKSPACE_ID.value):

        @st.fragment
        def render_quick_prompts_fragment():
            with stylable_container(
                key="quick_prompts",
                css_styles="div[data-testid='column'] { border-radius: 8px; overflow: hidden; }",
            ):
                cols = st.columns(len(QUICK_PROMPTS))
                for idx, p in enumerate(QUICK_PROMPTS):
                    with cols[idx]:
                        if st.button(p, key=f"q_{idx}", use_container_width=True):
                            st.session_state[SessionKeys.LAST_PROMPT.value] = p
                            st.rerun()

        render_quick_prompts_fragment()

    prompt = st.chat_input("Belgelerinize bir soru sorun...")

    # Handle both direct input and quick prompt buttons
    final_prompt = prompt or st.session_state.get(SessionKeys.LAST_PROMPT.value)
    if SessionKeys.LAST_PROMPT.value in st.session_state:
        del st.session_state[SessionKeys.LAST_PROMPT.value]

    if final_prompt:
        # 1. Add user message
        user_msg = Message(role="user", content=final_prompt)
        st.session_state.chat_history.append(user_msg)

        st.session_state[SessionKeys.STREAMING_PROMPT.value] = final_prompt
        st.rerun()

    # Streaming Handler
    if SessionKeys.STREAMING_PROMPT.value in st.session_state:
        streaming_prompt = st.session_state.pop(SessionKeys.STREAMING_PROMPT.value)

        db = DatabaseManager()
        config = AppConfig()
        workspace_id = st.session_state.get(SessionKeys.ACTIVE_WORKSPACE_ID.value)

        if not workspace_id:
            st.warning("⚠️ Lütfen önce bir çalışma alanı seçin veya oluşturun.")
        else:
            try:
                workspace = db.workspaces.get_by_id(workspace_id)
            except Exception:
                workspace = None

            if not workspace:
                st.error("❌ Çalışma alanı bulunamadı.")
            else:
                # Initialize RAG dependencies
                chroma = ChromaManager(
                    persist_directory=st.session_state.get(
                        SessionKeys.CHROMA_PATH.value, config.CHROMA_PERSIST_DIR
                    )
                )
                embedding = EmbeddingManager(
                    use_huggingface=st.session_state.get(
                        SessionKeys.USE_HUGGINGFACE.value, False
                    ),
                    ollama_model=st.session_state.get(
                        SessionKeys.EMBED_MODEL.value, "nomic-embed-text"
                    ),
                    ollama_url=st.session_state.get(
                        SessionKeys.OLLAMA_URL.value, "http://localhost:11434"
                    ),
                    hf_model=st.session_state.get(
                        SessionKeys.HF_EMBED_MODEL.value,
                        "sentence-transformers/all-MiniLM-L6-v2",
                    ),
                )

                chat_service = ChatService(db, chroma, embedding)

                with st.chat_message("assistant", avatar="🤖"):
                    # Use st.status for multi-step RAG flow
                    with st.status("🔍 İşlem başlatılıyor...", expanded=True) as status:
                        message_placeholder = st.empty()
                        full_response = ""
                        sources = []

                        try:
                            for event in chat_service.stream_response(
                                question=streaming_prompt,
                                workspace=workspace,
                                llm_config=settings,
                            ):
                                event_type = event.get("type")
                                content = event.get("content")

                                if event_type == "status":
                                    status.update(label=f"➡️ {content}")
                                elif event_type == "token":
                                    if not full_response:
                                        status.update(
                                            label="✍️ Cevap oluşturuluyor...",
                                            expanded=False,
                                        )
                                    full_response += content
                                    message_placeholder.markdown(full_response + "▌")
                                elif event_type == "sources":
                                    sources = content
                                elif event_type == "error":
                                    status.update(label="❌ Hata oluştu", state="error")
                                    st.error(f"RAG Hatası: {content}")
                                    break

                            status.update(label="✅ Tamamlandı", state="complete")
                            message_placeholder.markdown(full_response)

                            # Save assistant message
                            assistant_msg = Message(
                                role="assistant", content=full_response, sources=sources
                            )
                            st.session_state.chat_history.append(assistant_msg)

                            # Save to DB
                            msg_db_user = Message(
                                role="user",
                                content=streaming_prompt,
                                workspace_id=workspace.id,
                            )
                            db.messages.create(msg_db_user)
                            msg_db_assistant = Message(
                                role="assistant",
                                content=full_response,
                                sources=sources,
                                workspace_id=workspace.id,
                            )
                            db.messages.create(msg_db_assistant)

                        except Exception as e:
                            status.update(label="❌ Kritik hata", state="error")
                            st.error(f"Hata: {str(e)}")
                            with st.expander("Hata Detayı"):
                                import traceback

                                st.code(traceback.format_exc())

                st.rerun()
