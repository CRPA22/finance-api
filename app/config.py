from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parent.parent / ".env", 
        env_file_encoding="utf-8"
        )

    openai_api_key: str
    openai_model: str
    database_url: str
    chat_database_url: str
    log_level: str = "INFO"
    log_file: str = "logs/app.log"  # Local: relativo al proyecto. Docker: LOG_FILE=/app/logs/app.log
    cors_origins: str = "http://localhost:5173,http://localhost:3000"  # Separados por coma

settings = Settings()