"""Prompt loader for external configuration."""
import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path

from app.core.logger import get_logger

logger = get_logger(__name__)


class PromptLoader:
    """
    Load and manage prompts from external configuration.
    
    Supports YAML configuration files with fallback to defaults.
    """
    
    _instance: Optional['PromptLoader'] = None
    _prompts: Dict[str, Any] = {}
    _loaded: bool = False
    
    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the prompt loader."""
        if not self._loaded:
            self._load_prompts()
            self._loaded = True
    
    def _load_prompts(self) -> None:
        """Load prompts from YAML configuration file."""
        # Try to find prompts.yaml in multiple locations
        possible_paths = [
            Path("app/core/config/prompts.yaml"),
            Path("config/prompts.yaml"),
            Path("prompts.yaml"),
            Path(__file__).parent / "prompts.yaml",
        ]
        
        prompts_file = None
        for path in possible_paths:
            if path.exists():
                prompts_file = path
                break
        
        if prompts_file:
            try:
                with open(prompts_file, 'r', encoding='utf-8') as f:
                    self._prompts = yaml.safe_load(f) or {}
                logger.info(f"Loaded prompts from {prompts_file}")
            except Exception as e:
                logger.warning(f"Failed to load prompts from {prompts_file}: {e}")
                self._load_defaults()
        else:
            logger.info("No prompts.yaml found, using defaults")
            self._load_defaults()
    
    def _load_defaults(self) -> None:
        """Load default prompts."""
        self._prompts = {
            "SYSTEM_IDENTITY": "Sen gelişmiş bir PDF ve Belge Analiz Asistanısın. Soruları bağlamı kullanarak yanıtla.",
            "RAG_CONTEXT_TEMPLATE": "Bağlam: {context}\n\nTercihler: {preferences}\n\nSoru: {question}",
            "RESPONSE_CONCISE": "Kısa ve öz tut",
            "RESPONSE_DETAILED": "Kapsamlı açıklama yap",
            "NO_CONTEXT_ERROR": "Üzgünüm, bu konuda bilgi bulunmuyor.",
            "GREETING": "Merhaba! Size nasıl yardımcı olabilirim?",
            "DEFAULT_LANGUAGE": "tr",
            "DEFAULT_RETRIEVAL_K": 4,
            "SIMILARITY_THRESHOLD": 0.5,
        }
    
    def get(self, key: str, default: Optional[str] = None) -> str:
        """
        Get a prompt by key.
        
        Args:
            key: Prompt key
            default: Default value if key not found
            
        Returns:
            Prompt string
        """
        return self._prompts.get(key, default or "")
    
    def get_system_identity(self) -> str:
        """Get the system identity prompt."""
        return self.get("SYSTEM_IDENTITY", "")
    
    def get_rag_template(self) -> str:
        """Get the RAG context template."""
        return self.get("RAG_CONTEXT_TEMPLATE", "")
    
    def get_preference_prompt(self, preference: str) -> str:
        """Get prompt for a specific preference."""
        return self.get(f"RESPONSE_{preference.upper()}", "")
    
    def get_error_message(self, error_type: str) -> str:
        """Get error message."""
        return self.get(f"NO_CONTEXT_ERROR", "Bilgi bulunmuyor.")
    
    def get_greeting(self) -> str:
        """Get greeting message."""
        lang = self.get("DEFAULT_LANGUAGE", "tr")
        return self.get(f"GREETING", "Merhaba!") if lang == "tr" else self.get("GREETING_ENGLISH", "Hello!")
    
    def get_retrieval_k(self) -> int:
        """Get default retrieval k value."""
        return int(self.get("DEFAULT_RETRIEVAL_K", 4))
    
    def get_similarity_threshold(self) -> float:
        """Get similarity threshold."""
        return float(self.get("SIMILARITY_THRESHOLD", 0.5))
    
    def get_all(self) -> Dict[str, Any]:
        """Get all prompts."""
        return self._prompts.copy()
    
    def reload(self) -> None:
        """Reload prompts from file."""
        self._loaded = False
        self._load_prompts()


# Global instance
_prompt_loader: Optional[PromptLoader] = None


def get_prompt_loader() -> PromptLoader:
    """Get the global prompt loader instance."""
    global _prompt_loader
    if _prompt_loader is None:
        _prompt_loader = PromptLoader()
    return _prompt_loader


# Convenience functions
def get_system_identity() -> str:
    """Get system identity prompt."""
    return get_prompt_loader().get_system_identity()


def get_rag_template() -> str:
    """Get RAG context template."""
    return get_prompt_loader().get_rag_template()


def get_preference_prompt(preference: str) -> str:
    """Get preference-specific prompt."""
    return get_prompt_loader().get_preference_prompt(preference)


def get_error_message(error_type: str = "no_context") -> str:
    """Get error message."""
    return get_prompt_loader().get_error_message(error_type)
