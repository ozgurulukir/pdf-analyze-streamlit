"""Application configuration and settings."""
import os
import json
import requests
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv

# Load .env
load_dotenv()


def get_ollama_models(base_url: str = "http://localhost:11434") -> List[Dict[str, str]]:
    """
    Fetch available models from Ollama API.
    
    Args:
        base_url: Ollama server URL
        
    Returns:
        List of model dictionaries with 'label' and 'value' keys
    """
    default_models = [
        {"label": "nomic-embed-text (varsayılan)", "value": "nomic-embed-text"},
        {"label": "mxbai-embed-large", "value": "mxbai-embed-large"},
        {"label": "all-minilm", "value": "all-minilm"},
        {"label": "bge-m3", "value": "bge-m3"},
    ]
    
    try:
        response = requests.get(f"{base_url}/api/tags", timeout=5)
        if response.status_code == 200:
            data = response.json()
            models = data.get("models", [])
            if models:
                # Extract model names and create options
                model_options = []
                for m in models:
                    name = m.get("name", "")
                    # Remove tag if present (e.g., "model:latest" -> "model")
                    if ":" in name:
                        name = name.split(":")[0]
                    model_options.append({
                        "label": f"{name} (indirilmiş)",
                        "value": name
                    })
                return model_options
    except Exception as e:
        print(f"Ollama API hatası: {e}")
    
    return default_models


def get_ollama_llm_models(base_url: str = "http://localhost:11434") -> List[Dict[str, str]]:
    """
    Fetch available LLM models from Ollama API.
    
    Args:
        base_url: Ollama server URL
        
    Returns:
        List of model dictionaries with 'label' and 'value' keys
    """
    default_models = [
        {"label": "DeepSeek V2 (varsayılan)", "value": "deepseek-v2:671b"},
        {"label": "Qwen 2.5", "value": "qwen2.5:7b"},
        {"label": "Llama 3.1", "value": "llama3.1:8b"},
        {"label": "Mistral", "value": "mistral:7b"},
    ]
    
    try:
        response = requests.get(f"{base_url}/api/tags", timeout=5)
        if response.status_code == 200:
            data = response.json()
            models = data.get("models", [])
            if models:
                # Filter for likely LLM models (exclude embedding models)
                embed_keywords = ["embed", "embedding", "nomic-embed"]
                llm_models = []
                for m in models:
                    name = m.get("name", "")
                    # Skip embedding models
                    if any(kw in name.lower() for kw in embed_keywords):
                        continue
                    # Remove tag
                    if ":" in name:
                        name = name.split(":")[0]
                    size_gb = m.get("size", 0) / (1024**3)
                    llm_models.append({
                        "label": f"{name} ({size_gb:.1f}GB)",
                        "value": name
                    })
                if llm_models:
                    return llm_models
    except Exception as e:
        print(f"Ollama API hatası: {e}")
    
    return default_models


