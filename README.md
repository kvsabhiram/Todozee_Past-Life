# Past Life (Gatha Janma) Insight Generator

A one-time, belief-based "past life reflection" generator that runs the
local **Google Gemma 4** model on your own GPU, blends in **real astrology**
(Western + Vedic), and serves everything behind a clean **FastAPI**
service.

The reading the user gets is structured into seven themed sections with
emoji headers that change per archetype — a Healer sees garden / healing
emojis, a Builder sees foundation / stone emojis, a Mystic sees moon /
veil emojis, and so on. Twelve premium archetypes rotate across users so
nobody is locked into the same role.

---

## Features

- **Local LLM** — Gemma 4 (`google/gemma-4-E2B-it`) loaded via Hugging
  Face `transformers`. No external API, no per-token cost, no rate
  limits.
- **Real astrology** — `kerykeion` for Sun / Moon / Ascendant (Western
  tropical) and `pyswisseph` + Lahiri ayanamsa for Vedic Nakshatra,
  Pada, Rashi, and Lagna.
- **Rich mode auto-detected** — when the user gives all four inputs
  (name + DOB + time + place), Vedic data is woven into the reading.
- **12 rotating premium archetypes** — Healer, Scholar, Teacher, Artist,
  Explorer, Merchant, Guardian, Leader, Mystic, Storyteller, Builder,
  Navigator. Each carries themed section headers.
- **100+ mystical-words pool per zodiac sign** (~1,300 words total).
  A deterministic per-user palette of 25 is handed to the model, so two
  users with the same sign still get different prose.
- **8 rotating opening sentences** — same template pool, different
  per-user pick. No two readings start identically.
- **Append-only interaction log** — every request input + output is
  saved to `past_life_storage/interactions.jsonl` and exposed via
  `GET /interactions`.
- **One-time guarantee** — once an insight is generated for a user, it
  is cached on disk and re-served forever.

---

## Tech stack

| Layer              | Library / model                       |
| ------------------ | ------------------------------------- |
| Web framework      | FastAPI + Uvicorn + Pydantic v2       |
| LLM                | `google/gemma-4-E2B-it` (Hugging Face)|
| Tensor compute     | PyTorch (CUDA 12.8 build for sm_120)  |
| Western astrology  | `kerykeion`                           |
| Vedic astrology    | `pyswisseph` (Swiss Ephemeris)        |
| Persistence        | Local JSON files (one per user)       |

Tested on Python 3.13 + NVIDIA RTX 5090. Any GPU that supports CUDA 12.8
+ bfloat16 should work.

---

## Installation

> **IMPORTANT — install PyTorch first from the CUDA-12.8 wheel index.**
> The default PyPI wheel is compiled for CUDA 13.0; on most current
> drivers it will silently fall back to CPU and a single insight takes
> ~170 seconds instead of ~5 seconds.

```bash
git clone https://github.com/kvsabhiram/Todozee_Past-Life.git
cd Todozee_Past-Life

# 1. Make a venv (Python 3.13)
python -m venv past-life
source past-life/bin/activate

# 2. Install PyTorch from the CUDA-12.8 wheel index
pip install --index-url https://download.pytorch.org/whl/cu128 \
    torch torchvision torchaudio

# 3. Install everything else
pip install -r requirements.txt
```

That's it. No Hugging Face token needed — Gemma 4 is Apache-2.0 and
ungated.

---

## Running

```bash
python Past_Life.py
```

The server boots on `http://0.0.0.0:7002`. On first run it downloads
~10 GB of Gemma 4 weights into `~/.cache/huggingface/` — subsequent
starts are fast.

You'll see a banner like:

```
══════════════════════════════════════════════════════════
  🌿  Past Life Insight API  (local Gemma)
  Model       : google/gemma-4-E2B-it
  Listening   : http://0.0.0.0:7002
  Swagger UI  : http://0.0.0.0:7002/docs
══════════════════════════════════════════════════════════
```

Open the Swagger UI in a browser to try the endpoints interactively.

### CLI mode

```bash
python Past_Life.py --cli --generate
```

Runs an interactive CLI version that asks for name + birth details and
prints a framed ASCII "card" output.

---

## API endpoints

| Method | Path                       | Purpose                                           |
| ------ | -------------------------- | ------------------------------------------------- |
| GET    | `/`                        | Service metadata + model state                    |
| GET    | `/health`                  | Health check + GPU info                           |
| GET    | `/archetypes`              | List the 15 base symbolic archetypes              |
| POST   | `/insight`                 | Generate (or fetch cached) past-life reflection   |
| GET    | `/insight/{user_id}`       | Re-fetch a cached insight                         |
| DELETE | `/insight/{user_id}`       | Delete a cached insight (admin)                   |
| GET    | `/interactions`            | Tail the append-only request/response log         |
| GET    | `/interactions/stats`      | Aggregate counters over the log                   |
| GET    | `/docs`                    | Swagger UI                                        |

