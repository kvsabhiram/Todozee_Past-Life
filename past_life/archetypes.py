"""Archetypal catalogue — 15 ready-made past-life archetypes.

Each entry packs the symbolic data the prompt needs to write a reflection:
``core_nature``, ``contribution``, ``unfinished_theme``, ``present_life_lesson``.

This module is intentionally dependency-free so it can be imported from any
other module without circular-import risk.
"""

from __future__ import annotations

import logging

logger = logging.getLogger("past_life")


ARCHETYPES: dict[str, dict] = {
    "silent_organizer": {
        "archetypal_role": "silent organizer",
        "core_nature": [
            "worked quietly behind the scenes",
            "carried responsibility without seeking recognition",
        ],
        "contribution": [
            "supported people and systems",
            "maintained stability and order",
        ],
        "unfinished_theme": [
            "personal vision was often postponed",
            "self-expression took a back seat",
        ],
        "present_life_lesson": [
            "balance responsibility with personal aspirations",
            "allow your own path equal importance",
        ],
    },
    "gentle_healer": {
        "archetypal_role": "gentle healer",
        "core_nature": [
            "offered comfort through presence and patience",
            "sensed the needs of others before they spoke",
        ],
        "contribution": [
            "brought calm to troubled minds and hearts",
            "guided those who were lost toward inner peace",
        ],
        "unfinished_theme": [
            "own emotional wounds were quietly set aside",
            "self-care was never given priority",
        ],
        "present_life_lesson": [
            "healing others begins with healing yourself",
            "your needs matter just as deeply",
        ],
    },
    "wandering_seeker": {
        "archetypal_role": "wandering seeker",
        "core_nature": [
            "felt drawn to truths that lay beyond the ordinary",
            "moved through life with restless curiosity",
        ],
        "contribution": [
            "carried wisdom from one place to another",
            "inspired others to look beyond the familiar",
        ],
        "unfinished_theme": [
            "search for meaning sometimes overshadowed connection",
            "stillness and belonging felt elusive",
        ],
        "present_life_lesson": [
            "wisdom deepens when rooted in relationships",
            "allow yourself to stay and be present",
        ],
    },
    "quiet_guardian": {
        "archetypal_role": "quiet guardian",
        "core_nature": [
            "stood as a steady, watchful presence",
            "protected what was fragile without being asked",
        ],
        "contribution": [
            "shielded the vulnerable from harm",
            "held space so others could feel safe",
        ],
        "unfinished_theme": [
            "own desires were silently surrendered for duty",
            "joy was often deferred to responsibility",
        ],
        "present_life_lesson": [
            "strength includes protecting your own joy",
            "trust that the world can hold itself sometimes",
        ],
    },
    "dream_weaver": {
        "archetypal_role": "dream weaver",
        "core_nature": [
            "lived between the visible and the unseen",
            "carried an inner world richer than most could imagine",
        ],
        "contribution": [
            "painted meaning into the lives of those nearby",
            "turned the ordinary into something sacred",
        ],
        "unfinished_theme": [
            "creative gifts were often hidden from the world",
            "fear of being misunderstood held expression back",
        ],
        "present_life_lesson": [
            "your inner world is a gift meant to be shared",
            "let your vision breathe openly",
        ],
    },
    "steadfast_keeper": {
        "archetypal_role": "steadfast keeper",
        "core_nature": [
            "valued tradition and continuity above change",
            "became the memory that held a community together",
        ],
        "contribution": [
            "preserved what mattered across time",
            "gave others a sense of belonging and roots",
        ],
        "unfinished_theme": [
            "resistance to change sometimes blocked growth",
            "new horizons felt threatening rather than exciting",
        ],
        "present_life_lesson": [
            "honoring the past and embracing the future can coexist",
            "growth does not erase what came before",
        ],
    },
    "free_spirit": {
        "archetypal_role": "free spirit",
        "core_nature": [
            "moved through life with an untamed energy",
            "refused to be limited by expectations",
        ],
        "contribution": [
            "showed others that life could be lived boldly",
            "broke invisible chains with ease and grace",
        ],
        "unfinished_theme": [
            "deep commitments sometimes slipped away too soon",
            "stability felt like a cage",
        ],
        "present_life_lesson": [
            "freedom and belonging are not opposites",
            "the wildest souls can also choose to stay",
        ],
    },
    "patient_scholar": {
        "archetypal_role": "patient scholar",
        "core_nature": [
            "gathered knowledge with quiet dedication",
            "believed that understanding was the highest pursuit",
        ],
        "contribution": [
            "shared light with those who came seeking answers",
            "turned complex truths into simple wisdom",
        ],
        "unfinished_theme": [
            "mind often lived more in thought than in feeling",
            "emotional depth was undervalued",
        ],
        "present_life_lesson": [
            "wisdom lives as much in feeling as in knowing",
            "let your heart guide what your mind has learned",
        ],
    },
    "silent_witness": {
        "archetypal_role": "silent witness",
        "core_nature": [
            "observed the world with deep, quiet attention",
            "understood more than was ever spoken aloud",
        ],
        "contribution": [
            "held the truth when others looked away",
            "reminded those around that every story matters",
        ],
        "unfinished_theme": [
            "own voice was rarely heard or valued",
            "longing to be truly seen went unfulfilled",
        ],
        "present_life_lesson": [
            "your perspective has always had power",
            "speak — the world is ready to listen",
        ],
    },
    "gentle_teacher": {
        "archetypal_role": "gentle teacher",
        "core_nature": [
            "guided with patience rather than authority",
            "believed every soul was worthy of understanding",
        ],
        "contribution": [
            "lit small fires of curiosity in quiet minds",
            "helped the overlooked discover their own strength",
        ],
        "unfinished_theme": [
            "generosity left little room for yourself",
            "recognition was rare but the work continued",
        ],
        "present_life_lesson": [
            "teaching yourself is as sacred as teaching others",
            "accept gratitude — it is not a weakness",
        ],
    },
    "bridge_builder": {
        "archetypal_role": "bridge builder",
        "core_nature": [
            "connected people who would never have met otherwise",
            "sensed the invisible threads between souls",
        ],
        "contribution": [
            "turned strangers into community",
            "made understanding possible across great divides",
        ],
        "unfinished_theme": [
            "place was always in the middle, rarely at the center",
            "own identity was sometimes lost in service",
        ],
        "present_life_lesson": [
            "you too deserve to be the one who is connected to",
            "your place is not only between — it is among",
        ],
    },
    "lone_flame": {
        "archetypal_role": "lone flame",
        "core_nature": [
            "burned with an inner fire few could see",
            "carried a purpose that felt larger than one life",
        ],
        "contribution": [
            "inspired without ever being in the spotlight",
            "kept hope alive in the darkest moments",
        ],
        "unfinished_theme": [
            "isolation was the price paid for intensity",
            "longing for deep companionship went unanswered",
        ],
        "present_life_lesson": [
            "your flame is brighter when shared",
            "let others walk beside you on this path",
        ],
    },
    "earth_keeper": {
        "archetypal_role": "earth keeper",
        "core_nature": [
            "felt deeply connected to the living world",
            "understood that patience was its own kind of power",
        ],
        "contribution": [
            "nourished what others overlooked",
            "reminded souls of the quiet magic in simple things",
        ],
        "unfinished_theme": [
            "inner rhythm often clashed with the pace of the world",
            "ambition was sometimes mistaken for laziness",
        ],
        "present_life_lesson": [
            "depth moves at its own rhythm — trust yours",
            "the world needs more of what you quietly offer",
        ],
    },
    "star_dreamer": {
        "archetypal_role": "star dreamer",
        "core_nature": [
            "lived with one eye on the horizon",
            "carried visions that others called impossible",
        ],
        "contribution": [
            "expanded the sense of what was possible",
            "planted seeds of hope in uncertain times",
        ],
        "unfinished_theme": [
            "dreams sometimes floated too far from action",
            "deepest hopes were often invisible to others",
        ],
        "present_life_lesson": [
            "your dreams are not distractions — they are directions",
            "one small step today honors every vision you carry",
        ],
    },
    "sacred_storyteller": {
        "archetypal_role": "sacred storyteller",
        "core_nature": [
            "carried the memory of what truly mattered",
            "turned experience into meaning for everyone around",
        ],
        "contribution": [
            "gave voice to the voiceless through narrative",
            "wove hearts together with the thread of shared truth",
        ],
        "unfinished_theme": [
            "own story was often told last or not at all",
            "role as narrator rarely became the role of hero",
        ],
        "present_life_lesson": [
            "you are not only the one who tells — you are also the story",
            "step into your own narrative with courage",
        ],
    },
}

logger.debug("Loaded %d archetypes into catalogue.", len(ARCHETYPES))
