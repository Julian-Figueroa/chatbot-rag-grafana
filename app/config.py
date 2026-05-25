from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str
    llm_model: str = "gpt-4o-mini"
    embedding_model: str = "text-embedding-3-small"
    chroma_persist_dir: str = "./chroma_db"
    chroma_collection_name: str = "grafana_docs"

    class Config:
        env_file = ".env"


settings = Settings()
