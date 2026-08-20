from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Literal


class Settings(BaseSettings):
    """FREYJA configuration — env vars override defaults."""

    # App
    app_name: str = "freyja"
    debug: bool = False
    secret_key: str = "change-me-to-a-64-char-random-string"
    session_cookie_name: str = "freyja_session"
    session_max_age: int = 60 * 60 * 24 * 7  # 7 days

    # Database
    database_url: str = "sqlite+aiosqlite:///./freyja.db"

    # Redis (caching, rate limiting, session offload)
    redis_url: str = "redis://localhost:6379/0"

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    default_model: str = "phi4-mini:latest"

    # Stripe (billing)
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_price_basic: str = ""
    stripe_price_premium: str = ""

    # ElevenLabs (voice/TTS)
    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = ""

    # Age verification
    age_verification_required: bool = True
    age_verification_provider: Literal["manual", "jumio", "yoti"] = "manual"

    # Tiers
    default_tier: Literal["basic", "premium"] = "basic"
    basic_history_limit: int = 6
    premium_history_limit: int = 500
    basic_models: list[str] = ["phi4-mini:latest"]
    premium_models: list[str] = ["phi4-mini:latest", "qwen2.5-coder:14b"]

    # Persona
    system_persona: str = (
        "You are a warm, attentive companion. Stay in character. "
        "Be supportive, curious, and emotionally present."
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()
