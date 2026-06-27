"""Premium output-layer archetypes + theme rotation.

This sits on top of the base 15-entry ``ARCHETYPES`` catalogue. The base
catalogue still drives the deterministic CLI renderer and the symbolic
``past_life_data`` payload. The 12 premium archetypes defined here are the
*role names the user sees* in the new sectioned ``🏺 Past Life Archetype``
block (Healer, Scholar, Teacher, Artist, Explorer, Merchant, Guardian,
Leader, Mystic, Storyteller, Builder, Navigator).

Each sun sign has 3 candidate premium archetypes — a deterministic
per-user hash picks one of the three, so different users with the same
sun sign rotate across archetypes (no user is forever a "Healer").
Themes (courage, wisdom, creativity, …) rotate the same way.

Each premium archetype also carries a ``section_headers`` dict with
archetype-themed emoji + title for each of the 7 output sections, so a
Healer's reading uses garden/healing emojis while a Builder's uses
stone/foundation emojis, etc.
"""

from __future__ import annotations

import hashlib


PREMIUM_ARCHETYPES: dict[str, dict] = {
    "Healer": {
        "name": "Healer",
        "strength": "a soft, attentive presence that calmed others without words",
        "lesson": "your own tenderness was set aside while you tended to others",
        "present_message": "begin offering yourself the same care you so easily give others",
        "themes": ["forgiveness", "balance", "trust"],
        "section_headers": {
            "past_life":   "💚  Your Possible Past Life as a Healer",
            "archetype":   "🌿  The Soul of the Healer",
            "strength":    "🌱  The Gift in Your Hands",
            "lesson":      "🍂  The Wound You Quietly Tended",
            "message":     "🌸  Healing Forward",
            "quote":       "❝ A Whisper from the Garden ❞",
            "disclaimer":  "ℹ️  A Gentle Note",
        },
    },
    "Scholar": {
        "name": "Scholar",
        "strength": "patient, deep inquiry — you turned long study into clear wisdom",
        "lesson": "the mind sometimes outran the heart, leaving feeling behind",
        "present_message": "let your heart join your mind; both have something to say",
        "themes": ["wisdom", "growth", "purpose"],
        "section_headers": {
            "past_life":   "📚  Your Possible Past Life as a Scholar",
            "archetype":   "🪶  The Soul of the Scholar",
            "strength":    "🕯️  The Light in Your Mind",
            "lesson":      "📜  The Lesson Between the Lines",
            "message":     "🔍  Wisdom Carried Forward",
            "quote":       "❝ Words from the Library ❞",
            "disclaimer":  "ℹ️  A Note in the Margins",
        },
    },
    "Teacher": {
        "name": "Teacher",
        "strength": "patient clarity — you helped others see what they could not see alone",
        "lesson": "you forgot how much you, too, were learning",
        "present_message": "stay a student of your own life — there is more for you to receive",
        "themes": ["wisdom", "growth", "purpose"],
        "section_headers": {
            "past_life":   "🧑‍🏫  Your Possible Past Life as a Teacher",
            "archetype":   "🌟  The Soul of the Teacher",
            "strength":    "🔔  The Voice You Carried",
            "lesson":      "📖  The Lesson You Almost Missed",
            "message":     "✏️  Teaching Forward",
            "quote":       "❝ A Note Left on the Desk ❞",
            "disclaimer":  "ℹ️  A Quiet Reminder",
        },
    },
    "Artist": {
        "name": "Artist",
        "strength": "a vision that found beauty where others saw the ordinary",
        "lesson": "fear of judgment kept some of your work hidden",
        "present_message": "let your work be seen — it was always meant for the world",
        "themes": ["creativity", "courage", "purpose"],
        "section_headers": {
            "past_life":   "🎨  Your Possible Past Life as an Artist",
            "archetype":   "🖌️  The Soul of the Artist",
            "strength":    "🌈  The Vision You Held",
            "lesson":      "🎭  The Lesson in the Quiet",
            "message":     "✨  Creating Forward",
            "quote":       "❝ A Line from the Sketchbook ❞",
            "disclaimer":  "ℹ️  A Small Note",
        },
    },
    "Explorer": {
        "name": "Explorer",
        "strength": "curiosity that carried you to thresholds others would not cross",
        "lesson": "you moved on so often that some depths went unmet",
        "present_message": "exploration includes turning inward; stay long enough to know",
        "themes": ["courage", "exploration", "growth"],
        "section_headers": {
            "past_life":   "🧭  Your Possible Past Life as an Explorer",
            "archetype":   "🗺️  The Soul of the Explorer",
            "strength":    "🌄  The Strength of the Road",
            "lesson":      "🏕️  The Lesson Along the Way",
            "message":     "⛰️  Exploring Forward",
            "quote":       "❝ A Page from the Journal ❞",
            "disclaimer":  "ℹ️  A Traveler's Note",
        },
    },
    "Merchant": {
        "name": "Merchant",
        "strength": "a gift for fair exchange — trust formed wherever you traded",
        "lesson": "you sometimes held on too tightly to what was meant to flow",
        "present_message": "true wealth is what passes through you, not what you hold",
        "themes": ["trust", "balance", "purpose"],
        "section_headers": {
            "past_life":   "⚖️  Your Possible Past Life as a Merchant",
            "archetype":   "🪙  The Soul of the Merchant",
            "strength":    "🌊  The Strength of Exchange",
            "lesson":      "🧺  The Lesson of Letting Go",
            "message":     "🛤️  Trading Forward",
            "quote":       "❝ Words from the Caravan ❞",
            "disclaimer":  "ℹ️  A Quiet Receipt",
        },
    },
    "Guardian": {
        "name": "Guardian",
        "strength": "steady vigilance — you protected what was fragile without being asked",
        "lesson": "your own desires were set aside in the name of duty",
        "present_message": "guard your joy with the same devotion you offered others",
        "themes": ["resilience", "balance", "trust"],
        "section_headers": {
            "past_life":   "🛡️  Your Possible Past Life as a Guardian",
            "archetype":   "🗝️  The Soul of the Guardian",
            "strength":    "🏔️  The Steady Watch",
            "lesson":      "🌒  The Lesson of the Vigil",
            "message":     "🤲  Guarding Forward",
            "quote":       "❝ A Word at the Gate ❞",
            "disclaimer":  "ℹ️  A Watchful Note",
        },
    },
    "Leader": {
        "name": "Leader",
        "strength": "decisive vision that gave others a direction to walk",
        "lesson": "the weight of every choice made you feel alone in the role",
        "present_message": "share the burden — leading does not mean carrying it all",
        "themes": ["leadership", "courage", "resilience"],
        "section_headers": {
            "past_life":   "👑  Your Possible Past Life as a Leader",
            "archetype":   "🦁  The Soul of the Leader",
            "strength":    "🌅  The Strength to Decide",
            "lesson":      "⛰️  The Lesson of the Crown",
            "message":     "🤝  Leading Forward",
            "quote":       "❝ A Word from the Front ❞",
            "disclaimer":  "ℹ️  A Note from the Council",
        },
    },
    "Mystic": {
        "name": "Mystic",
        "strength": "deep perception — you sensed currents others could not see",
        "lesson": "the inner world felt so vivid that the outer one slipped past",
        "present_message": "bring your inner knowing into ordinary days; it belongs there too",
        "themes": ["wisdom", "trust", "purpose"],
        "section_headers": {
            "past_life":   "🌙  Your Possible Past Life as a Mystic",
            "archetype":   "🔮  The Soul of the Mystic",
            "strength":    "✨  The Sight You Carried",
            "lesson":      "🌑  The Lesson of the Veil",
            "message":     "🕯️  Knowing Forward",
            "quote":       "❝ A Whisper from the Threshold ❞",
            "disclaimer":  "ℹ️  A Quiet Note",
        },
    },
    "Storyteller": {
        "name": "Storyteller",
        "strength": "a voice that turned scattered experience into shared meaning",
        "lesson": "your own story was often told last, or not at all",
        "present_message": "claim your own narrative — you are also the hero of it",
        "themes": ["creativity", "courage", "purpose"],
        "section_headers": {
            "past_life":   "📖  Your Possible Past Life as a Storyteller",
            "archetype":   "🪶  The Soul of the Storyteller",
            "strength":    "🎶  The Voice You Wove",
            "lesson":      "🤐  The Lesson Untold",
            "message":     "📜  Telling Forward",
            "quote":       "❝ A Line from the Tale ❞",
            "disclaimer":  "ℹ️  A Note from the Margin",
        },
    },
    "Builder": {
        "name": "Builder",
        "strength": "vision made tangible — what you built outlived the hands that made it",
        "lesson": "the structures sometimes mattered more than the souls who lived inside",
        "present_message": "build with grace, not only rigor; the why matters as much as the how",
        "themes": ["purpose", "resilience", "growth"],
        "section_headers": {
            "past_life":   "🏛️  Your Possible Past Life as a Builder",
            "archetype":   "🧱  The Soul of the Builder",
            "strength":    "🔨  The Strength You Forged",
            "lesson":      "📐  The Lesson in the Foundation",
            "message":     "🏗️  Building Forward",
            "quote":       "❝ Words from the Quarry ❞",
            "disclaimer":  "ℹ️  A Note from the Stones",
        },
    },
    "Navigator": {
        "name": "Navigator",
        "strength": "a quiet skill for reading signs and finding the way forward",
        "lesson": "always reading the path, you rarely rested in any one place",
        "present_message": "your inner compass is steady; you are allowed to stop and rest",
        "themes": ["trust", "exploration", "balance"],
        "section_headers": {
            "past_life":   "⛵  Your Possible Past Life as a Navigator",
            "archetype":   "🧭  The Soul of the Navigator",
            "strength":    "🌟  The Strength of the Compass",
            "lesson":      "🌊  The Lesson of the Tide",
            "message":     "⚓  Sailing Forward",
            "quote":       "❝ Words from the Helm ❞",
            "disclaimer":  "ℹ️  A Note from the Charts",
        },
    },
}


