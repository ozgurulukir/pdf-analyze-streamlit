# Doc Analyzer Pro 🎯

AI tabanlı, modern ve modüler bir belge analiz uygulaması. Streamlit, LangChain ve Ollama/OpenAI teknolojileri kullanılarak geliştirilmiştir. Proje, kurumsal standartlarda bir mimari ve yüksek performanslı işleme motorları üzerine inşa edilmiştir.

## 🚀 Öne Çıkan Özellikler

- 📁 **Gelişmiş Çalışma Alanı Yönetimi**: Belgelerinizi farklı çalışma alanlarında (workspaces) organize edin.
- 📄 **Üstün Metin Çıkarımı (Kreuzberg)**: PDF, DOCX, Resim ve daha birçok formattan **OCR destekli**, yüksek performanslı metin çıkarımı.
- 💬 **Gerçek Zamanlı Sohbet**: Streaming (akış) desteği ve akıllı bağlam yönetimi ile gecikmesiz yanıtlar.
- 🧠 **Esnek LLM & Embedding**: Ollama (Cloud/Yerel) ve OpenAI uyumlu API desteği. HuggingFace modelleri ile yerel embedding imkanı.
- 🛡️ **Güvenlik & Stabilite**: Entegre **Rate Limiter**, içerik **Sanitizer** (temizleyici) ve sistem için otomatik **Health Checks**.
- 🎨 **Premium UI**: Streamlit 1.40+ native bileşenleri (dialog, popover, status) ve özel CSS dokunuşları ile optimize edilmiş kullanıcı deneyimi.

## 🏗️ Mimari Yapı

Uygulama, sürdürülebilirlik ve tip güvenliği için dikey katmanlı, **Repository Pattern** tabanlı modern bir mimari kullanır:

- **Core Layer**:
  - **Repository Pattern**: Veri erişimi arayüzler (Interfaces) üzerinden soyutlanmıştır (SQLite & ChromaDB).
  - **Pydantic v2 Config**: Tüm uygulama yapılandırması tip güvenliği sağlayan `AppConfig` modeli ile yönetilir.
  - **Background Jobs**: Uzun süreli belge işleme süreçleri için iş kuyruğu yönetimi.
- **Service Layer**: İş mantığı, asenkron sohbet servisleri ve belge işleme boru hatları (pipelines).
- **UI Layer**: Streamlit tabanlı modüler sayfalar, sidebar bileşenleri ve dinamik callback yönetimi.

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
