import streamlit as st

from app.core.constants import SessionKeys
from app.ui.callbacks import (
    clear_cache_callback,
    clear_chat_history_callback,
    create_chat_session_callback,
    create_workspace_callback,
    delete_chat_session_callback,
    delete_workspace_callback,
    get_cached_database_manager,
    rename_workspace_callback,
    select_chat_session_callback,
    select_workspace_callback,
)
from app.ui.settings_components import (
    render_data_settings,
    render_embedding_settings,
    render_llm_settings,
)


@st.dialog("Sistemi Sıfırla")
def reset_system_dialog():
    """Dangerous action confirmation."""
    L = st.session_state.locale
    st.error(L.settings.reset_system)
    st.warning(L.common.warning)
    confirm = st.text_input(L.common.confirm)
    if st.button(
        L.settings.reset_system,
        type="primary",
        key="btn_hard_reset",
        use_container_width=True,
        disabled=confirm != "SIFIRLA",
    ):
        from app.ui.callbacks import reset_system_callback
        reset_system_callback()
        st.success(L.common.success)
        st.rerun()


@st.dialog("🎯 Çalışma Alanları", width="large")
def manage_workspaces_dialog():
    """Dialog for workspace management: Switch, Create, Delete."""
    L = st.session_state.locale
    workspaces = st.session_state.get(SessionKeys.WORKSPACES.value, [])
    active_id = st.session_state.get(SessionKeys.ACTIVE_WORKSPACE_ID.value)

    st.markdown(f"### {L.workspace.current_areas}")
    if not workspaces:
        st.info(L.library.no_files)
    else:
        for ws in workspaces:
            cols = st.columns([4, 1, 1])
            is_active = ws.id == active_id

            with cols[0]:
                st.write(f"**{ws.name}**" + (f" ({L.workspace.active})" if is_active else ""))
                # Edit Area (Expander to keep it clean)
                with st.expander(L.common.edit):
                    new_name = st.text_input(L.common.edit, value=ws.name, key=f"ren_input_{ws.id}")
                    if st.button(L.common.update, key=f"ren_btn_{ws.id}", use_container_width=True):
                        rename_workspace_callback(ws.id, new_name)
                        st.rerun()
                st.caption(
                    f"Blok: {ws.file_count} belge | Güncelleme: {ws.last_modified.strftime('%d.%m.%Y %H:%M')}"
                )

            with cols[1]:
                if not is_active:
                    if st.button(L.workspace.select, key=f"sel_{ws.id}"):
                        select_workspace_callback(ws.id)
                        st.rerun()
                else:
                    st.button(L.workspace.active, key=f"act_{ws.id}", disabled=True)

            with cols[2]:
                if st.button("🗑️", key=f"del_{ws.id}", help=L.common.delete):
                    delete_workspace_callback(ws.id)
                    st.rerun()

    st.divider()
    st.markdown(f"### {L.workspace.new_workspace}")
    new_name = st.text_input(L.workspace.name_placeholder, placeholder="Örn: Proje Analizi")
    if st.button(L.common.save, use_container_width=True, type="primary"):
        if new_name:
            create_workspace_callback(new_name)
            st.rerun()


