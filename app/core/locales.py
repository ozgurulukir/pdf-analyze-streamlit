"""
Centralized String Management & i18n System.
Uses Pydantic v2 for type-safe locale management.
"""

from typing import Literal

from pydantic import BaseModel, Field


class CommonStrings(BaseModel):
    """Common UI elements used across multiple pages."""
    success: str = "✅ Başarılı"
    error: str = "❌ Hata"
    warning: str = "⚠️ Uyarı"
    info: str = "ℹ️ Bilgi"
    save: str = "Kaydet"
    update: str = "Güncelle"
    delete: str = "Sil"
    cancel: str = "İptal"
    loading: str = "İşleniyor..."
    search: str = "Ara"
    edit: str = "Düzenle"
    confirm: str = "Onayla"
    refresh: str = "Yenile"
    active_label: str = "Aktif"
    passive_label: str = "Kapalı"
    dialog_reset_title: str = "Sistemi Sıfırla"
    dialog_workspace_title: str = "🎯 Çalışma Alanları"
    dialog_settings_title: str = "⚙️ Sistem Yapılandırması"
    dialog_library_title: str = "📚 Belge Kütüphanesi"
    dialog_chat_sessions_title: str = "💬 Sohbet Geçmişi"


class ChatStrings(BaseModel):
    """Strings for the Chat interface."""
    title: str = "Sohbet"
    input_placeholder: str = "Dökümanlarınız hakkında bir şeyler sorun..."
    add_to_kb: str = "⭐ Bilgi Bankasına Ekle"
    kb_added_toast: str = "⭐ Bilgi Bankasına kaydedildi!"
    kb_searching_tags: str = "🧠 İçerik analiz ediliyor ve etiketler oluşturuluyor..."
    no_history: str = "Henüz bir mesaj yok. İlk sorunuzu sorarak başlayın!"
    sources_title: str = "🔍 Alıntılanan Kaynaklar:"
    empty_title: str = "Size bugün nasıl yardımcı olabilirim?"
    empty_subtitle: str = "Dökümanlarınızı analiz etmek ve sorularınızı yanıtlamak için buradayım."
    sessions_title: str = "🕒 Kayıtlı Oturumlar"
    default_session_name: str = "Ana Akış"
    default_session_desc: str = "Genel sohbet geçmişi"
    sessions_empty: str = "Henüz özel bir oturum oluşturulmadı."
    new_session: str = "➕ Yeni Oturum"
    last_message: str = "Son mesaj: {}"


class KnowledgeBaseStrings(BaseModel):
    """Strings for the Knowledge Base page."""
    title: str = "Bilgi Bankası"
    search_label: str = "🔍 İçerik Araması"
    search_placeholder: str = "Soru veya cevapta ara..."
    tag_filter_label: str = "🏷️ Etiket Filtresi"
    no_results: str = "Kriterlere uygun kayıt bulunamadı."
    delete_confirm: str = "Kayıt Bilgi Bankasından silindi."
    details_label: str = "📝 Detaylar ve Kaynaklar"
    date_label: str = "Kayıt Tarihi"


class WorkspaceStrings(BaseModel):
    """Strings for Workspace management."""
    title: str = "Çalışma Alanları"
    current_areas: str = "📂 Mevcut Alanlar"
    new_workspace: str = "➕ Yeni Alan Oluştur"
    rename_dialog_title: str = "Çalışma Alanını Yeniden Adlandır"
    delete_confirm: str = "Çalışma alanını ve içindeki TÜM belgeleri silmek istediğinizden emin misiniz?"
    select: str = "Seç"
    rename: str = "Ad Değiştir"
    active: str = "Aktif"
    no_active: str = "Lütfen üst menüden bir çalışma alanı seçin."
    name_placeholder: str = "Alan ismi girin..."
    example_name: str = "Örn: Hukuki Belgeler"
    not_found: str = "Çalışma alanı bulunamadı."
    stats: str = "Blok: {} belge | Güncelleme: {}"


