"""Narrative variation system.

Builds a deterministic per-user seed from birth details and uses it to
mildly shuffle the order of bullet points inside an archetype dict, so two
users mapped to the same archetype still get different prose seeds.
"""

from __future__ import annotations

import hashlib
import logging
from typing import Optional

from .models import BirthDetails

logger = logging.getLogger("past_life")


def get_narrative_variation_seed(birth_details: Optional[BirthDetails]) -> int:
    """Generate a unique variation seed from birth details."""
    if not birth_details:
        logger.debug("No birth details provided; variation seed = 0.")
        return 0

    try:
        date_parts = birth_details.date_of_birth.split('-')
        year = int(date_parts[0])
        month = int(date_parts[1])
        day = int(date_parts[2])

        hour = 0
        minute = 0
        if birth_details.time_of_birth:
            time_parts = birth_details.time_of_birth.split(':')
            hour = int(time_parts[0])
            minute = int(time_parts[1])

        place_hash = 0
        if birth_details.place_of_birth:
            place_hash = sum(ord(c) for c in birth_details.place_of_birth)

        composite_seed = (
            (year % 100) * 1000000 +
            month * 100000 +
            day * 10000 +
            hour * 1000 +
            minute * 10 +
            (place_hash % 10)
        )
        logger.debug(
            "Variation seed built: y=%d m=%d d=%d h=%d min=%d place_hash=%d → seed=%d",
            year, month, day, hour, minute, place_hash, composite_seed,
        )
        return composite_seed

    except (ValueError, IndexError) as exc:
        logger.warning(
            "Could not build numeric variation seed (%s); falling back to SHA-256.",
            exc,
        )
        seed_string = (
            f"{birth_details.date_of_birth}"
            f"{birth_details.time_of_birth or ''}"
            f"{birth_details.place_of_birth or ''}"
        )
        hash_val = int(hashlib.sha256(seed_string.encode()).hexdigest(), 16)
        logger.debug("Fallback seed (SHA-256): %d", hash_val)
        return hash_val


def apply_narrative_variations(
    base_archetype: dict,
    archetype_key: str,
    variation_seed: int,
) -> dict:
    """Apply subtle variations to the base archetype based on birth details."""
    varied = base_archetype.copy()
    flips: list[str] = []

    if (variation_seed & 0b0001):
        varied["core_nature"] = [
            varied["core_nature"][1],
            varied["core_nature"][0],
        ]
        flips.append("core_nature")
    if (variation_seed & 0b0010):
        varied["contribution"] = [
            varied["contribution"][1],
            varied["contribution"][0],
        ]
        flips.append("contribution")
    if (variation_seed & 0b0100):
        varied["unfinished_theme"] = [
            varied["unfinished_theme"][1],
            varied["unfinished_theme"][0],
        ]
        flips.append("unfinished_theme")
    if (variation_seed & 0b1000):
        varied["present_life_lesson"] = [
            varied["present_life_lesson"][1],
            varied["present_life_lesson"][0],
        ]
        flips.append("present_life_lesson")

    logger.debug(
        "Archetype '%s' variations applied: flipped=%s (seed=%d)",
        archetype_key, flips or "none", variation_seed,
    )
    return varied
