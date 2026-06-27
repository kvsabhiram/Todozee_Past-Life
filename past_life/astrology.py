"""Real astrology (kerykeion) — name + DOB minimum, richer with full inputs.

Two-tier behaviour:

* **Basic mode** — only name + date_of_birth required. Sun sign is exact;
  Moon sign and Ascendant are approximations (we default time → noon and
  place → Hyderabad). We always return Sun-driven archetype + a
  per-user-seeded subset of mystical vocabulary from :mod:`past_life.vocab`.

* **Rich mode** — engaged automatically when the user provides ALL four
  inputs (name + date_of_birth + time_of_birth + place_of_birth). On top
  of the basic facts we also compute true Vedic / sidereal data via
  :mod:`past_life.vedic` (Nakshatra, Pada, Rashi, Lagna). The prompt is
  then allowed to use stronger Vedic-flavoured vocabulary.
"""

from __future__ import annotations

import logging
from typing import Optional

try:
    from kerykeion import AstrologicalSubject
    KERYKEION_AVAILABLE = True
except ImportError:                          # pragma: no cover
    KERYKEION_AVAILABLE = False

from .vedic import compute_vedic_facts
from .vocab import MYSTIC_VOCAB, select_mystic_words

logger = logging.getLogger("past_life")


SIGN_ABBR_TO_FULL = {
    "Ari": "Aries", "Tau": "Taurus", "Gem": "Gemini", "Can": "Cancer",
    "Leo": "Leo", "Vir": "Virgo", "Lib": "Libra", "Sco": "Scorpio",
    "Sag": "Sagittarius", "Cap": "Capricorn", "Aqu": "Aquarius",
    "Pis": "Pisces",
}

# Each sun sign maps to one archetype key. The mystic-words pool itself
# lives in :mod:`past_life.vocab` (100+ words per sign) and the per-user
# subset is selected by :func:`past_life.vocab.select_mystic_words`.
SUN_SIGN_ARCHETYPES = {
    "Ari": {"archetype_key": "lone_flame"},
    "Tau": {"archetype_key": "earth_keeper"},
    "Gem": {"archetype_key": "sacred_storyteller"},
    "Can": {"archetype_key": "gentle_healer"},
    "Leo": {"archetype_key": "free_spirit"},
    "Vir": {"archetype_key": "patient_scholar"},
    "Lib": {"archetype_key": "bridge_builder"},
    "Sco": {"archetype_key": "silent_witness"},
    "Sag": {"archetype_key": "wandering_seeker"},
    "Cap": {"archetype_key": "steadfast_keeper"},
    "Aqu": {"archetype_key": "star_dreamer"},
    "Pis": {"archetype_key": "dream_weaver"},
}

# Sensible default location used when the user does not give a place of birth.
DEFAULT_PLACE = {
    "city": "Hyderabad",
    "nation": "IN",
    "lat": 17.385,
    "lng": 78.486,
    "tz_str": "Asia/Kolkata",
}
DEFAULT_TIME = (12, 0)   # noon, when the user does not give a birth time