SUN_SIGN_TO_PREMIUM: dict[str, list[str]] = {
    "Ari": ["Leader",      "Explorer",   "Guardian"],
    "Tau": ["Builder",     "Merchant",   "Guardian"],
    "Gem": ["Storyteller", "Teacher",    "Navigator"],
    "Can": ["Healer",      "Guardian",   "Storyteller"],
    "Leo": ["Leader",      "Artist",     "Teacher"],
    "Vir": ["Scholar",     "Healer",     "Builder"],
    "Lib": ["Artist",      "Merchant",   "Navigator"],
    "Sco": ["Mystic",      "Explorer",   "Healer"],
    "Sag": ["Explorer",    "Navigator",  "Teacher"],
    "Cap": ["Builder",     "Leader",     "Scholar"],
    "Aqu": ["Mystic",      "Navigator",  "Scholar"],
    "Pis": ["Mystic",      "Artist",     "Healer"],
}


THEMES: list[str] = [
    "courage", "wisdom", "creativity", "leadership", "exploration",
    "resilience", "balance", "forgiveness", "trust", "purpose", "growth",
]


def _hash_int(seed: str) -> int:
    return int(hashlib.sha256((seed or "?").encode()).hexdigest(), 16)


def pick_premium_archetype(
    sun_sign_abbr: str,
    seed: str,
) -> dict:
    """Deterministically pick one of the 3 candidate premium archetypes
    for this sun sign, varied by ``seed`` (usually the user_id)."""
    candidates = SUN_SIGN_TO_PREMIUM.get(sun_sign_abbr, [])
    if candidates:
        key = candidates[_hash_int(seed + ":archetype") % len(candidates)]
    else:
        keys = sorted(PREMIUM_ARCHETYPES.keys())
        key = keys[_hash_int(seed + ":archetype") % len(keys)]
    return dict(PREMIUM_ARCHETYPES[key])


def pick_theme(seed: str, archetype: dict | None = None) -> str:
    """Pick a theme deterministically from the user's seed."""
    if archetype and archetype.get("themes"):
        pool = archetype["themes"]
    else:
        pool = THEMES
    return pool[_hash_int(seed + ":theme") % len(pool)]
