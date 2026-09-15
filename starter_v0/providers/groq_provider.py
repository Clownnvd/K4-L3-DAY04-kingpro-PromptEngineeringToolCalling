from __future__ import annotations
import os
from providers.openai_provider import OpenAIProvider

class GroqProvider(OpenAIProvider):
    """Groq OpenAI-compatible Chat Completions with local tool calling."""
    def __init__(self)->None:
        super().__init__(
            api_key_env='GROQ_API_KEY',
            base_url=os.getenv('GROQ_BASE_URL','https://api.groq.com/openai/v1'),
            default_model=os.getenv('GROQ_MODEL','qwen/qwen3.8-27b'),
            max_completion_tokens=int(os.getenv('GROQ_MAX_COMPLETION_TOKENS','128')),
            max_retries=int(os.getenv('GROQ_MAX_RETRIES','6')),
        )