@st.dialog("⚙️ Sistem Yapılandırması", width="large")
def global_settings_dialog():
    """Consolidated settings dialog replacing the sidebar configuration."""

    @st.fragment
    def render_settings_fragment():
        L = st.session_state.locale
        tab1, tab2, tab3, tab4 = st.tabs(
            [L.settings.llm_tab, L.settings.embed_tab, L.settings.system_tab, L.settings.tools_tab]
        )

        with tab1:
            render_llm_settings(key_prefix="dlg_")

        with tab2:
            render_embedding_settings(key_prefix="dlg_")

        with tab3:
            render_data_settings(key_prefix="dlg_")

        with tab4:
            L = st.session_state.locale
            st.markdown(f"### {L.settings.tools_tab}")
            col1, col2 = st.columns(2)

            active_id = st.session_state.get(SessionKeys.ACTIVE_WORKSPACE_ID.value)
            if col1.button(L.settings.clear_chat, use_container_width=True):
                if active_id:
                    clear_chat_history_callback(active_id)
                    st.rerun()

            if col2.button(L.settings.clear_cache, use_container_width=True):
                clear_cache_callback()
                st.rerun()

            st.divider()

            # ID Consistency & Health Utility
            st.markdown("### 🛠️ Sistem Sağlığı")
            from app.core import DatabaseManager
            db = DatabaseManager()
            ws_id = st.session_state.get(SessionKeys.ACTIVE_WORKSPACE_ID.value)
            sess_id = st.session_state.get(SessionKeys.ACTIVE_SESSION_ID.value)

            issues = []
            if ws_id:
                if sess_id:
                    sess = db.chat_sessions.get_by_id(sess_id)
                    if sess and sess.workspace_id != ws_id:
                        issues.append("⚠️ Oturum ve Alan Uyumsuzluğu! Veritabanı tutarlılığı için bu durumu düzeltmenizi öneririz.")

                db_files = db.files.count_by_workspace(ws_id)
                if db_files > 0:
                    st.success(f"✅ Alan Durumu: {db_files} döküman başarıyla eşleşti.")
                else:
                    st.info("ℹ️ Bu alan henüz boş görünüyor.")

            for issue in issues:
                st.error(issue)
                if st.button("Uyumsuzluğu Otomatik Düzelt", use_container_width=True):
                    st.session_state[SessionKeys.ACTIVE_SESSION_ID.value] = None
                    st.rerun()

            st.divider()

            # Inline Confirmation for System Reset to avoid nested dialogs
            if "show_reset_confirm" not in st.session_state:
                st.session_state.show_reset_confirm = False

            if not st.session_state.show_reset_confirm:
                if st.button("⚠️ Sistemi Tamamen Sıfırla", use_container_width=True, type="secondary"):
                    st.session_state.show_reset_confirm = True
                    st.rerun(scope="fragment")
            else:
                st.error("DİKKAT: Tüm veritabanı, çalışma alanları ve yüklü belgeler silinecek! Bu işlem geri alınamaz.")
                confirm = st.text_input("Onaylamak için 'SIFIRLA' yazın")

                c1, c2 = st.columns(2)
                if c1.button("İptal", use_container_width=True):
                    st.session_state.show_reset_confirm = False
                    st.rerun(scope="fragment")

                if c2.button("Sıfırlamayı Onayla", type="primary", use_container_width=True, disabled=confirm != "SIFIRLA"):
                    from app.ui.callbacks import reset_system_callback
                    reset_system_callback()
                    st.session_state.show_reset_confirm = False
                    st.rerun(scope="app") 

    render_settings_fragment()


@st.dialog("📚 Belge Kütüphanesi", width="large")
def document_library_dialog(settings: dict):
    """Dialog for document management within the active workspace."""
    from app.ui.pages.library_page import render_library_page
    render_library_page(settings=settings)


@st.dialog("💬 Sohbet Geçmişi", width="large")
def chat_sessions_dialog():
    """Dialog for managing multiple chat threads in a workspace."""
    L = st.session_state.locale
    active_ws_id = st.session_state.get(SessionKeys.ACTIVE_WORKSPACE_ID.value)
    if not active_ws_id:
        st.warning(L.workspace.no_active)
        return

    db = get_cached_database_manager()
    sessions = db.chat_sessions.get_by_workspace(active_ws_id)
    active_session_id = st.session_state.get(SessionKeys.ACTIVE_SESSION_ID.value)

    st.markdown("### 🕒 Kayıtlı Oturumlar")

    # "Varsayılan" oturum (session_id = None)
    default_cols = st.columns([4, 1, 1])
    is_default_active = active_session_id is None
    default_cols[0].write("**Ana Akış**" + (" (Aktif)" if is_default_active else ""))
    default_cols[0].caption("Genel sohbet geçmişi")

    if not is_default_active:
        if default_cols[1].button("Seç", key="sel_default"):
            select_chat_session_callback(None)
            st.rerun()
    else:
        default_cols[1].button("Aktif", key="act_default", disabled=True)

    st.divider()

    if not sessions:
        st.info("Henüz özel bir oturum oluşturulmadı.")
    else:
        for sess in sessions:
            cols = st.columns([4, 1, 1])
            is_active = sess.id == active_session_id

            with cols[0]:
                st.write(f"**{sess.title}**" + (" (Aktif)" if is_active else ""))
                st.caption(f"Son mesaj: {sess.last_message_at.strftime('%d.%m %H:%M')}")

            with cols[1]:
                if not is_active:
                    if st.button("Seç", key=f"sess_sel_{sess.id}"):
                        select_chat_session_callback(sess.id)
                        st.rerun()
                else:
                    st.button("Aktif", key=f"sess_act_{sess.id}", disabled=True)

            with cols[2]:
                if st.button("🗑️", key=f"sess_del_{sess.id}"):
                    delete_chat_session_callback(sess.id)
                    st.rerun()

    st.divider()
    st.markdown(f"### ➕ {L.chat.no_history}")
    new_title = st.text_input(L.chat.sources_title, placeholder="Örn: Rapor Analizi")
    if st.button(L.common.save, use_container_width=True, type="primary"):
        if new_title:
            create_chat_session_callback(active_ws_id, new_title)
            st.rerun()