### Minimal request

Only `name` and `date_of_birth` are required:

```bash
curl -X POST http://0.0.0.0:7002/insight \
     -H 'Content-Type: application/json' \
     -d '{"name": "Aarav", "date_of_birth": "1990-05-15"}'
```

### Rich-mode request (all 4 inputs → Vedic data)

```bash
curl -X POST http://0.0.0.0:7002/insight \
     -H 'Content-Type: application/json' \
     -d '{
       "name": "Aarav",
       "date_of_birth": "1990-05-15",
       "time_of_birth": "14:30",
       "place_of_birth": "Hyderabad, India"
     }'
```

### Sample response

```json
{
  "is_new": true,
  "user_id": "18e9549056110d29",
  "archetypal_role": "earth keeper",
  "insight_text": "🏛️ Your Possible Past Life as a Builder\n...\n🔨 The Strength You Forged\n...",
  "generated_at": "2026-06-27T12:30:00+00:00",
  "source": "gemma"
}
```

The `insight_text` contains the full 7-section reading with archetype-
themed emoji headers.

---

## Output format

Every fresh generation follows this structure (headers vary per
archetype):

```
🏛️  Your Possible Past Life as a Builder
🧱  The Soul of the Builder
🔨  The Strength You Forged
📐  The Lesson in the Foundation
🏗️  Building Forward
❝ Words from the Quarry ❞
ℹ️  A Note from the Stones
```

Length is held to 150–250 words across all sections. The model is
instructed to:

- Use the opening sentence verbatim from a per-user pool of 8.
- Mention the Sun sign once if it fits naturally.
- (Rich mode only) Reference Nakshatra by name + quality, once.
- Weave 3–4 mystical words from the per-user palette of 25.
- Write its own short closing quote (no fake attributions).
- Avoid generic horoscope language entirely.

---

## Package layout

The codebase used to be a single 2,350-line file. It is now a focused
17-module package:

```
past_life/
├── __init__.py
├── logging_setup.py        # shared logger
├── models.py               # dataclasses
├── archetypes.py           # 15 base symbolic archetypes
├── vocab.py                # 100+ mystical words × 12 signs
├── vedic.py                # Nakshatra / Pada / Rashi / Lagna
├── astrology.py            # Western + rich-mode bridge
├── narrative.py            # variation seeds
├── storage.py              # JSONL log + insight cache
├── selection.py            # archetype picker (CLI)
├── payload.py              # builds JSON sent to the model
├── premium_archetypes.py   # 12 rotating archetypes + themed headers
├── prompts.py              # SYSTEM_PROMPT + opening rotation
├── gemma.py                # Gemma 4 loader + generation
├── orchestrator.py         # one-time generate-or-fetch (CLI)
├── renderer.py             # ASCII card + deterministic fallback
└── api.py                  # FastAPI app + all endpoints

Past_Life.py                # thin uvicorn entrypoint
pyproject.toml              # uv / pip metadata
requirements.txt            # plain pip
past_life_storage/          # user data (git-ignored)
```

---

## How an insight is built end-to-end

```
POST /insight  (name, date_of_birth)
        │
        ▼
1. Derive user_id from SHA-256(name + dob).
2. Compute Sun / Moon / Ascendant via kerykeion.
3. If birth time + place given → also compute Vedic facts.
4. Pick a deterministic opening sentence (1 of 8) from user_id.
5. Pick a premium archetype (1 of 3 candidates per Sun sign) from user_id.
6. Pick a theme (1 of ~11) from user_id + archetype.
7. Select 25 mystical words from this Sun sign's 100+-word pool.
8. Bundle everything into a JSON payload.
9. Send to Gemma 4 with the SYSTEM_PROMPT.
10. Save the result to disk + append to the JSONL log.
        │
        ▼
JSON response with insight_text + archetypal_role
```

The same user always gets the same archetype, opening, theme, and word
palette — so re-fetching is bit-for-bit reproducible.

---

## Disclaimer

Every reading ends with this exact line, included in the prompt as a
hard requirement:

> *This reflection is intended for inspiration and self-exploration. It
> is not a factual account of a previous life.*

The service is **belief-based**. It never claims certainty, predicts the
future, identifies real historical people, or makes factual / scientific
/ historical claims.

---

## License

The source code in this repository is yours to use. Gemma 4 weights
themselves are published by Google under the Apache-2.0 license — review
[Google's Gemma terms](https://ai.google.dev/gemma/terms) before any
commercial redistribution of the model files.
