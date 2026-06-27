"""Internal data models (dataclasses).

These are the in-memory structures the rest of the package passes around.
Pydantic request/response models for the HTTP API live in :mod:`past_life.api`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class BirthDetails:
    """Birth information used for archetype selection and variation."""
    date_of_birth: str                           # YYYY-MM-DD (REQUIRED)
    time_of_birth: Optional[str] = None          # HH:MM 24-hr (OPTIONAL)
    place_of_birth: Optional[str] = None         # City, Country (OPTIONAL)


@dataclass
class UserProfile:
    """Minimal profile used to deterministically select an archetype."""
    user_id: str
    name: str
    birth_details: Optional[BirthDetails] = None
    archetype_hint: Optional[str] = None


@dataclass
class PastLifePayload:
    """Exact JSON structure sent to the model — contains ONLY
    symbolic archetypal meanings, never raw astrology."""
    context: str = "one-time belief-based past life insight"
    language: str = "english"
    tone: str = "calm, deep, reassuring"
    content_type: str = "one_time_past_life"
    safety: dict = field(default_factory=lambda: {
        "no_prediction": True,
        "no_fear": True,
        "no_certainty": True,
        "no_historical_claims": True,
    })
    past_life_data: dict = field(default_factory=dict)


@dataclass
class InsightRecord:
    """Permanent storage record written after a successful generation."""
    user_id: str
    generated_at: str
    archetypal_role: str
    insight_text: str
    past_life_unlocked: bool = True
