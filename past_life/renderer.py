"""Local renderer — turns an archetype into a narrative without the model.

Used by the CLI mode (and as a no-model fallback) to produce a deterministic
written-out version of a past-life insight using only Python string templates
and the variation seed. Also builds the framed ASCII "card" version.
"""

from __future__ import annotations

import logging
import textwrap
import unicodedata
from typing import Optional

from .archetypes import ARCHETYPES
from .models import BirthDetails, UserProfile
from .narrative import apply_narrative_variations, get_narrative_variation_seed
from .selection import select_archetype
from .storage import load_insight

logger = logging.getLogger("past_life")


DISCLAIMER = (
    "This is a belief-based, symbolic reflection drawn from "
    "traditional spiritual ideas.  It is not a factual or "
    "scientific claim about your past."
)


def _you(phrase: str) -> str:
    return "You " + phrase[0].lower() + phrase[1:]


def _your(phrase: str) -> str:
    return "Your " + phrase[0].lower() + phrase[1:]


def _cap(phrase: str) -> str:
    return phrase[0].upper() + phrase[1:]


def _render_insight(
    archetype_key: str,
    birth_details: Optional[BirthDetails] = None,
) -> str:
    """Turn one archetype into a clean narrative without touching the model."""
    logger.debug(
        "Rendering deterministic insight for archetype='%s' (has_birth=%s).",
        archetype_key, bool(birth_details),
    )
    base_archetype = ARCHETYPES[archetype_key]
    variation_seed = get_narrative_variation_seed(birth_details)
    a = apply_narrative_variations(base_archetype, archetype_key, variation_seed)

    role = a["archetypal_role"]
    nature = a["core_nature"]
    contrib = a["contribution"]
    unfinished = a["unfinished_theme"]
    lesson = a["present_life_lesson"]

    opening = DISCLAIMER

    opening_options = [
        "In a story that lives beyond time",
        "In a memory woven from starlight and shadow",
        "In the quiet space between one life and another",
        "In the ancient soul-story that shaped you",
        "In the threads that connect all your lifetimes",
        "In a chapter written long before this one",
        "In the depths of your soul's journey",
        "In a time when the world was different but you were you",
        "In the eternal dance of becoming",
        "In a life that echoes still within you",
        "In the mirror that past and present hold up",
        "In the sacred book of your soul",
        "In a world that has faded but lives on in you",
        "In the tapestry of your many journeys",
        "In a realm where memory meets mystery",
        "In the silent knowing that predates thought",
    ]
    opening_phrase = opening_options[variation_seed % len(opening_options)]

    role_block = (
        f"{opening_phrase}, your soul carried the "
        f"energy of the {role}.  "
        + _you(nature[0]) + ".  "
        + _you(nature[1]) + "."
    )

    contrib_options = [
        "Through this quiet presence you made a real difference",
        "In ways both visible and hidden, you changed lives",
        "Your impact rippled outward in circles you never saw",
        "With steadiness and care, you touched countless souls",
        "The difference you made was profound though often invisible",
        "Your gifts were given freely and touched deeply",
        "In small moments and large, you shifted the world",
        "What you offered changed the course of many lives",
        "Your presence was a blessing even when unnamed",
        "The seeds you planted grew in ways you never witnessed",
        "You served in ways that mattered more than you knew",
        "Your contribution was woven into the fabric of community",
        "What you gave shaped the world in lasting ways",
        "Your impact was felt long after you moved on",
        "The care you offered created ripples across time",
        "You left the world different than you found it",
    ]
    contrib_phrase = contrib_options[(variation_seed // 16) % len(contrib_options)]

    contrib_block = (
        f"{contrib_phrase}.  "
        + _you(contrib[0]) + ".  "
        + _you(contrib[1]) + "."
    )

    unfinished_options = [
        "Yet beneath that strength, something remained softly unresolved",
        "Still, a quiet longing lingered beneath the surface",
        "But within all you gave, something of yours waited",
        "And yet, a part of you stayed in shadow",
        "Even so, one thread was left unwoven",
        "Yet something within you remained unspoken",
        "But a gentle ache persisted in the background",
        "Still, one door remained closed to you",
        "Even then, a piece of your heart stayed unfulfilled",
        "Yet beneath the surface, a question lingered",
        "But one note in your song was never played",
        "Still, a part of you remained hidden even from yourself",
        "And yet, something essential waited to bloom",
        "Even so, one aspect of you never fully emerged",
        "But a quiet need went unmet through all those years",
        "Yet within your service, your own soul stood waiting",
    ]
    unfinished_phrase = unfinished_options[
        (variation_seed // 256) % len(unfinished_options)
    ]

    unfinished_block = (
        f"{unfinished_phrase}.  "
        + _your(unfinished[0]) + ".  "
        + _your(unfinished[1]) + "."
    )

    lesson_options = [
        "That thread has followed you into this life — not as a burden, but as an invitation",
        "This lifetime offers you a chance to complete what was left undone",
        "The invitation carried forward into this life is clear and simple",
        "What was once unfinished now asks gently to be resolved",
        "This life brings the opportunity to honor what was postponed",
        "Now, in this lifetime, you can tend to what was set aside",
        "The work that waited then calls to you now",
        "This present life whispers the same invitation",
        "What you couldn't do then, you can embrace now",
        "The path opens now to what was once closed",
        "This time around, you carry the key to what was locked",
        "Now the missing piece can finally find its place",
        "This lifetime brings the medicine for that old wound",
        "The door that once closed stands open before you now",
        "Now you hold the answer to that ancient question",
        "This life offers the completion that once eluded you",
    ]
    lesson_phrase = lesson_options[(variation_seed // 4096) % len(lesson_options)]

    lesson_block = (
        f"{lesson_phrase}.  "
        + _cap(lesson[0]) + ".  "
        + _cap(lesson[1]) + "."
    )

    closing_options = [
        "This is not a weight to carry.  It is a door, gently open, waiting for you to walk through in your own time.",
        "This is not a demand, only an invitation.  The door opens when you're ready.",
        "There is no rush.  The path reveals itself one step at a time.",
        "You already know the way.  Trust what stirs within you.",
        "Take your time.  The invitation doesn't expire.",
        "This is yours to claim whenever you choose.",
        "The unfinished becomes whole at your own pace.",
        "Listen.  Something within you already knows what to do.",
        "You've carried this far enough.  Set it down when you're ready.",
        "The answer lives in you.  It always has.",
        "Your soul remembers.  Follow what feels true.",
        "This is not homework.  It's an opening.",
        "The thread pulls gently.  You choose whether to follow.",
        "What was once impossible is now simply waiting.",
        "The past releases you into this moment.",
        "You are already on the path, even if you don't yet see it.",
    ]
    closing = closing_options[(variation_seed // 65536) % len(closing_options)]

    rendered = "\n\n".join([
        opening, role_block, contrib_block,
        unfinished_block, lesson_block, closing,
    ])
    logger.debug(
        "Rendered local insight: archetype='%s' length=%d chars / %d words.",
        archetype_key, len(rendered), len(rendered.split()),
    )
    return rendered


def render_and_print(profile: UserProfile) -> None:
    """End-to-end local preview: gate check → render → print."""
    existing = load_insight(profile.user_id)
    if existing and existing.past_life_unlocked:
        logger.info("Rendering cached insight for user_id=%s.", profile.user_id)
        _print_card(
            existing.archetypal_role, existing.insight_text,
            existing.generated_at, cached=True,
        )
        return

    archetype_key = select_archetype(profile)
    insight_text = _render_insight(archetype_key, profile.birth_details)
    role = ARCHETYPES[archetype_key]["archetypal_role"]

    _print_card(role, insight_text, generated_at=None, cached=False)


def _display_width(s: str) -> int:
    """Visual column width of a string, treating emoji / wide CJK as 2 cols."""
    try:
        from wcwidth import wcswidth
        w = wcswidth(s)
        if w is not None and w >= 0:
            return w
    except ImportError:
        pass

    total = 0
    for ch in s:
        cp = ord(ch)
        if cp == 0:
            continue
        if (
            0x1F300 <= cp <= 0x1FAFF or
            0x1F000 <= cp <= 0x1F2FF or
            0x2600 <= cp <= 0x26FF
        ):
            total += 2
            continue
        ea = unicodedata.east_asian_width(ch)
        total += 2 if ea in ("W", "F") else 1
    return total


def _pad_line(content: str, inner_width: int) -> str:
    """Pad a line so its visible width equals inner_width."""
    pad = inner_width - _display_width(content)
    if pad < 0:
        pad = 0
    return content + (" " * pad)


def _build_card(
    role: str, text: str,
    generated_at: Optional[str], cached: bool,
    width: int = 60,
) -> str:
    """Build the framed past-life insight card as a single string."""
    inner = width - 2
    lines: list[str] = []

    lines.append("╭" + "─" * inner + "╮")

    title = "  🌿  YOUR PAST LIFE INSIGHT" + (
        "  (lifetime copy)  " if cached else ""
    )
    lines.append("│" + _pad_line(title, inner) + "│")
    lines.append("├" + "─" * inner + "┤")

    badge = f"  ✦  Archetypal Role :  {role.title()}"
    lines.append("│" + _pad_line(badge, inner) + "│")
    if generated_at:
        ts = f"  ✦  Unlocked on     :  {generated_at[:10]}"
        lines.append("│" + _pad_line(ts, inner) + "│")
    lines.append("├" + "─" * inner + "┤")

    text_width = inner - 4
    for paragraph in text.split("\n\n"):
        wrapped = textwrap.wrap(paragraph, width=text_width) or [""]
        for line in wrapped:
            lines.append("│  " + _pad_line(line, text_width) + "  │")
        lines.append("│" + " " * inner + "│")

    if cached:
        lines.append("├" + "─" * inner + "┤")
        notice = "  ℹ  This insight is available only once as part of"
        lines.append("│" + _pad_line(notice, inner) + "│")
        notice2 = "     a lifetime reflection."
        lines.append("│" + _pad_line(notice2, inner) + "│")

    lines.append("╰" + "─" * inner + "╯")
    return "\n".join(lines)


def _print_card(
    role: str, text: str,
    generated_at: Optional[str], cached: bool,
) -> None:
    """Print the framed card to stdout (CLI mode)."""
    print("\n" + _build_card(role, text, generated_at, cached) + "\n")
