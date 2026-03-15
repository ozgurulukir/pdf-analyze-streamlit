# Modern RAG App - Tilted-T Layout Implementation Plan

## ✅ Completed Tasks

### Phase 1: Project Structure & Configuration ✅
- [x] Update project structure
- [x] Create new config with all settings
- [x] Update requirements.txt with new dependencies
- [x] Update .streamlit/config.toml

### Phase 2: Data Models & Storage ✅
- [x] Create SQLite database models (workspaces, files, preferences, messages)
- [x] Create data classes for all entities
- [x] Implement workspace manager
- [x] Implement file/chunk manager

### Phase 3: Chroma Integration ✅
- [x] Create Chroma client manager
- [x] Implement collection naming strategy
- [x] Implement chunking and embedding pipeline
- [x] Handle incremental updates

### Phase 4: Background Processing ✅
- [x] Implement job queue system
- [x] Create worker thread for embeddings
- [x] Add progress tracking

### Phase 5: UI Components - Layout ✅
- [x] Create tilted-T layout
- [x] Implement header with theme toggle
- [x] Implement collapsible sidebar
- [x] Implement chat area

### Phase 6: UI Components - Workspace ✅
- [x] Workspace list/selector
- [x] File cards with actions
- [x] Upload handling
- [x] Progress bars

### Phase 7: UI Components - Chat ✅
- [x] Chat message rendering
- [x] Input bar with quick prompts
- [x] Keyboard shortcuts
- [x] Typing indicator

### Phase 8: Q&A Dashboard & Preferences ✅
- [x] Q&A history dashboard
- [x] Like/dislike system
- [x] Preference weights

### Phase 9: Caching & Persistence ✅
- [x] Message cache (LRU)
- [x] Embedding cache (in Chroma)
- [x] State persistence (SQLite)

### Phase 10: Error Handling & Security ✅
- [x] File size limits
- [x] Confirmation dialogs
- [x] Input sanitization

---

## Technical Decisions (Justified)

### Embedding Model
- **Model**: `text-embedding-3-small` (OpenAI)
- **Rationale**: Good balance of quality/speed/cost, 1536 dimensions

### Chunk Size & Overlap
- **Chunk Size**: 1000 characters
- **Overlap**: 200 characters
- **Rationale**: Balances context preservation with retrieval precision

### Background Job Approach
- **Method**: Python's `concurrent.futures.ThreadPoolExecutor`
- **Rationale**: Lightweight, integrates well with Streamlit, handles I/O-bound embedding tasks

### Caching
- **Message Cache**: 100 messages in-memory (LRU)
- **Embedding Cache**: SQLite with file hash lookup (via Chroma)
- **Eviction**: Mark old messages as summarized, store in DB

### Persistence
- **Workspaces**: SQLite (metadata) + Chroma (vectors)
- **Preferences**: SQLite
- **Messages**: SQLite with workspace_id scope

---

## Project Structure

```
pdf-analyze-streamlit/
├── app/
│   ├── __init__.py
│   ├── main.py              # Main application (tilted-T layout)
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py       # App configuration
│   │   ├── models.py       # Data models
│   │   ├── database.py     # SQLite manager
│   │   ├── chroma.py      # Chroma vector store
│   │   ├── loader.py      # Document loader
│   │   ├── jobs.py        # Background job queue
│   │   └── rag.py         # RAG chain & QA
│   └── ui/
│       ├── __init__.py
│       ├── chat.py        # Chat UI
│       ├── workspace.py   # Workspace sidebar
│       ├── header.py      # Header & nav
│       ├── dashboard.py   # Q&A dashboard
│       └── layout.py      # Tilted-T layout
├── data/                   # SQLite + Chroma storage
├── tests/
├── .streamlit/config.toml
├── requirements.txt
└── IMPLEMENTATION_PLAN.md
```

---

## To Run

```bash
# Install dependencies
uv pip install -r requirements.txt

# Set API key
export OPENAI_API_KEY=sk-...

# Run app
streamlit run app/main.py
```
