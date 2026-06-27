"""Past Life (Gatha Janma) Insight Generator — modular package.

This package was split out of the original monolithic Past_Life.py.
The top-level ``Past_Life.py`` is now a thin entrypoint that imports
:data:`past_life.api.app` and runs uvicorn.

Modules
-------
    logging_setup       – configure the shared ``past_life`` logger
    models              – dataclasses (BirthDetails, UserProfile, PastLifePayload, …)
    archetypes          – the 15 base symbolic archetypes
    narrative           – narrative-variation seed + helpers
    storage             – on-disk persistence + interaction log (JSONL)
    selection           – archetype selection + interactive CLI prompt
    payload             – build the safe JSON payload sent to the model
    vocab               – 100+ mystical words per zodiac sign + per-user picker
    astrology           – kerykeion-based Sun / Moon / Ascendant + rich mode
    vedic               – Lahiri-sidereal Nakshatra / Rashi / Pada / Lagna
    premium_archetypes  – 12 user-facing archetypes with themed section headers
    prompts             – SYSTEM_PROMPT, opening-line variation, user-message builder
    gemma               – local Gemma 4 model loader + ``call_gemma_local``
    orchestrator        – one-time-only generate-or-fetch orchestration
    renderer            – CLI-side narrative renderer + framed "card" formatter
    api                 – FastAPI app, request/response models, all HTTP endpoints
"""
