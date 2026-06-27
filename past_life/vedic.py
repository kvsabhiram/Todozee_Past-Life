"""Vedic (sidereal) astrology — Nakshatra, Pada, Rashi via Swiss Ephemeris.

This is the "second library" layer that engages only when the user gives
ALL four inputs (name + date_of_birth + time_of_birth + place_of_birth).
With less than full inputs, the Vedic data would be too inaccurate to be
useful (Moon moves ~13° per day — without a real birth time + place, the
Nakshatra is wrong).

Implementation uses :mod:`pyswisseph` (the canonical Swiss Ephemeris
Python binding — already installed as a kerykeion dependency) for the
Lahiri ayanamsa, and kerykeion for the underlying tropical longitudes.
"""

from __future__ import annotations

import logging
from typing import Optional

try:
    import swisseph as swe
    SWE_AVAILABLE = True
except ImportError:                          # pragma: no cover
    SWE_AVAILABLE = False

try:
    from kerykeion import AstrologicalSubject
    KERYKEION_AVAILABLE = True
except ImportError:                          # pragma: no cover
    KERYKEION_AVAILABLE = False

logger = logging.getLogger("past_life")


# The 27 lunar mansions (Nakshatras) of Vedic astrology.
# Each spans 13°20' (= 360°/27) of the sidereal zodiac.
NAKSHATRAS: list[str] = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni",
    "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha",
    "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha",
    "Shravana", "Dhanishtha", "Shatabhisha", "Purva Bhadrapada",
    "Uttara Bhadrapada", "Revati",
]

# Symbolic essence of each Nakshatra (short phrase the model can use).
NAKSHATRA_QUALITIES: dict[str, str] = {
    "Ashwini": "swift healer of beginnings",
    "Bharani": "keeper of life's thresholds",
    "Krittika": "purifying flame",
    "Rohini": "blossoming abundance",
    "Mrigashira": "gentle seeker of the unseen",
    "Ardra": "tear of transformation",
    "Punarvasu": "returning home to oneself",
    "Pushya": "nourisher of the soul",
    "Ashlesha": "intuitive coil of wisdom",
    "Magha": "ancestral throne",
    "Purva Phalguni": "joy of creative play",
    "Uttara Phalguni": "steady-hearted giver",
    "Hasta": "skillful hand of craft",
    "Chitra": "weaver of bright designs",
    "Swati": "free-moving breath",
    "Vishakha": "rooted in purpose",
    "Anuradha": "devoted friend of the soul",
    "Jyeshtha": "elder wisdom-bearer",
    "Mula": "root searcher of truth",
    "Purva Ashadha": "early-rising victor",
    "Uttara Ashadha": "lasting victory of patience",
    "Shravana": "deep listener",
    "Dhanishtha": "rhythm of the drum",
    "Shatabhisha": "hundred-healed mystic",
    "Purva Bhadrapada": "fire of inner transformation",
    "Uttara Bhadrapada": "calm depths of compassion",
    "Revati": "wealth of the inner ocean",
}

# 12 Vedic zodiac signs (Rashis) — Sanskrit names.
RASHIS: list[str] = [
    "Mesha", "Vrishabha", "Mithuna", "Karka", "Simha", "Kanya",
    "Tula", "Vrishchika", "Dhanu", "Makara", "Kumbha", "Meena",
]

RASHI_WESTERN: dict[str, str] = {
    "Mesha": "Aries",        "Vrishabha": "Taurus",  "Mithuna": "Gemini",
    "Karka": "Cancer",       "Simha": "Leo",         "Kanya": "Virgo",
    "Tula": "Libra",         "Vrishchika": "Scorpio","Dhanu": "Sagittarius",
    "Makara": "Capricorn",   "Kumbha": "Aquarius",   "Meena": "Pisces",
}


def compute_vedic_facts(
    name: str,
    date_of_birth: str,           # YYYY-MM-DD
    time_of_birth: str,           # HH:MM (24-hour, REQUIRED for Vedic)
    place_of_birth: str,          # used as a label, lat/lng/tz come from caller
    lat: float,
    lng: float,
    tz_str: str,
    utc_offset_hours: float,
) -> Optional[dict]:
    """Return rich Vedic chart data — only meaningful with real time + place.

    Returns ``None`` if a required library is missing or the calculation
    fails. The caller is expected to gate this on ALL four user inputs
    being present; this function trusts that contract.
    """
    if not (SWE_AVAILABLE and KERYKEION_AVAILABLE):
        logger.warning(
            "Vedic computation skipped — swisseph or kerykeion not available."
        )
        return None

    try:
        year, month, day = (int(p) for p in date_of_birth.split("-"))
        hour, minute = (int(p) for p in time_of_birth.split(":"))
    except (ValueError, AttributeError) as exc:
        logger.error("Vedic: bad date/time '%s'/'%s': %s",
                     date_of_birth, time_of_birth, exc)
        return None

    try:
        subject = AstrologicalSubject(
            name=name or "User",
            year=year, month=month, day=day,
            hour=hour, minute=minute,
            city=place_of_birth.split(",")[0].strip() or "Unknown",
            nation="IN",
            lat=lat, lng=lng, tz_str=tz_str,
            online=False,
        )
    except Exception as exc:                                # noqa: BLE001
        logger.warning("Vedic: kerykeion failed: %s", exc)
        return None

    ut_hour = hour + (minute / 60.0) - utc_offset_hours
    jd_ut = swe.julday(year, month, day, ut_hour)
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    ayanamsa = swe.get_ayanamsa(jd_ut)

    moon_sid = (subject.moon.abs_pos - ayanamsa) % 360
    sun_sid = (subject.sun.abs_pos - ayanamsa) % 360
    asc_sid = (subject.first_house.abs_pos - ayanamsa) % 360

    nak_span = 360.0 / 27
    nak_idx = int(moon_sid / nak_span)
    nak_remainder = moon_sid - (nak_idx * nak_span)
    pada = int(nak_remainder / (nak_span / 4)) + 1

    nakshatra_name = NAKSHATRAS[nak_idx]
    rashi_moon = RASHIS[int(moon_sid / 30)]
    rashi_sun = RASHIS[int(sun_sid / 30)]
    lagna = RASHIS[int(asc_sid / 30)]

    facts = {
        "ayanamsa": round(ayanamsa, 4),
        "nakshatra": nakshatra_name,
        "nakshatra_quality": NAKSHATRA_QUALITIES.get(nakshatra_name, ""),
        "pada": pada,
        "moon_rashi": rashi_moon,
        "moon_rashi_western": RASHI_WESTERN.get(rashi_moon, rashi_moon),
        "sun_rashi": rashi_sun,
        "sun_rashi_western": RASHI_WESTERN.get(rashi_sun, rashi_sun),
        "lagna": lagna,
        "lagna_western": RASHI_WESTERN.get(lagna, lagna),
        "system": "Lahiri sidereal",
    }
    logger.info(
        "🕉 Vedic facts: nakshatra=%s pada=%d moon_rashi=%s sun_rashi=%s lagna=%s",
        nakshatra_name, pada, rashi_moon, rashi_sun, lagna,
    )
    return facts
