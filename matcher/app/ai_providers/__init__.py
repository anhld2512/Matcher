"""__init__.py for ai_providers package"""
from .base import AIProvider
from .gemini import GeminiProvider
from .chatgpt import ChatGPTProvider
from .deepseek import DeepSeekProvider
from .huggingface import HuggingFaceProvider
from typing import Dict, Any


def get_ai_provider(provider: str, config: Dict[str, Any]) -> AIProvider:
    """
    Factory function to get AI provider instance.

    Args:
        provider: Provider name (gemini, chatgpt, deepseek, huggingface)
        config: Configuration dictionary with provider-specific settings

    Returns:
        AIProvider instance

    Raises:
        ValueError: If provider is unknown
    """
    providers = {
        "gemini": GeminiProvider,
        "chatgpt": ChatGPTProvider,
        "deepseek": DeepSeekProvider,
        "huggingface": HuggingFaceProvider
    }

    provider_class = providers.get(provider.lower())
    if not provider_class:
        raise ValueError(f"Unknown provider: {provider}")

    return provider_class(config)


def load_active_provider_from_db():
    """
    Load active AI provider from database.

    Returns:
        AIProvider instance or None if not configured
    """
    from ..database import SessionLocal, AISettings

    db = SessionLocal()
    try:
        settings = db.query(AISettings).filter(AISettings.is_active == 1).first()
        if not settings:
            # Return default Gemini provider (cloud-based, fast)
            return GeminiProvider({
                "api_key": "",  # User must configure
                "model": "gemini-pro"
            })

        config = {
            "model": settings.model_name
        }

        if settings.provider == "ollama":
            config["host"] = settings.host or "localhost"
            config["port"] = settings.port or 11434
        else:
            config["api_key"] = settings.api_key or ""

        return get_ai_provider(settings.provider, config)
    finally:
        db.close()


__all__ = [
    'AIProvider',
    'GeminiProvider',
    'ChatGPTProvider',
    'DeepSeekProvider',
    'HuggingFaceProvider',
    'get_ai_provider',
    'load_active_provider_from_db'
]
