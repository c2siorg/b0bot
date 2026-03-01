"""
Centralised, validated application configuration using Pydantic Settings.

Every value can be overridden via environment variables or the ``.env`` file.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All env-vars consumed by the application."""

    # ── Secrets ───────────────────────────────────────────────────────────────
    huggingface_token: str
    pinecone_api_key: str

    # ── Pinecone ──────────────────────────────────────────────────────────────
    pinecone_index_name: str = "cybernews-index"
    pinecone_namespace: str = "c2si"
    pinecone_vector_dimension: int = 384

    # ── LLM ───────────────────────────────────────────────────────────────────
    llm_config_path: str = "config/llm_config.json"
    llm_temperature: float = 0.5

    # ── News defaults ─────────────────────────────────────────────────────────
    max_news_context: int = 50       # max articles fed to the LLM
    max_news_results: int = 10       # max articles returned to client

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    """Singleton accessor – parsed once, cached forever."""
    return Settings()