class LibraryStrings(BaseModel):
    """Strings for Document Library."""
    title: str = "Belgeler"
    header_subtitle: str = "Belge & Çalışma Alanı Yönetimi"
    header_caption: str = "Sistemi yapılandırın ve belgelerinizi yönetin"
    upload_label: str = "📤 Yeni Belgeler Yükle"
    upload_help: str = "PDF, TXT, DOCX desteklenir"
    upload_to: str = "'{}' Alanına Yükle"
    no_files: str = "Henüz belge yüklenmemiş."
    no_files_ws: str = "Bu çalışma alanında henüz belge yok."
    select_ws_to_list: str = "Belgelerini listelemek için bir çalışma alanı seçin."
    select_ws_to_upload: str = "Dosya yüklemek için önce bir çalışma alanı seçin."
    stats_label: str = "📊 Özet"
    manage_tab: str = "📁 Çalışma Alanları"
    upload_tab: str = "📤 Yükleme"
    files_tab: str = "📄 Tüm Belgeler"
    file_name: str = "Dosya Adı"
    file_type: str = "Tür"
    file_size: str = "Boyut"
    status: str = "Durum"
    status_all: str = "Tümü"
    status_processed: str = "İşlendi"
    status_processing: str = "İşleniyor"
    status_pending: str = "Bekliyor"
    status_error: str = "Hata"
    sync_data: str = "🔄 Verileri Senkronize Et"
    sync_help: str = "Eğer dosyalarınız görünmüyorsa bu butona basın."
    sync_success: str = "Senkronizasyon tamamlandı."
    listing_count: str = "{} belge listeleniyor"
    last_action: str = "Son işlem: {}"
    unknown: str = "Bilinmeyen"


class JobStrings(BaseModel):
    """Strings for Background Jobs."""
    waiting: str = "Bekleniyor..."
    processing: str = "🔄 İşleniyor: {}/{} dosya"
    completed: str = "✅ Başarıyla Tamamlandı"
    failed: str = "❌ İşlem Başarısız"
    please_wait: str = "Lütfen bekleyiniz..."
    error_detail: str = "Hata Detayı: {}"
    all_processed: str = "Tüm belgeler işlendi."


class SettingsStrings(BaseModel):
    """Strings for System Settings."""
    title: str = "Ayarlar"
    llm_tab: str = "🤖 LLM Ayarları"
    embed_tab: str = "🧠 Embedding"
    system_tab: str = "📁 Veri & Sistem"
    tools_tab: str = "🛠️ Araçlar"
    reset_system: str = "⚠️ Sistemi Sıfırla & Varsayılanları Yükle"
    clear_chat: str = "🗑️ Sohbeti Temizle"
    clear_cache: str = "🧹 Önbelleği Temizle"
    health_title: str = "🛠️ Sistem Sağlığı"
    health_issue_sync: str = "⚠️ Oturum ve Alan Uyumsuzluğu! Veritabanı tutarlılığı için bu durumu düzeltmenizi öneririz."
    health_ok: str = "✅ Alan Durumu: {} döküman başarıyla eşleşti."
    health_empty: str = "ℹ️ Bu alan henüz boş görünüyor."
    health_fix_btn: str = "Uyumsuzluğu Otomatik Düzelt"
    reset_warning: str = "DİKKAT: Tüm veritabanı, çalışma alanları ve yüklü belgeler silinecek! Bu işlem geri alınamaz."
    reset_confirm_placeholder: str = "Onaylamak için 'SIFIRLA' yazın"
    reset_confirm_btn: str = "Sıfırlamayı Onayla"

    # LLM Settings
    provider: str = "Sağlayıcı"
    provider_ollama: str = "Yerel Ollama"
    provider_cloud: str = "Ollama Cloud"
    provider_custom: str = "Özel (OpenAI Compatible)"
    api_connection: str = "🔗 API Bağlantısı"
    base_url: str = "Giriş Noktası (Base URL)"
    api_key: str = "API Anahtarı"
    model_settings: str = "⚙️ Model Ayarları"
    use_custom_model: str = "Özel model adı kullan"
    model_name: str = "Model Adı"
    select_model: str = "Model Seçin"
    temperature: str = "Temperature (Yaratıcılık)"
    test_connection: str = "🔌 Bağlantıyı Test Et"

    # Embedding Settings
    hf_model: str = "HF Model"
    ollama_url: str = "Ollama URL"
    embed_model_name: str = "Embed Model"
    model_change_warning: str = (
        "⚠️ **Model Değişikliği Notu:** Ollama ve HuggingFace modelleri farklı vektör boyutları kullanır. "
        "Sağlayıcı değiştirdiğinizde eski dökümanlar okunamaz hale gelebilir. Yeni modelin aktif olması için "
        "belgeleri tekrar yüklemeniz veya Sistemi Sıfırlamanız önerilir."
    )

    # Data Settings
    paths_title: str = "📁 Veri Yolları"
    data_dir: str = "Veri Klasörü"
    chroma_path: str = "Chroma Yolu"
    chunking_title: str = "✂️ Parçalama (Chunking)"
    chunk_size: str = "Boyut"
    chunk_overlap: str = "Overlap"