def compute_astro_facts(
    name: str,
    date_of_birth: str,
    time_of_birth: Optional[str] = None,
    place_of_birth: Optional[str] = None,
    user_seed: Optional[str] = None,
) -> Optional[dict]:
    """Compute Sun / Moon / Ascendant from name + date of birth.

    `time_of_birth` and `place_of_birth` are optional. When omitted we use
    noon and a default city — the Sun sign is still exact, the Moon sign
    and Ascendant become best-effort approximations.

    When ALL of name + date + time + place are provided ("rich mode"), we
    additionally compute Vedic / sidereal facts (Nakshatra, Pada, Rashi,
    Lagna) via :func:`past_life.vedic.compute_vedic_facts`.

    ``user_seed`` (any string — usually the user_id) seeds the per-user
    selection of mystic vocabulary. When omitted, ``name + date_of_birth``
    is used as the seed.

    Returns ``None`` if kerykeion is not installed or the calculation fails.
    """
    if not KERYKEION_AVAILABLE:
        logger.warning(
            "kerykeion not installed — skipping real astrology. "
            "Install with: pip install kerykeion"
        )
        return None
    try:
        year, month, day = (int(p) for p in date_of_birth.split("-"))
    except (ValueError, AttributeError) as exc:
        logger.error("Bad date_of_birth '%s': %s", date_of_birth, exc)
        return None

    hour, minute = DEFAULT_TIME
    used_default_time = True
    if time_of_birth:
        try:
            hour, minute = (int(p) for p in time_of_birth.split(":"))
            used_default_time = False
        except ValueError:
            logger.warning(
                "Bad time_of_birth '%s' — defaulting to noon.", time_of_birth,
            )

    city = DEFAULT_PLACE["city"]
    if place_of_birth:
        city = place_of_birth.split(",")[0].strip() or city

    try:
        subject = AstrologicalSubject(
            name=name or "User",
            year=year, month=month, day=day,
            hour=hour, minute=minute,
            city=city, nation=DEFAULT_PLACE["nation"],
            lat=DEFAULT_PLACE["lat"], lng=DEFAULT_PLACE["lng"],
            tz_str=DEFAULT_PLACE["tz_str"],
            online=False,
        )
    except Exception as exc:                                # noqa: BLE001
        logger.warning("kerykeion failed: %s", exc)
        return None

    sun_abbr = subject.sun.sign
    moon_abbr = subject.moon.sign
    asc_abbr = subject.first_house.sign

    # Per-user palette of mystical words drawn from the 100+-word pool
    # for this sun sign. The pool itself lives in past_life.vocab.
    seed = user_seed or f"{name}{date_of_birth}"
    suggested_words = select_mystic_words(sun_abbr, seed=seed, count=25)
    pool_size = len(MYSTIC_VOCAB.get(sun_abbr, []))

    facts = {
        "sun_sign": SIGN_ABBR_TO_FULL.get(sun_abbr, sun_abbr),
        "moon_sign": SIGN_ABBR_TO_FULL.get(moon_abbr, moon_abbr),
        "ascendant_sign": SIGN_ABBR_TO_FULL.get(asc_abbr, asc_abbr),
        "element": subject.sun.element,
        "modality": subject.sun.quality,
        "suggested_words": suggested_words,
        "used_default_time": used_default_time,
        "used_default_place": not place_of_birth,
    }

    # ── Rich mode: bring in real Vedic data when ALL 4 inputs given ──
    if time_of_birth and place_of_birth:
        vedic = compute_vedic_facts(
            name=name,
            date_of_birth=date_of_birth,
            time_of_birth=time_of_birth,
            place_of_birth=place_of_birth,
            lat=DEFAULT_PLACE["lat"],
            lng=DEFAULT_PLACE["lng"],
            tz_str=DEFAULT_PLACE["tz_str"],
            utc_offset_hours=5.5,    # India Standard Time default
        )
        if vedic:
            facts["vedic"] = vedic
            facts["rich_mode"] = True
        else:
            facts["rich_mode"] = False
    else:
        facts["rich_mode"] = False

    logger.info(
        "🔮 Astro facts: sun=%s moon=%s asc=%s element=%s "
        "suggested_words=%d/%d rich=%s",
        facts["sun_sign"], facts["moon_sign"], facts["ascendant_sign"],
        facts["element"], len(suggested_words), pool_size, facts["rich_mode"],
    )
    return facts


def archetype_from_astro(astro_facts: Optional[dict]) -> Optional[str]:
    """Pick an archetype key from the Sun sign. Returns None if no Sun info."""
    if not astro_facts:
        return None
    sun_full = astro_facts.get("sun_sign", "")
    abbr_by_full = {v: k for k, v in SIGN_ABBR_TO_FULL.items()}
    abbr = abbr_by_full.get(sun_full, sun_full[:3].title())
    entry = SUN_SIGN_ARCHETYPES.get(abbr)
    if entry is None:
        logger.warning("No archetype mapping for sun sign '%s'.", sun_full)
        return None
    logger.info(
        "Sun sign '%s' → archetype '%s'.", sun_full, entry["archetype_key"],
    )
    return entry["archetype_key"]
