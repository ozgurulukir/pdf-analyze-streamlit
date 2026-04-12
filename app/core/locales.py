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
    active: str = "Aktif"
    no_active: str = "Lütfen üst menüden bir çalışma alanı seçin."
    name_placeholder: str = "Alan ismi girin..."


class LibraryStrings(BaseModel):
    """Strings for Document Library."""
    title: str = "Belgeler"
    header_subtitle: str = "Belge & Çalışma Alanı Yönetimi"
    header_caption: str = "Sistemi yapılandırın ve belgelerinizi yönetin"
    upload_label: str = "📤 Yeni Belgeler Yükle"
    upload_help: str = "PDF, TXT, DOCX desteklenir"
    no_files: str = "Henüz belge yüklenmemiş."
    stats_label: str = "📊 Özet"
    manage_tab: str = "📁 Çalışma Alanları"
    upload_tab: str = "📤 Yükleme"
    files_tab: str = "📄 Tüm Belgeler"
    file_name: str = "Dosya Adı"
    file_type: str = "Tür"
    file_size: str = "Boyut"
    status: str = "Durum"
    status_processed: str = "İşlendi"
    status_processing: str = "İşleniyor"
    status_pending: str = "Bekliyor"
    status_error: str = "Hata"
    sync_data: str = "🔄 Verileri Senkronize Et"
    sync_help: str = "Eğer dosyalarınız görünmüyorsa bu butona basın."
    sync_success: str = "Senkronizasyon tamamlandı."


class SettingsStrings(BaseModel):
    """Strings for System Settings."""
    title: str = "Ayarlar"
    llm_tab: str = "🤖 LLM Ayarları"
    embed_tab: str = "🧠 Embedding"
    system_tab: str = "📁 Veri & Sistem"
    tools_tab: str = "🛠️ Araçlar"
    reset_system: str = "⚠️ Sistemi Tamamen Sıfırla"
    clear_chat: str = "🗑️ Sohbeti Temizle"
    clear_cache: str = "🧹 Önbelleği Temizle"


class AnalysisStrings(BaseModel):
    """Strings for Document Analysis."""
    title: str = "Analiz"
    header_caption: str = "Çalışma alanı istatistikleri ve geçmiş sorgular"
    summary_label: str = "📄 Özet"
    stats_tab: str = "📈 İstatistikler"
    pref_tab: str = "🎯 Tercihler & Geçmiş"
    total_docs: str = "📄 Toplam Belge"
    processed: str = "✅ İşlenen"
    queued: str = "⏳ Kuyrukta"
    avg_size: str = "💾 Ort. Boyut"
    unique_sources: str = "📝 Özgün Kaynak"
    pref_title: str = "⚖️ Tercihlerinizi Ayarlayın"
    pref_subtitle: str = "Cevap tarzınızı özelleştirin"
    no_data: str = "Analiz edilecek veri bulunamadı."


class MessageStrings(BaseModel):
    """Success and Error messages."""
    file_uploaded: str = "Dosya başarıyla yüklendi: {}"
    file_processed: str = "Dosya işlendi: {}"
    workspace_created: str = "Çalışma alanı oluşturuldu: {}"
    db_error: str = "Veritabanı hatası: {}"
    llm_error: str = "LLM hatası: {}"
    invalid_input: str = "Geçersiz giriş: {}"
    not_found: str = "Bulunamadı: {}"


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
    messages=MessageStrings()
)

# Example English Locale
EN_LOCALE = LocaleStrings(
    lang="en",
    common=CommonStrings(
        success="✅ Success", error="❌ Error", warning="⚠️ Warning", info="ℹ️ Info",
        save="Save", update="Update", delete="Delete", cancel="Cancel",
        loading="Processing...", search="Search", edit="Edit", confirm="Confirm", refresh="Refresh",
        active_label="Active", passive_label="Off"
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
        empty_subtitle="I'm here to analyze your documents and answer your questions."
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
        active="Active",
        no_active="Please select a workspace from the top menu.",
        name_placeholder="Enter area name..."
    ),
    library=LibraryStrings(
        title="Documents",
        header_subtitle="Document & Workspace Management",
        header_caption="Configure the system and manage your documents",
        upload_label="📤 Upload New Documents",
        upload_help="PDF, TXT, DOCX supported",
        no_files="No documents uploaded yet.",
        stats_label="📊 Summary",
        manage_tab="📁 Workspaces",
        upload_tab="📤 Upload",
        files_tab="📄 All Documents",
        file_name="File Name", file_type="Type", file_size="Size", status="Status",
        status_processed="Processed", status_processing="Processing",
        status_pending="Pending", status_error="Error",
        sync_data="🔄 Sync Data",
        sync_help="Press if files are not showing up.",
        sync_success="Synchronization complete."
    ),
    settings=SettingsStrings(
        title="Settings",
        llm_tab="🤖 LLM Settings", embed_tab="🧠 Embedding",
        system_tab="📁 Data & System", tools_tab="🛠️ Tools",
        reset_system="⚠️ Hard Reset System", clear_chat="🗑️ Clear Chat", clear_cache="🧹 Clear Cache"
    ),
    analysis=AnalysisStrings(
        title="Analysis",
        header_caption="Workspace statistics and query history",
        summary_label="📄 Summary", stats_tab="📈 Statistics",
        pref_tab="🎯 Preferences & History", total_docs="📄 Total Docs",
        processed="✅ Processed", queued="⏳ Queued", avg_size="💾 Avg. Size",
        unique_sources="📝 Unique Sources", pref_title="⚖️ Adjustment Panel",
        pref_subtitle="Customize your response style", no_data="No data found for analysis."
    ),
    messages=MessageStrings(
        file_uploaded="File uploaded successfully: {}",
        file_processed="File processed: {}",
        workspace_created="Workspace created: {}",
        db_error="Database error: {}",
        llm_error="LLM error: {}",
        invalid_input="Invalid input: {}",
        not_found="Not found: {}"
    )
)


def get_locale(lang: str = "tr") -> LocaleStrings:
    """Utility to get a locale bundle."""
    return EN_LOCALE if lang == "en" else TR_LOCALE
