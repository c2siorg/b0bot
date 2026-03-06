
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    huggingface_token: str
    huggingfacehub_api_token: str
    pinecone_api_key: str

    pinecone_index_name: str = "cybernews-index"
    pinecone_namespace: str = "c2si"
    pinecone_vector_dimension: int = 384

    llm_config_path: str = "config/llm_config.json"
    llm_temperature: float = 0.5

    max_news_context: int = 50 
    max_news_results: int = 10 

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()