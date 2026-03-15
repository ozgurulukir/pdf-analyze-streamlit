# PDF Analyzer Pro v2.0

Modern ve geliştirilmiş Streamlit tabanlı PDF Analiz uygulaması.

## 🚀 Özellikler

- 📄 **Çoklu Dosya Desteği** - PDF, TXT, MD dosyaları yükleyin
- 💬 **Sohbet Arayüzü** - Modern chat interface ile sorular sorun
- 🔍 **Akıllı Arama** - Similarity, SVM ve MMR retriever seçenekleri
- ⚡ **Hızlı İşleme** - Chunking ve embedding optimizasyonları
- 🎨 **Modern UI** - Streamlit component kütüphaneleri ile zengin arayüz
- 📊 **Document Preview** - Yüklenen belgeleri görüntüleyin

## 📦 Kurulum

### Gereksinimler

- Python 3.10+
- OpenAI API Key

### Adımlar

```bash
# Repository'yi klonlayın
git clone https://github.com/mehmetba/pdf-analyze-streamlit.git
cd pdf-analyze-streamlit

# Sanal ortam oluşturun
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Bağımlılıkları yükleyin
pip install -r requirements.txt

# .env dosyasını oluşturun
cp .env.example .env
# .env dosyasına OpenAI API Key'inizi ekleyin

# Uygulamayı çalıştırın
streamlit run app/main.py
```

## 🏗️ Proje Yapısı

```
pdf-analyze-streamlit/
├── app/
│   ├── __init__.py
│   ├── main.py              # Ana uygulama
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py       # Konfigürasyon
│   │   ├── loader.py       # Belge yükleme
│   │   └── retriever.py    # Retrieval ve QA
│   └── ui/
│       ├── __init__.py
│       ├── sidebar.py      # Sidebar bileşenleri
│       ├── upload.py       # Upload bileşenleri
│       └── chat.py         # Chat arayüzü
├── tests/
│   ├── conftest.py
│   ├── test_loader.py
│   └── test_retriever.py
├── .streamlit/
│   └── config.toml
├── .env.example
├── pyproject.toml
└── requirements.txt
```

## 🔧 Kullanılan Teknolojiler

| Kategori | Teknoloji |
|----------|-----------|
| Web Framework | Streamlit 1.40+ |
| AI Framework | LangChain 0.3+ |
| Vector Store | FAISS |
| Embeddings | OpenAI |
| PDF Parsing | PyPDF2 |
| UI Components | streamlit-option-menu, streamlit-extras |

## ⚙️ Konfigürasyon

### Environment Değişkenleri

`.env` dosyasına ekleyin:

```env
OPENAI_API_KEY=sk-your-api-key-here
```

### Streamlit Ayarları

`.streamlit/config.toml` dosyasından özelleştirin:

```toml
[theme]
primaryColor = "#FF4B4B"
backgroundColor = "#FFFFFF"

[server]
port = 8501
```

## 🧪 Test

```bash
# Testleri çalıştırın
pytest tests/

# Coverage ile test
pytest --cov=app tests/
```

## 📝 Lisans

MIT License - Detaylar için LICENSE dosyasına bakın.

## 👤 Yazar

Mehmet Balioglu - [Twitter](https://twitter.com/mehmet_ba7)

---

⭐ Bu projeyi beğendiyseniz yıldız vermeyi unutmayın!
