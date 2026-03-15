"""Q&A Dashboard component."""
import streamlit as st
from typing import List

from app.core.models import QAPair, UserPreferences


def render_qa_dashboard(
    qa_pairs: List[QAPair],
    preferences: UserPreferences,
    on_like: callable,
    on_dislike: callable,
    on_select_qa: callable = None
):
    """Render Q&A dashboard with cards."""
    
    st.markdown("## 📊 Soru-Cevap Geçmişi")
    
    # Stats summary
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Toplam Soru", len(qa_pairs))
    
    with col2:
        total_likes = sum(qa.likes for qa in qa_pairs)
        st.metric("👍 Beğeni", total_likes)
    
    with col3:
        total_dislikes = sum(qa.dislikes for qa in qa_pairs)
        st.metric("👎 Beğenmedi", total_dislikes)
    
    with col4:
        net_score = total_likes - total_dislikes
        st.metric("📈 Net Puan", net_score)
    
    st.divider()
    
    # Preference weights display
    st.markdown("### 🎯 Tercih Ağırlıkları")
    
    cols = st.columns(4)
    for idx, (tag, weight) in enumerate(preferences.weights.items()):
        with cols[idx]:
            st.progress(weight, text=f"{tag}: {weight:.1f}")
    
    st.divider()
    
    # Q&A Cards
    st.markdown("### 💬 Soru-Cevap Çiftleri")
    
    if not qa_pairs:
        st.info("Henüz soru-cevap çifti yok.")
        return
    
    for qa in qa_pairs:
        render_qa_card(qa, on_like, on_dislike, on_select_qa)


def render_qa_card(
    qa: QAPair,
    on_like: callable,
    on_dislike: callable,
    on_select_qa: callable = None
):
    """Render a single Q&A card."""
    
    with st.container():
        # Question
        st.markdown(f"**❓ Soru:** {qa.question}")
        
        # Answer (collapsible)
        with st.expander("💡 Cevabı Gör"):
            st.markdown(qa.answer)
            
            # Metadata
            st.caption(f"Oluşturulma: {qa.created_at.strftime('%d/%m/%Y %H:%M')}")
            st.caption(f"Kaynak dosya sayısı: {len(qa.file_ids)}")
        
        # Actions
        col1, col2, col3 = st.columns([1, 1, 4])
        
        with col1:
            if st.button(f"👍 {qa.likes}", key=f"like_{qa.id}"):
                on_like(qa.id)
        
        with col2:
            if st.button(f"👎 {qa.dislikes}", key=f"dislike_{qa.id}"):
                on_dislike(qa.id)
        
        with col3:
            if on_select_qa and st.button("📋 Kullan", key=f"use_{qa.id}"):
                on_select_qa(qa.question)
    
    st.divider()


def render_preference_adjuster(
    preferences: UserPreferences,
    on_adjust: callable
):
    """Render preference adjustment panel."""
    
    st.markdown("### ⚖️ Tercihlerinizi Ayarlayın")
    st.caption("Cevap tarzınızı özelleştirin")
    
    tags = list(preferences.weights.keys())
    
    for tag in tags:
        col1, col2, col3 = st.columns([2, 4, 1])
        
        with col1:
            st.write(tag.replace("_", " ").title())
        
        with col2:
            new_value = st.slider(
                f"slider_{tag}",
                min_value=0.0,
                max_value=1.0,
                value=preferences.weights[tag],
                step=0.1,
                key=f"pref_{tag}"
            )
        
        with col3:
            delta = new_value - preferences.weights[tag]
            if delta != 0:
                if st.button("Uygula", key=f"apply_{tag}"):
                    on_adjust(tag, delta)
    
    # Reset button
    if st.button("Varsayılana Sıfırla"):
        for tag in tags:
            on_adjust(tag, 0.5 - preferences.weights[tag])
        st.success("Tercihler sıfırlandı!")