@dataclass
class AppConfig:
    """Application configuration."""

    # App settings
    APP_TITLE: str = "PDF Analyzer Pro"
    APP_ICON: str = "📄"
    APP_DESCRIPTION: str = "AI-Powered Document Analysis"

    # ----- LLM Ayarları -----
    # OpenAI-compatible endpoint (Ollama Cloud, vLLM, Groq, Together vs.)
    LLM_BASE_URL: str = field(default_factory=lambda: os.getenv("LLM_BASE_URL", "https://ollama.com/v1"))
    LLM_API_KEY: str = field(default_factory=lambda: os.getenv("LLM_API_KEY", "ollama"))
    LLM_MODEL: str = field(default_factory=lambda: os.getenv("LLM_MODEL", "deepseek-v2:671b"))
    LLM_TEMPERATURE: float = 0.3

    # ----- Embedding Ayarları -----
    # Ollama yerel sunucu
    OLLAMA_BASE_URL: str = field(default_factory=lambda: os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))
    EMBED_MODEL: str = field(default_factory=lambda: os.getenv("EMBED_MODEL", "nomic-embed-text"))
    
    # HuggingFace alternatif
    USE_HUGGINGFACE: bool = field(default_factory=lambda: os.getenv("USE_HUGGINGFACE", "false").lower() == "true")
    HF_EMBED_MODEL: str = field(default_factory=lambda: os.getenv("HF_EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2"))

    # Chunking settings
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200

    # File settings
    ALLOWED_FILE_TYPES: List[str] = field(default_factory=lambda: ["pdf", "txt", "docx", "html", "md"])
    MAX_FILE_SIZE_MB: int = 50
    MAX_FILE_SIZE_BYTES: int = 50 * 1024 * 1024

    # Retriever settings
    DEFAULT_RETRIEVER_K: int = 4

    # Chat settings
    MAX_MESSAGES_IN_MEMORY: int = 100
    MESSAGE_SUMMARY_THRESHOLD: int = 50

    # Database settings
    DB_PATH: str = "data/app.db"
    CHROMA_PERSIST_DIR: str = "data/chroma"

    # UI settings
    SIDEBAR_DEFAULT_OPEN: bool = True

    # Preference weights
    DEFAULT_PREFERENCE_WEIGHTS: Dict[str, float] = field(default_factory=lambda: {
        "concise": 0.5,
        "detailed": 0.5,
        "examples": 0.5,
        "step_by_step": 0.5
    })

    def __post_init__(self):
        Path(self.DB_PATH).parent.mkdir(parents=True, exist_ok=True)
        Path(self.CHROMA_PERSIST_DIR).mkdir(parents=True, exist_ok=True)


# LLM Model seçenekleri
LLM_MODEL_OPTIONS = [
    {"label": "DeepSeek V2", "value": "deepseek-v2:671b"},
    {"label": "Qwen 2.5", "value": "qwen2.5:7b"},
    {"label": "Llama 3.1", "value": "llama3.1:8b"},
    {"label": "Mistral", "value": "mistral:7b"},
    {"label": "Gemma 2", "value": "gemma2:9b"},
    {"label": "Phi 3", "value": "phi3:14b"},
    {"label": "Aya", "value": "aya:8b"},
    {"label": "Command R", "value": "command-r7b-enterprise"},
]

# Embedding Model seçenekleri
EMBED_MODEL_OPTIONS = [
    {"label": "nomic-embed-text", "value": "nomic-embed-text", "desc": "Önerilen"},
    {"label": "mxbai-embed-large", "value": "mxbai-embed-large", "desc": "Yüksek kalite"},
    {"label": "all-minilm", "value": "all-minilm", "desc": "Hızlı"},
    {"label": "bge-m3", "value": "bge-m3", "desc": "Çok dilli"},
]

# HuggingFace Embedding seçenekleri
HF_EMBED_OPTIONS = [
    {"label": "all-MiniLM-L6-v2", "value": "sentence-transformers/all-MiniLM-L6-v2"},
    {"label": "multi-qa-mpnet-base", "value": "sentence-transformers/multi-qa-mpnet-base-cos-v1"},
    {"label": "bge-small-en-v1.5", "value": "BAAI/bge-small-en-v1.5"},
]

# Quick prompt suggestions
QUICK_PROMPTS = [
    "Bu belgede ne hakkında bilgi var?",
    "Özet çıkarır mısın?",
    "Ana noktaları listeler misin?",
    "Detaylı açıklama yapabilir misin?",
]

# CSS for tilted-T layout
TILTED_T_CSS = """
<style>
    .stApp { background: linear-gradient(to bottom right, #f8f9fa, #e9ecef); }
    .stButton > button { border-radius: 0.5rem; font-weight: 600; transition: all 0.3s ease; }
    .stButton > button:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
    .stChatMessage { border-radius: 16px; }
    div[data-testid="stMetricValue"] { font-size: 1.5rem; }
    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-track { background: #f1f1f1; }
    ::-webkit-scrollbar-thumb { background: #888; border-radius: 4px; }
</style>
"""