class AnalysisStrings(BaseModel):
    """Strings for Document Analysis."""
    title: str = "Analiz"
    header_caption: str = "Çalışma alanı istatistikleri ve geçmiş sorgular"
    summary_label: str = "📄 Özet"
    stats_tab: str = "📈 İstatistikler"
    pref_tab: str = "🎯 Prompt Tercihi"
    total_docs: str = "📄 Toplam Belge"
    processed: str = "✅ İşlenen"
    queued: str = "⏳ Kuyrukta"
    avg_size: str = "💾 Ort. Boyut"
    unique_sources: str = "📝 Özgün Kaynak"
    pref_title: str = "⚖️ Prompt Yönetimi"
    pref_subtitle: str = "Prompt parçalarını düzenleyin ve seçin"
    prompt_label: str = "Prompt İçeriği"
    prompt_include: str = "Sohbete Ekle"
    no_data: str = "Analiz edilecek veri bulunamadı."
    pref_conflict_detailed: str = "⚠️ Detaylı anlatım kapatıldı (Çelişki önlendi)."
    pref_conflict_concise: str = "⚠️ Kısa yanıt kapatıldı (Çelişki önlendi)."
    stats_title: str = "📈 Çalışma Alanı İstatistikleri"
    detail_analysis: str = "📋 Detaylı Boyut Analizi"


class MessageStrings(BaseModel):
    """Success and Error messages."""
    file_uploaded: str = "Dosya başarıyla yüklendi: {}"
    file_processed: str = "Dosya işlendi: {}"
    workspace_created: str = "Çalışma alanı oluşturuldu: {}"
    db_error: str = "Veritabanı hatası: {}"
    llm_error: str = "LLM hatası: {}"
    invalid_input: str = "Geçersiz giriş: {}"
    not_found: str = "Bulunamadı: {}"
    chat_init_failed: str = "Sohbet başlatılamadı: {}"
    tags_label: str = "Etiketler: {}"


class LocaleStrings(BaseModel):
    """Complete locale string collection."""
    lang: Literal["tr", "en"] = "tr"
    common: CommonStrings = Field(default_factory=CommonStrings)
    chat: ChatStrings = Field(default_factory=ChatStrings)
    knowledge: KnowledgeBaseStrings = Field(default_factory=KnowledgeBaseStrings)
    workspace: WorkspaceStrings = Field(default_factory=WorkspaceStrings)
    library: LibraryStrings = Field(default_factory=LibraryStrings)
    settings: SettingsStrings = Field(default_factory=SettingsStrings)
    analysis: AnalysisStrings = Field(default_factory=AnalysisStrings)
    messages: MessageStrings = Field(default_factory=MessageStrings)
    jobs: JobStrings = Field(default_factory=JobStrings)


