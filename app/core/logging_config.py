"""
Configuración centralizada de logging.
Escribe a stdout (docker logs) y a archivo (RotatingFileHandler).
"""
import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app.config import settings

LOG_FORMAT = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging() -> None:
    """Configura el logger raíz de la aplicación."""
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    root = logging.getLogger("app")
    root.setLevel(level)

    if root.handlers:
        return

    formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)

    # stdout para docker logs
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(level)
    stream_handler.setFormatter(formatter)
    root.addHandler(stream_handler)

    # archivo en volumen (Docker) o local
    log_path = Path(settings.log_file)
    if not log_path.is_absolute():
        log_path = Path(__file__).resolve().parent.parent.parent / log_path
    log_path.parent.mkdir(parents=True, exist_ok=True)
    file_handler = RotatingFileHandler(
        str(log_path),
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """Devuelve un logger hijo de app.{name}."""
    return logging.getLogger(f"app.{name}")
