"""File-based storage and interaction logging.

* Each user's insight is saved as a single JSON file under
  ``past_life_storage/<sha16-of-user-id>.json``.
* Every request input and its output are appended to
  ``past_life_storage/interactions.jsonl`` (one JSON record per line).
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Optional

from .models import InsightRecord

logger = logging.getLogger("past_life")


STORAGE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "past_life_storage",
)

INTERACTIONS_LOG = os.path.join(STORAGE_DIR, "interactions.jsonl")


def log_interaction(
    *,
    endpoint: str,
    user_id: str,
    request_input: dict,
    output: dict,
) -> None:
    """Append one request input + its output to the interactions log.

    Never raises — logging must not break the API response.
    """
    try:
        os.makedirs(STORAGE_DIR, exist_ok=True)
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "endpoint": endpoint,
            "user_id": user_id,
            "input": request_input,
            "output": output,
        }
        with open(INTERACTIONS_LOG, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
        logger.info(
            "📝 Interaction logged: endpoint=%s user_id=%s source=%s → %s",
            endpoint, user_id, output.get("source", "?"), INTERACTIONS_LOG,
        )
    except Exception as exc:                                   # noqa: BLE001
        logger.error("Could not write interaction log: %s", exc, exc_info=True)


def _storage_path(user_id: str) -> str:
    safe = hashlib.sha256(user_id.encode()).hexdigest()[:16]
    path = os.path.join(STORAGE_DIR, f"{safe}.json")
    logger.debug("Computed storage path for user_id='%s': %s", user_id, path)
    return path


def save_insight(record: InsightRecord) -> str:
    """Persist an InsightRecord to disk."""
    try:
        os.makedirs(STORAGE_DIR, exist_ok=True)
        path = _storage_path(record.user_id)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(asdict(record), fh, indent=2, ensure_ascii=False)
        logger.info(
            "✅ Insight saved: user_id=%s archetype='%s' path=%s size=%d chars",
            record.user_id, record.archetypal_role, path,
            len(record.insight_text),
        )
        return path
    except OSError as exc:
        logger.error(
            "Failed to save insight for user_id=%s: %s", record.user_id, exc,
        )
        raise


def load_insight(user_id: str) -> Optional[InsightRecord]:
    """Load a cached insight, if any exists."""
    path = _storage_path(user_id)
    if not os.path.exists(path):
        logger.debug("No cached insight for user_id=%s (path=%s)", user_id, path)
        return None
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        record = InsightRecord(**data)
        logger.info(
            "📂 Cached insight loaded: user_id=%s archetype='%s' generated_at=%s",
            record.user_id, record.archetypal_role, record.generated_at,
        )
        return record
    except (OSError, json.JSONDecodeError, TypeError) as exc:
        logger.error(
            "Corrupt or unreadable insight file at %s for user_id=%s: %s",
            path, user_id, exc,
        )
        return None