# Default Turkish Locale
TR_LOCALE = LocaleStrings(
    lang="tr",
    common=CommonStrings(),
    chat=ChatStrings(),
    knowledge=KnowledgeBaseStrings(),
    workspace=WorkspaceStrings(),
    library=LibraryStrings(),
    settings=SettingsStrings(),
    analysis=AnalysisStrings(),
    messages=MessageStrings(),
    jobs=JobStrings()
)

# Example English Locale
EN_LOCALE = LocaleStrings(
    lang="en",
    common=CommonStrings(
        success="✅ Success", error="❌ Error", warning="⚠️ Warning", info="ℹ️ Info",
        save="Save", update="Update", delete="Delete", cancel="Cancel",
        loading="Processing...", search="Search", edit="Edit", confirm="Confirm", refresh="Refresh",
        active_label="Active", passive_label="Off",
        dialog_reset_title="Hard Reset System",
        dialog_workspace_title="🎯 Workspaces",
        dialog_settings_title="⚙️ System Configuration",
        dialog_library_title="📚 Document Library",
        dialog_chat_sessions_title="💬 Chat History"
    ),
    chat=ChatStrings(
        title="Chat",
        input_placeholder="Ask something about your documents...",
        add_to_kb="⭐ Add to Knowledge Base",
        kb_added_toast="⭐ Saved to Knowledge Base!",
        kb_searching_tags="🧠 Analyzing content and generating tags...",
        no_history="No messages yet. Start by asking your first question!",
        sources_title="🔍 Cited Sources:",
        empty_title="How can I help you today?",
        empty_subtitle="I'm here to analyze your documents and answer your questions.",
        sessions_title="🕒 Recorded Sessions",
        default_session_name="Primary Stream",
        default_session_desc="General chat history",
        sessions_empty="No custom sessions created yet.",
        new_session="➕ New Session",
        last_message="Last message: {}"
    ),
    knowledge=KnowledgeBaseStrings(
        title="Knowledge Base",
        search_label="🔍 Search Content",
        search_placeholder="Search in questions or answers...",
        tag_filter_label="🏷️ Tag Filter",
        no_results="No records found matching criteria.",
        delete_confirm="Record deleted from Knowledge Base.",
        details_label="📝 Details & Sources",
        date_label="Record Date"
    ),
    workspace=WorkspaceStrings(
        title="Workspaces",
        current_areas="📂 Existing Areas",
        new_workspace="➕ Create New Workspace",
        rename_dialog_title="Rename Workspace",
        delete_confirm="Are you sure you want to delete the workspace and ALL its documents?",
        select="Select",
        rename="Rename",
        active="Active",
        no_active="Please select a workspace from the top menu.",
        name_placeholder="Enter area name...",
        example_name="e.g. Legal Documents",
        not_found="Workspace not found.",
        stats="Area: {} documents | Update: {}"
    ),
    library=LibraryStrings(
        title="Documents",
        header_subtitle="Document & Workspace Management",
        header_caption="Configure the system and manage your documents",
        upload_label="📤 Upload New Documents",
        upload_help="PDF, TXT, DOCX supported",
        upload_to="Upload to '{}' Area",
        no_files="No documents uploaded yet.",
        no_files_ws="No documents in this workspace yet.",
        select_ws_to_list="Select a workspace to list your documents.",
        select_ws_to_upload="Select a workspace to upload files.",
        stats_label="📊 Summary",
        manage_tab="📁 Workspaces",
        upload_tab="📤 Upload",
        files_tab="📄 All Documents",
        file_name="File Name", file_type="Type", file_size="Size", status="Status",
        status_all="All",
        status_processed="Processed", status_processing="Processing",
        status_pending="Pending", status_error="Error",
        sync_data="🔄 Sync Data",
        sync_help="Press if files are not showing up.",
        sync_success="Synchronization complete.",
        listing_count="{} documents listed",
        last_action="Last action: {}",
        unknown="Unknown"
    ),
    jobs=JobStrings(
        waiting="Waiting...",
        processing="🔄 Processing: {}/{} files",
        completed="✅ Completed Successfully",
        failed="❌ Operation Failed",
        please_wait="Please wait...",
        error_detail="Error Detail: {}",
        all_processed="All documents processed."
    ),
    settings=SettingsStrings(
        title="Settings",
        llm_tab="🤖 LLM Settings", embed_tab="🧠 Embedding",
        system_tab="📁 Data & System", tools_tab="🛠️ Tools",
        reset_system="⚠️ Reset System & Load Defaults",
        clear_chat="🗑️ Clear Chat", clear_cache="🧹 Clear Cache",
        health_title="🛠️ System Health",
        health_issue_sync="⚠️ Session/Workspace Mismatch! We recommend fixing this for database consistency.",
        health_ok="✅ Area Status: {} documents successfully synchronized.",
        health_empty="ℹ️ This area appears to be empty.",
        health_fix_btn="Auto-Fix Mismatch",
        reset_warning="DANGER: All database, workspaces, and uploaded documents will be deleted! This cannot be undone.",
        reset_confirm_placeholder="Type 'SIFIRLA' to confirm (case sensitive)",
        reset_confirm_btn="Confirm Hard Reset",

        # LLM Settings
        provider="Provider",
        provider_ollama="Local Ollama",
        provider_cloud="Ollama Cloud",
        provider_custom="Custom (OpenAI Compatible)",
        api_connection="🔗 API Connection",
        base_url="Base URL",
        api_key="API Key",
        model_settings="⚙️ Model Settings",
        use_custom_model="Use custom model name",
        model_name="Model Name",
        select_model="Select Model",
        temperature="Temperature (Creativity)",
        test_connection="🔌 Test Connection",

        # Embedding Settings
        hf_model="HF Model",
        ollama_url="Ollama URL",
        embed_model_name="Embed Model",
        model_change_warning=(
            "⚠️ **Model Change Note:** Ollama and HuggingFace models use different vector dimensions. "
            "Changing providers may make existing documents unreadable. We recommend re-uploading documents "
            "or Hard Resetting the system for the new model to take effect."
        ),

        # Data Settings
        paths_title="📁 Data Paths",
        data_dir="Data Directory",
        chroma_path="Chroma Path",
        chunking_title="✂️ Chunking",
        chunk_size="Size",
        chunk_overlap="Overlap"
    ),
    analysis=AnalysisStrings(
        title="Analysis",
        header_caption="Workspace statistics and query history",
        summary_label="📄 Summary", stats_tab="📈 Statistics",
        pref_tab="🎯 Prompt Preferences", total_docs="📄 Total Docs",
        processed="✅ Processed", queued="⏳ Queued", avg_size="💾 Avg. Size",
        unique_sources="📝 Unique Sources", pref_title="⚖️ Prompt Management",
        pref_subtitle="Edit and select prompt fragments",
        prompt_label="Prompt Content",
        prompt_include="Include in Chat",
        no_data="No data found for analysis.",
        pref_conflict_detailed="⚠️ Detailed mode disabled (Conflict prevented).",
        pref_conflict_concise="⚠️ Concise mode disabled (Conflict prevented).",
        stats_title="📈 Workspace Statistics",
        detail_analysis="📋 Detailed Size Analysis"
    ),
    messages=MessageStrings(
        file_uploaded="File uploaded successfully: {}",
        file_processed="File processed: {}",
        workspace_created="Workspace created: {}",
        db_error="Database error: {}",
        llm_error="LLM error: {}",
        invalid_input="Invalid input: {}",
        not_found="Not found: {}",
        chat_init_failed="Chat start failed: {}",
        tags_label="Tags: {}"
    )
)


def get_locale(lang: str = "tr") -> LocaleStrings:
    """Utility to get a locale bundle."""
    return EN_LOCALE if lang == "en" else TR_LOCALE
