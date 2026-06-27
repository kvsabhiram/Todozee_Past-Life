"""Archetype selection (deterministic) and interactive CLI prompt."""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime

from .archetypes import ARCHETYPES
from .models import BirthDetails, UserProfile

logger = logging.getLogger("past_life")


def prompt_birth_details() -> tuple[str, BirthDetails]:
    """Interactive prompt to collect birth details (CLI mode)."""
    logger.debug("Prompting user for birth details (CLI mode).")
    print("\n" + "═" * 60)
    print("  🌙  PERSONAL DETAILS FOR PAST LIFE INSIGHT")
    print("═" * 60)
    print("\nPlease provide your information:")
    print("(This data is used ONLY to select your archetype)")
    print("(It is NOT stored or sent anywhere)\n")

    print("─" * 60)
    name = input("Full Name (REQUIRED): ").strip()
    while not name:
        print("  ✗ Name cannot be empty\n")
        name = input("Full Name (REQUIRED): ").strip()

    print()
    while True:
        dob = input(
            "Date of Birth - REQUIRED (YYYY-MM-DD, e.g., 1990-05-15): "
        ).strip()
        try:
            datetime.strptime(dob, "%Y-%m-%d")
            break
        except ValueError:
            print("  ✗ Invalid format. Please use YYYY-MM-DD (e.g., 1990-05-15)\n")

    print("\n" + "─" * 60)
    print("Optional Information (press Enter to skip):")
    print("─" * 60)
    tob = None
    tob_input = input(
        "Time of Birth - Optional (HH:MM in 24-hour, e.g., 14:30): "
    ).strip()
    if tob_input:
        while True:
            try:
                datetime.strptime(tob_input, "%H:%M")
                tob = tob_input
                break
            except ValueError:
                print("  ✗ Invalid format. Use HH:MM (e.g., 14:30) or Enter to skip\n")
                tob_input = input("Time of Birth - Optional (HH:MM): ").strip()
                if not tob_input:
                    break

    place = input(
        "Place of Birth - Optional (City, Country, e.g., Mumbai, India): "
    ).strip() or None

    print("\n" + "═" * 60)
    print("  ✓  Details collected")
    print("═" * 60 + "\n")

    logger.info(
        "CLI details collected: name='%s' dob=%s tob=%s place=%s",
        name, dob, tob or "-", place or "-",
    )
    return name, BirthDetails(
        date_of_birth=dob,
        time_of_birth=tob,
        place_of_birth=place,
    )


def select_archetype(profile: UserProfile) -> str:
    """Return an archetype key based on birth date (deterministic)."""
    keys = sorted(ARCHETYPES.keys())

    if profile.archetype_hint and profile.archetype_hint in ARCHETYPES:
        logger.info(
            "Archetype forced via hint for user_id=%s → '%s'",
            profile.user_id, profile.archetype_hint,
        )
        return profile.archetype_hint

    if profile.birth_details and profile.birth_details.date_of_birth:
        try:
            date_parts = profile.birth_details.date_of_birth.split('-')
            year = int(date_parts[0])
            month = int(date_parts[1])
            day = int(date_parts[2])

            seed_components = [
                str(year),
                str(month),
                str(day),
                profile.birth_details.time_of_birth or "",
                profile.birth_details.place_of_birth or "",
                profile.name,
                profile.user_id,
            ]
            seed_str = "".join(seed_components)
            seed_hash = int(hashlib.sha256(seed_str.encode()).hexdigest(), 16)
            chosen = keys[seed_hash % len(keys)]
            logger.info(
                "Archetype chosen from birth details for user_id=%s → '%s' "
                "(hash_index=%d/%d)",
                profile.user_id, chosen, seed_hash % len(keys), len(keys),
            )
            return chosen
        except (ValueError, IndexError) as e:
            logger.warning(
                "Failed to parse birth date '%s' for user_id=%s (%s). "
                "Falling back to user_id hash.",
                profile.birth_details.date_of_birth, profile.user_id, e,
            )

    idx = int(hashlib.sha256(profile.user_id.encode()).hexdigest(), 16) % len(keys)
    chosen = keys[idx]
    logger.info(
        "Archetype chosen from user_id hash for user_id=%s → '%s' (idx=%d/%d)",
        profile.user_id, chosen, idx, len(keys),
    )
    return chosen
