# RAG Uygulaması - Geliştirilmiş Versiyon

## 🚀 Özellikler

### 1. LLM Desteği
- **OpenAI-compatible API** ile herhangi bir LLM servisi kullanılabilir
- Ollama Cloud, vLLM, Groq, Together.ai, OpenAI vb.
- Sidebar'dan model seçimi ve yapılandırma

### 2. Embedding Desteği
- **Ollama yerel sunucu** (http://localhost:11434)
- **HuggingFace** alternatif olarak desteklenir
- Modeller: nomic-embed-text, mxbai-embed-large, all-minilm

### 3. Vector Store
- **ChromaDB** persistent storage (stored in `data/chroma`)
- Otomatik chunk'lama (RecursiveCharacterTextSplitter)
- DirectoryLoader ile çoklu dosya desteği

### 4. Streamlit Arayüz
- **Tilted-T Layout**: Geniş chat alanı + sidebar
- **Streaming yanıtlar**: Gerçek zamanlı LLM çıktısı
- **Mesaj geçmişi**: SQLite veritabanında (`data/app.db`) saklanır

---

## 📦 Kurulum

```bash
# Dependencies yükle
pip install -r requirements.txt

# .env dosyası oluştur
cp .env.example .env
```

---

## ⚙️ Yapılandırma

`.env` dosyasını düzenleyin:

```env
# LLM Ayarları
LLM_BASE_URL=https://ollama.com/v1
LLM_API_KEY=ollama
LLM_MODEL=deepseek-v2:671b

# Embedding Ayarları
OLLAMA_BASE_URL=http://localhost:11434
EMBED_MODEL=nomic-embed-text

# Veri Ayarları
DATA_DIR=data
CHROMA_PATH=data/chroma
```

---

## 📁 Kullanım

### 1. Belgeleri Hazırla
`./data` klasörüne belgelerinizi ekleyin:
- `.txt`, `.md`, `.html`, `.pdf`, `.docx`

### 2. Uygulamayı Çalıştır
```bash
streamlit run app/main.py
```

### 3. Sidebar'dan Yapılandır
- Veri klasörü yolunu ayarla
- LLM modelini seç
- Embedding modelini seç
- "Oluştur" butonuna tıkla

### 4. Soru Sor
Chat aracılığıyla belgeleriniz hakkında sorular sorun.

---

## 🔧 Sorun Giderme

### Ollama Çalışmıyor
```bash
# Ollama'yı başlat
ollama serve

# Modeli indir
ollama pull nomic-embed-text
ollama pull deepseek-v2:671b
```

### Vector Store Hatası
ChromaDB klasörünü silip yeniden oluşturun:
```bash
rm -rf data/chroma
```

### API Bağlantı Hatası
- `LLM_BASE_URL` doğru olduğundan emin olun
- Firewall port'ları kontrol edin (11434, 80, 443)

---

## 📂 Proje Yapısı

```
pdf-analyze-streamlit/
├── app/
│   └── main.py              # Ana uygulama
├── data/                    # Tüm veriler (DB, Chroma, Belgeler)
├── .env.example             # Örnek konfigürasyon
├── requirements.txt
└── README.md
```

---

## 🔨 Geliştirme

### Yeni Özellikler Ekleyin

1. **MultiQueryRetriever**: 
```python
from langchain.retrievers.multi_query import MultiQueryRetriever

retriever = MultiQueryRetriever.from_llm(
    retriever=base_retriever,
    llm=llm
)
```

2. **ConversationBufferMemory**:
```python
from langchain.memory import ConversationBufferMemory

memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True
)
```

3. **BM25 Retriever**:
```python
from langchain_community.retrievers import BM25Retriever
```

---

## 📝 Lisans

MIT License
