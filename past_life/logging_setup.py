"""Logging setup for the Past Life service."""

from __future__ import annotations

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from typing import Optional

LOG_FORMAT = (
    "%(asctime)s | %(levelname)-8s | %(name)s | "
    "%(filename)s:%(lineno)d | %(funcName)s | %(message)s"
)
CONSOLE_FORMAT = (
    "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
)
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def configure_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    max_bytes: int = 10 * 1024 * 1024,   # 10 MB per rotation
    backup_count: int = 5,
) -> logging.Logger:
    """Configure the root 'past_life' logger.

    • Console handler (human-friendly format).
    • Optional rotating file handler (detailed format).
    • Tames noisy third-party libs (transformers, urllib3, uvicorn.access).
    """
    level_value = getattr(logging, level.upper(), logging.INFO)

    root = logging.getLogger("past_life")
    root.setLevel(level_value)
    root.handlers.clear()
    root.propagate = False

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level_value)
    console_handler.setFormatter(
        logging.Formatter(CONSOLE_FORMAT, datefmt=DATE_FORMAT)
    )
    root.addHandler(console_handler)

    if log_file:
        try:
            os.makedirs(os.path.dirname(os.path.abspath(log_file)) or ".",
                        exist_ok=True)
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding="utf-8",
            )
            file_handler.setLevel(level_value)
            file_handler.setFormatter(
                logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
            )
            root.addHandler(file_handler)
            root.info("File logging enabled → %s (max=%d MB, keep=%d)",
                      log_file, max_bytes // (1024 * 1024), backup_count)
        except Exception as exc:                             # noqa: BLE001
            root.error("Could not open log file %s: %s", log_file, exc)

    logging.getLogger("transformers").setLevel(logging.WARNING)
    logging.getLogger("transformers.modeling_utils").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("huggingface_hub").setLevel(logging.WARNING)
    logging.getLogger("filelock").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)

    root.debug("Logger configured at level=%s", level.upper())
    return root


logger = configure_logging(level=os.environ.get("LOG_LEVEL", "INFO"),
                           log_file=os.environ.get("LOG_FILE"))
