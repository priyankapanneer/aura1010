import logging

from app.core.config import settings
from app.integrations.llm.base import LLMProvider
from app.integrations.llm.gemini import GeminiProvider
from app.integrations.llm.mock import MockLLMProvider

logger = logging.getLogger(__name__)


def get_llm_provider() -> LLMProvider:
    provider_name = settings.LLM_PROVIDER.lower().strip()

    if provider_name == "gemini" and settings.GEMINI_API_KEY:
        logger.info("Using Google Gemini LLM Provider (%s)", settings.LLM_MODEL)
        return GeminiProvider(api_key=settings.GEMINI_API_KEY, model_name=settings.LLM_MODEL)

    # Fallback to Mock provider
    logger.info("Using Deterministic Mock LLM Provider (Demo/Testing Mode)")
    return MockLLMProvider()
