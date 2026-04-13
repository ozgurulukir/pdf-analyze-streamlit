# Doc Analyzer Pro 🎯

AI tabanlı, modern ve modüler bir belge analiz uygulaması. Streamlit, LangChain ve Ollama/OpenAI teknolojileri kullanılarak geliştirilmiştir. Proje, kurumsal standartlarda bir mimari ve yüksek performanslı işleme motorları üzerine inşa edilmiştir.

## 🚀 Öne Çıkan Özellikler

- 📁 **Gelişmiş Çalışma Alanı Yönetimi**: Belgelerinizi farklı çalışma alanlarında (workspaces) organize edin.
- 📄 **Üstün Metin Çıkarımı (Kreuzberg)**: PDF, DOCX, Resim ve daha birçok formattan **OCR destekli**, yüksek performanslı metin çıkarımı.
- 🌍 **%100 Yerelleştirme (i18n)**: Pydantic v2 tabanlı merkezi dil sistemi ile sıfır "hardcoded" metin. Dinamik dil desteği altyapısı.
- 💬 **Modern Sohbet Arayüzü**: Etkileşim kartları (Q&A cards) ile gruplandırılmış soru-cevap yapısı ve canlı akış desteği.
- 🧠 **Esnek LLM & Embedding**: Ollama (Cloud/Yerel) ve OpenAI uyumlu API desteği. HuggingFace modelleri ile yerel embedding imkanı.
- 🛡️ **Güvenlik & Stabilite**: Entegre **Rate Limiter**, içerik **Sanitizer**, merkezi `@handle_errors` dekoratörü ve veritabanı tabanlı kalıcı sistem ayarları.
- 🎨 **Premium UI**: Streamlit 1.40+ native bileşenleri (dialog, fragment, popover, status, pills) ile optimize edilmiş ve `@st.fragment` ile modülerleştirilmiş kullanıcı deneyimi.
- ⚙️ **Veritabanı Yönetimi**: **Alembic** ile otomatik şema migrasyonları (Zero-Config startup).

## 🏗️ Mimari Yapı

Uygulama, sürdürülebilirlik ve tip güvenliği için dikey katmanlı, **Repository Pattern** tabanlı modern bir mimari kullanır:

- **Core Layer**:
  - **Repository Pattern**: Veri erişimi arayüzler (Interfaces) üzerinden soyutlanmıştır. SQLite (Raw SQL) & ChromaDB entegrasyonu.
  - **Database Migrations**: Alembic entegrasyonu ile veritabanı şeması uygulama başlatıldığında otomatik olarak güncellenir.
  - **Pydantic v2 Config & i18n**: Tüm uygulama yapılandırması ve yerelleştirme metinleri tip güvenliği sağlayan modeller ile merkezi olarak yönetilir.
  - **Background Jobs**: Uzun süreli belge işleme süreçleri için iş kuyruğu yönetimi.
- **Service Layer**: İş mantığı, asenkron sohbet servisleri ve belge işleme boru hatları (pipelines).
- **UI Layer**:
  - **State Management**: Merkezi `AppState` yöneticisi ile tip güvenli `st.session_state` erişimi.
  - **Error Handling**: Merkezi `@handle_errors` dekoratörü ile standartlaştırılmış UI hata yönetimi.
  - **Modular Components**: `@st.fragment` ile izole edilmiş hızlı arayüz bileşenleri.

## 📦 Kurulum ve Çalıştırma

### Gereksinimler

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (Astral Python paket yöneticisi)
- **Sistem Bağımlılıkları (OCR ve Döküman İşleme)**:
  - **Tesseract OCR**: Resimlerden ve taranmış PDF'lerden metin çıkarımı için.
  - **Pandoc**: DOCX, PPTX ve diğer döküman formatlarını işleyebilmek için.
  - **Excel Desteği**: `.xlsx` dosyaları Kreuzberg tarafından yerleşik olarak desteklenir.

  **Kurulum Komutları:**
  - **Windows**: `choco install tesseract pandoc` veya manuel kurulum ([Tesseract](https://github.com/UB-Mannheim/tesseract/wiki), [Pandoc](https://pandoc.org/installing.html))
  - **Linux**: `sudo apt install tesseract-ocr pandoc`
  - **macOS**: `brew install tesseract pandoc`
- Ollama (Yerel kullanım için) veya OpenAI-uyumlu API anahtarı.

### Adımlar

1. **Bağımlılıkları Senkronize Edin**:

   ```bash
   uv sync
   ```

2. **Uygulamayı Çalıştırın**:

   ```bash
   uv run streamlit run app/main.py
   ```

3. **Testleri Çalıştırın**:

   ```bash
   uv run pytest
   ```

## 🛠️ Geliştirici Notları

Proje, **Astral uv** standartlarına göre paketlenmiş ve modernize edilmiştir:

- **Tip Güvenliği**: Pydantic v2 ve Mypy entegrasyonu.
- **Kod Kalitesi**: Ruff, Black ve Isort ile otomatik formatlama ve linting.
- **Genişletilebilirlik**: Yeni veritabanı veya LLM sağlayıcıları eklemek için hazır Interface yapıları.

---

⭐ Eğer bu projeyi faydalı buluyorsanız lütfen bir yıldız bırakmayı unutmayın!
