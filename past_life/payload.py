"""Builds the safe JSON payload sent to the language model.

The payload carries ONLY symbolic data the model is allowed to write about:
the archetype, optional astrology facts, the chosen opening line, the
premium archetype (Healer/Scholar/…), and the per-user theme.
"""

from __future__ import annotations

import logging
from typing import Optional

from .archetypes import ARCHETYPES
from .models import PastLifePayload

logger = logging.getLogger("past_life")


def build_payload(
    archetype_key: str,
    astro_facts: Optional[dict] = None,
    opening_line: Optional[str] = None,
    premium_archetype: Optional[dict] = None,
    theme: Optional[str] = None,
) -> PastLifePayload:
    """Build a PastLifePayload for the given archetype.

    Parameters
    ----------
    archetype_key
        One of the keys in :data:`past_life.archetypes.ARCHETYPES` — the
        internal symbolic archetype used by the deterministic renderer.
    astro_facts
        Optional dict from :func:`past_life.astrology.compute_astro_facts`.
    opening_line
        Optional first sentence chosen via :func:`past_life.prompts.pick_opening`.
        When provided, the model is instructed to use it verbatim as the
        first sentence of the ``🔮 Your Possible Past Life`` section.
    premium_archetype
        Optional dict from :func:`past_life.premium_archetypes.pick_premium_archetype`.
        Drives the user-facing ``🏺 Past Life Archetype`` block — one of
        12 rotating roles (Healer, Scholar, Teacher, Artist, Explorer,
        Merchant, Guardian, Leader, Mystic, Storyteller, Builder, Navigator).
    theme
        Optional theme string from :func:`past_life.premium_archetypes.pick_theme`
        (e.g. ``"courage"``, ``"wisdom"``, ``"forgiveness"`` …). The prompt
        leans on this to vary the lesson / message focus across users.
    """
    if archetype_key not in ARCHETYPES:
        logger.error("Unknown archetype key requested: '%s'", archetype_key)
        raise ValueError(f"Unknown archetype: {archetype_key}")
    data = dict(ARCHETYPES[archetype_key])
    if astro_facts:
        data["astrology"] = astro_facts
    if opening_line:
        data["opening_line"] = opening_line
    if premium_archetype:
        data["premium_archetype"] = premium_archetype
    if theme:
        data["theme"] = theme
    payload = PastLifePayload(past_life_data=data)
    logger.debug(
        "Built payload for archetype '%s' (astro=%s, opening=%s, "
        "premium=%s, theme=%s).",
        archetype_key, bool(astro_facts), bool(opening_line),
        premium_archetype.get("name") if premium_archetype else None,
        theme,
    )
    return payload
