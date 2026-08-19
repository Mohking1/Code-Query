from backend.config import get_settings


def test_settings_defaults():
    settings = get_settings()
    assert settings.port == 8765
    assert settings.host == "127.0.0.1"
    assert settings.embedding_model_name == "sentence-transformers/all-MiniLM-L6-v2"
    assert "**/node_modules/**" in settings.default_ignore_patterns
