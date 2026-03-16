# PDF Analyzer Pro 🎯

AI tabanlı, modern ve modüler bir belge analiz uygulaması. Streamlit, LangChain ve Ollama/OpenAI teknolojileri kullanılarak geliştirilmiştir.

## 🚀 Öne Çıkan Özellikler

- 📁 **Gelişmiş Çalışma Alanı Yönetimi**: Belgelerinizi farklı çalışma alanlarında organize edin.
- 📄 **Kreuzberg Entegrasyonu**: PDF, DOCX, Resim ve daha birçok format dökümandan yüksek doğrulukla metin çıkarımı.
- 💬 **Gerçek Zamanlı Sohbet**: Streaming (akış) desteği ile gecikmesiz yanıtlar.
- 🧠 **Esnek LLM Gecitleri**: Ollama Cloud, Yerel Ollama veya herhangi bir OpenAI uyumlu API kullanım imkanı.
- 🔢 **Çoklu Embedding Desteği**: Yerel Ollama modelleri veya HuggingFace (transformer) modelleri arasında geçiş.
- 🎨 **Premium UI**: Modern Indigo-Dark tema ve tilted-T layout ile üst düzey kullanıcı deneyimi.
- 📊 **Q&A Dashboard**: Önceki sorulardan elde edilen içgörüleri yönetin ve oylayın.

## 🏗️ Mimari Yapı

Uygulama, sürdürülebilirlik ve tip güvenliği için dikey katmanlı bir mimari kullanır:

- **Core Layer**: 
    - `database.py`: SQLite odaklı veri yönetimi.
    - `chroma.py`: ChromaDB vektör veritabanı yönetimi.
    - `rag.py`: RAG (Retrieval-Augmented Generation) operasyonları ve istem şablonları.
    - `models.py`: Merkezi veri modelleri ve dataclass'lar.
- **Service Layer**: 
    - `file_service.py`: Belge yükleme ve OCR/Metin çıkarım servisleri.
    - `chat_service.py`: Sohbet ve RAG isteklerinin UI'dan bağımsız yönetimi.
- **UI Layer**: 
    - `main.py`: Uygulama giriş noktası ve session yönetimi.
    - `pages/`: Modüler sayfa yapıları (Sohbet, Belgeler, Analiz, Ayarlar).
    - `callbacks.py`: UI olaylarını servislere aktaran köprüler.

## 📦 Kurulum ve Çalıştırma

### Gereksinimler
- Python 3.10+
- Ollama (Yerel kullanım için) veya OpenAI-uyumlu API anahtarı.

### Adımlar

1. **Hazırlık**:
   ```bash
   # Sanal ortam oluşturun
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   ```

2. **Bağımlılıkları Yükleyin**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Çalıştırın**:
   ```bash
   streamlit run app/main.py
   ```

## 🔧 Kullanılan Teknolojiler

| Kategori | Teknoloji |
| :--- | :--- |
| **Frontend** | Streamlit 1.40+ |
| **Orchestration** | LangChain 0.3+ |
| **Vector DB** | ChromaDB |
| **Extraction** | Kreuzberg |
| **Embedding** | Ollama / HuggingFace |
| **Metreics** | Plotly |

## 🛠️ Geliştirici Notları

Proje, **Python Best Practices** prensiplerine göre refaktör edilmiştir:
- Tüm metodlar tip ipuçları (`Type Hints`) ile donatılmıştır.
- Google-style docstring formatı kullanılmıştır.
- Merkezi bir `logger` ve özel `AppError` sınıfları ile hata yönetimi optimize edilmiştir.
- `SessionKeys` Enum yapısı ile state yönetimi tip güvenli hale getirilmiştir.

---
⭐ Eğer bu projeyi faydalı buluyorsanız lütfen bir yıldız bırakmayı unutmayın!
