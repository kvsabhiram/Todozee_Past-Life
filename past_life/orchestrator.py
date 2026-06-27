"""One-time-only orchestrator: generate-or-fetch a past-life insight.

This is the CLI-side counterpart of the ``POST /insight`` endpoint in
:mod:`past_life.api`. The HTTP endpoint does its own orchestration for
historical reasons; this function is kept so that ``--cli`` mode keeps
working.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Optional

from .archetypes import ARCHETYPES
from .gemma import call_gemma_local
from .models import InsightRecord, UserProfile
from .payload import build_payload
from .prompts import pick_opening
from .selection import select_archetype
from .storage import load_insight, save_insight

logger = logging.getLogger("past_life")


ONE_TIME_MESSAGE = (
    "This insight is available only once as part of a lifetime reflection."
)


def get_past_life_insight(
    profile: UserProfile,
    hf_token: Optional[str] = None,
) -> dict:
    """Public API. Returns dict with is_new, insight_text, etc."""
    logger.info(
        "Insight request: user_id=%s name='%s' has_birth=%s hint=%s",
        profile.user_id, profile.name,
        bool(profile.birth_details), profile.archetype_hint or "-",
    )

    existing = load_insight(profile.user_id)
    if existing and existing.past_life_unlocked:
        logger.info(
            "↩ Insight already unlocked for user_id=%s — returning cached copy.",
            profile.user_id,
        )
        return {
            "is_new": False,
            "insight_text": existing.insight_text,
            "archetypal_role": existing.archetypal_role,
            "generated_at": existing.generated_at,
            "message": ONE_TIME_MESSAGE,
        }

    archetype_key = select_archetype(profile)

    opening_line = pick_opening(profile.user_id)
    payload = build_payload(archetype_key, opening_line=opening_line)
    t0 = time.time()
    insight_text = call_gemma_local(payload, hf_token=hf_token)
    logger.info(
        "Generated fresh insight for user_id=%s in %.2fs.",
        profile.user_id, time.time() - t0,
    )

    now = datetime.now(timezone.utc).isoformat()
    record = InsightRecord(
        user_id=profile.user_id,
        generated_at=now,
        archetypal_role=ARCHETYPES[archetype_key]["archetypal_role"],
        insight_text=insight_text,
    )
    save_insight(record)

    return {
        "is_new": True,
        "insight_text": insight_text,
        "archetypal_role": record.archetypal_role,
        "generated_at": now,
        "message": None,
    }
