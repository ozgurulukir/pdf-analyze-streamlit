"""Chat UI components."""
import streamlit as st
from typing import List, Optional
from app.core.models import Message


def init_chat_state():
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []


def add_message(role: str, content: str, sources: List[str] = None):
    """Add message to session state."""
    message = Message(
        role=role,
        content=content,
        sources=sources or []
    )
    st.session_state.chat_history.append(message)
    return message


def render_chat_area(messages: List[Message]):
    """Render chat messages."""
    for message in messages:
        with st.chat_message(message.role, avatar="🤖" if message.role == "assistant" else "👤"):
            st.markdown(message.content)
            
            if hasattr(message, 'sources') and message.sources:
                with st.expander("📚 Kaynaklar"):
                    for source in message.sources:
                        st.caption(source)


def render_input_bar(on_send, quick_prompts=None, disabled=False):
    """Render input bar."""
    if quick_prompts:
        cols = st.columns(len(quick_prompts))
        for idx, prompt in enumerate(quick_prompts):
            with cols[idx]:
                if st.button(prompt, key=f"quick_{idx}"):
                    return prompt
    
    st.markdown("---")
    
    return st.chat_input("Sorunuzu yazın...", disabled=disabled)


def render_empty_chat():
    st.markdown("""
    <div style="text-align: center; padding: 3rem; color: #888;">
        <div style="font-size: 3rem;">💬</div>
        <h3>Sohbete Başlayın</h3>
    </div>
    """, unsafe_allow_html=True)


def render_typing_indicator():
    return st.markdown("Asistan yazıyor...", unsafe_allow_html=True)
