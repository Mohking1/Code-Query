from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    host: str = "127.0.0.1"
    port: int = 8765
    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    rrf_k: int = 60
    vector_weight: float = 1.0
    bm25_weight: float = 0.8
    default_ignore_patterns: list[str] = [
        "**/node_modules/**",
        "**/.git/**",
        "**/dist/**",
        "**/build/**",
        "**/venv/**",
        "**/.venv/**",
        "**/__pycache__/**",
        "**/.codequery/**",
        "**/docs/**",
    ]


def get_settings() -> Settings:
    return Settings()
