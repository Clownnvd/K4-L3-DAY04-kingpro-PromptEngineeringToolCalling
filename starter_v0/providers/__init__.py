from providers.openai_provider import OpenAIProvider
from providers.openrouter_provider import OpenRouterProvider
from providers.anthropic_provider import AnthropicProvider
from providers.gemini_provider import GeminiProvider
from providers.groq_provider import GroqProvider
from providers.offline_provider import OfflineRuleProvider


def make_provider(name: str):
    if name == "openai":
        return OpenAIProvider(
            default_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            max_completion_tokens=int(os.getenv("OPENAI_MAX_COMPLETION_TOKENS", "300")),
            max_retries=int(os.getenv("OPENAI_MAX_RETRIES", "4")),
        )
    if name == "openrouter":
        return OpenRouterProvider()
    if name == "anthropic":
        return AnthropicProvider()
    if name == "gemini":
        return GeminiProvider()
    if name == "groq":
        return GroqProvider()
    if name == "offline":
        return OfflineRuleProvider()
    raise ValueError(f"Unknown provider: {name}")
import os
