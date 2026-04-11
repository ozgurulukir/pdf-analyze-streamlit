# Doc Analyzer Pro 🎯

AI tabanlı, modern ve modüler bir belge analiz uygulaması. Streamlit, LangChain ve Ollama/OpenAI teknolojileri kullanılarak geliştirilmiştir. Artık PDF'in yanı sıra DOCX, TXT ve daha birçok formatı desteklemektedir.

## 🚀 Öne Çıkan Özellikler

- 📁 **Gelişmiş Çalışma Alanı Yönetimi**: Belgelerinizi farklı çalışma alanlarında organize edin.
- 📄 **Üstün Metin Çıkarımı**: PDF, DOCX, Resim ve daha birçok format dökümandan yüksek doğrulukla metin çıkarımı.
- 💬 **Gerçek Zamanlı Sohbet**: Streaming (akış) desteği ile gecikmesiz yanıtlar.
- 🧠 **Esnek LLM Geçitleri**: Ollama Cloud, Yerel Ollama veya herhangi bir OpenAI uyumlu API kullanım imkanı.
- 🔢 **Çoklu Embedding Desteği**: Yerel Ollama modelleri veya HuggingFace modelleri arasında geçiş.
- 🎨 **Modern UI**: Streamlit 1.40+ native bileşenleri (dialog, popover, status) ile optimize edilmiş kullanıcı deneyimi.

## 🏗️ Mimari Yapı

Uygulama, sürdürülebilirlik ve tip güvenliği için dikey katmanlı bir mimari kullanır:

- **Core Layer**: Veritabanı (SQLite), Vektör DB (ChromaDB) ve RAG operasyonları.
- **Service Layer**: Belge işleme ve sohbet servisleri.
- **UI Layer**: Streamlit tabanlı modüler sayfalar ve navigasyon.

## 📦 Kurulum ve Çalıştırma

### Gereksinimler
- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (Astral Python paket yöneticisi)
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

Proje, **Astral uv** standartlarına göre paketlenmiştir:
- Tüm bağımlılıklar `pyproject.toml` dosyasında yönetilir.
- `uv.lock` ile tekrarlanabilir ortamlar sağlanır.
- Geliştirme araçları (pytest, ruff, black) `dev` bağımlılık grubunda tanımlıdır.

---
⭐ Eğer bu projeyi faydalı buluyorsanız lütfen bir yıldız bırakmayı unutmayın!
