"""FastAPI application — endpoints, pydantic models, lifespan.

This module is imported as ``past_life.api.app`` from the thin
top-level ``Past_Life.py`` entrypoint. All HTTP behaviour lives here.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

try:
    from fastapi import FastAPI, HTTPException, Query, Request
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel, Field, field_validator, model_validator
    FASTAPI_AVAILABLE = True
except ImportError:                          # pragma: no cover
    FASTAPI_AVAILABLE = False

from .archetypes import ARCHETYPES
from .astrology import archetype_from_astro, compute_astro_facts
from .gemma import (
    HF_AVAILABLE,
    MODEL_ID,
    _MODEL_CACHE,
    _load_model,
    call_gemma_local,
)
from .models import BirthDetails, InsightRecord, UserProfile
from .orchestrator import ONE_TIME_MESSAGE
from .payload import build_payload
from .premium_archetypes import pick_premium_archetype, pick_theme
from .prompts import pick_opening
from .renderer import _build_card, _render_insight
from .selection import select_archetype
from .storage import INTERACTIONS_LOG, _storage_path, load_insight, log_interaction, save_insight

logger = logging.getLogger("past_life")


PRELOAD_MODEL_ON_STARTUP = True

# Always export an `app` name so `from past_life.api import app` works
# even when FastAPI is missing — the entrypoint then prints a clear
# install hint instead of raising a confusing ImportError.
app = None


if FASTAPI_AVAILABLE:

    # ── Pydantic request / response models ────────────────────
    class BirthDetailsIn(BaseModel):
        date_of_birth: str = Field(
            ..., description="YYYY-MM-DD", examples=["1990-05-15"],
        )
        time_of_birth: Optional[str] = Field(
            None, description="HH:MM (24-hour)", examples=["14:30"],
        )
        place_of_birth: Optional[str] = Field(
            None, description="City, Country", examples=["Mumbai, India"],
        )

        @field_validator("date_of_birth")
        @classmethod
        def _check_date(cls, v: str) -> str:
            try:
                datetime.strptime(v, "%Y-%m-%d")
            except ValueError:
                raise ValueError("date_of_birth must be YYYY-MM-DD")
            return v

        @field_validator("time_of_birth")
        @classmethod
        def _check_time(cls, v: Optional[str]) -> Optional[str]:
            if v is None or v == "":
                return None
            try:
                datetime.strptime(v, "%H:%M")
            except ValueError:
                raise ValueError("time_of_birth must be HH:MM (24-hour)")
            return v

    ArchetypeEnum = Enum(
        "ArchetypeEnum",
        {k: k for k in sorted(ARCHETYPES.keys())},
        type=str,
    )

    class InsightRequest(BaseModel):
        name: str = Field(..., min_length=1, examples=["Aarav Sharma"])
        date_of_birth: Optional[str] = Field(
            default=None,
            description="YYYY-MM-DD. Required if `birth_details` is not given.",
            examples=["1990-05-15"],
        )
        time_of_birth: Optional[str] = Field(
            default=None,
            description="Optional HH:MM (24-hour). Improves Moon-sign accuracy.",
            examples=["14:30"],
        )
        place_of_birth: Optional[str] = Field(
            default=None,
            description="Optional 'City, Country'. Used as the chart label.",
            examples=["Mumbai, India"],
        )
        birth_details: Optional[BirthDetailsIn] = Field(
            default=None,
            description="Optional birth_details block. Alternative to passing "
                        "date_of_birth / time_of_birth / place_of_birth at "
                        "the top level — both shapes are accepted.",
        )
        user_id: Optional[str] = Field(
            default=None,
            description="Unique user ID. If omitted, derived from name+DOB.",
            examples=[None],
        )
        archetype_hint: Optional[ArchetypeEnum] = Field(
            default=None,
            description="Optional. Force a specific archetype. Leave blank to auto-select.",
            examples=[None],
        )
        use_gemma: bool = Field(
            default=True,
            description="If true, calls the local Gemma model. "
                        "If false, returns the local deterministic renderer (instant).",
        )
        hf_token: Optional[str] = Field(
            default=None,
            description="Optional Hugging Face token. Falls back to env HF_TOKEN.",
            examples=[None],
        )

        model_config = {
            "json_schema_extra": {
                "examples": [
                    {   # minimal — name + DOB only
                        "name": "Aarav Sharma",
                        "date_of_birth": "1990-05-15",
                        "use_gemma": True,
                    },
                    {   # name + DOB + place (no time)
                        "name": "Aarav Sharma",
                        "date_of_birth": "1990-05-15",
                        "place_of_birth": "Mumbai, India",
                        "use_gemma": True,
                    },
                    {   # full chart inputs
                        "name": "Aarav Sharma",
                        "date_of_birth": "1990-05-15",
                        "time_of_birth": "14:30",
                        "place_of_birth": "Mumbai, India",
                        "use_gemma": True,
                    },
                ]
            }
        }

        @field_validator("date_of_birth")
        @classmethod
        def _check_top_dob(cls, v: Optional[str]) -> Optional[str]:
            if v is None or v == "":
                return None
            try:
                datetime.strptime(v, "%Y-%m-%d")
            except ValueError:
                raise ValueError("date_of_birth must be YYYY-MM-DD")
            return v

        @field_validator("time_of_birth")
        @classmethod
        def _check_top_time(cls, v: Optional[str]) -> Optional[str]:
            if v is None or v == "":
                return None
            try:
                datetime.strptime(v, "%H:%M")
            except ValueError:
                raise ValueError("time_of_birth must be HH:MM (24-hour)")
            return v

        @field_validator("place_of_birth")
        @classmethod
        def _check_top_place(cls, v: Optional[str]) -> Optional[str]:
            if v is None or v == "" or v == "string":
                return None
            return v

        @field_validator("archetype_hint", mode="before")
        @classmethod
        def _check_arch(cls, v):
            if v is None or v == "" or v == "string":
                return None
            if isinstance(v, ArchetypeEnum):
                return v
            if v not in ARCHETYPES:
                raise ValueError(
                    f"archetype_hint must be one of: "
                    f"{', '.join(sorted(ARCHETYPES.keys()))}"
                )
            return v

        @field_validator("user_id", "hf_token", mode="before")
        @classmethod
        def _blank_or_placeholder_to_none(cls, v):
            if v == "" or v == "string":
                return None
            return v

        @model_validator(mode="after")
        def _normalize_birth_fields(self):
            """Merge top-level date/time/place into birth_details so downstream
            code can always read `self.birth_details.*`. At least date_of_birth
            must be provided somewhere — top-level wins when both shapes appear.
            """
            dob = (self.date_of_birth or
                   (self.birth_details.date_of_birth if self.birth_details else None))
            if not dob:
                raise ValueError(
                    "date_of_birth is required (either as a top-level field "
                    "or inside birth_details)."
                )
            tob = self.time_of_birth or (
                self.birth_details.time_of_birth if self.birth_details else None
            )
            place = self.place_of_birth or (
                self.birth_details.place_of_birth if self.birth_details else None
            )
            if self.birth_details is None:
                self.birth_details = BirthDetailsIn(
                    date_of_birth=dob,
                    time_of_birth=tob,
                    place_of_birth=place,
                )
            else:
                self.birth_details.date_of_birth = dob
                self.birth_details.time_of_birth = tob
                self.birth_details.place_of_birth = place
            self.date_of_birth = dob
            self.time_of_birth = tob
            self.place_of_birth = place
            return self

    class InsightResponse(BaseModel):
        is_new: bool
        user_id: str
        archetypal_role: str
        insight_text: str
        generated_at: str
        message: Optional[str] = None
        source: str = Field(..., description="'gemma', 'local', or 'cached'")
        rendered_card: Optional[str] = Field(
            default=None,
            description=(
                "Pre-formatted framed 'card' version of the insight, "
                "identical to the CLI output. Plain text with box-drawing "
                "characters. Render in a monospace font. Only included when "
                "the request is made with ?include_card=true; omitted otherwise "
                "to keep the response small (e.g. for mobile clients)."
            ),
        )

    class ArchetypeInfo(BaseModel):
        key: str
        archetypal_role: str

    # ── Lifespan: preload the model at startup ─────────────────
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        logger.info("🚀 FastAPI lifespan: startup.")
        if PRELOAD_MODEL_ON_STARTUP and HF_AVAILABLE:
            try:
                logger.info("⏳ Preloading Gemma model at startup …")
                _load_model()
                logger.info("✅ Gemma model ready at startup.")
            except Exception as exc:                 # noqa: BLE001
                logger.warning(
                    "⚠ Model preload failed: %s\n"
                    "  First request that uses use_gemma=true will retry.",
                    exc, exc_info=True,
                )
        else:
            logger.info(
                "ℹ Model preload skipped (HF_AVAILABLE=%s, preload=%s).",
                HF_AVAILABLE, PRELOAD_MODEL_ON_STARTUP,
            )
        yield
        logger.info("🛑 FastAPI lifespan: shutdown.")

    # ── App ────────────────────────────────────────────────────
    app = FastAPI(
        title="Past Life (Gatha Janma) Insight API",
        description=(
            "One-time belief-based past life reflections via local Gemma 4 "
            "(`google/gemma-4-E2B-it`) or a deterministic renderer."
        ),
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Middleware: request-level logging ─────────────────────
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        """Attach a request-id and log start / end with duration + status."""
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]
        client = request.client.host if request.client else "unknown"
        logger.info(
            "→ [%s] %s %s from %s",
            request_id, request.method, request.url.path, client,
        )
        t0 = time.time()
        try:
            response = await call_next(request)
        except Exception as exc:                     # noqa: BLE001
            elapsed = (time.time() - t0) * 1000
            logger.exception(
                "✖ [%s] %s %s UNHANDLED after %.1fms: %s",
                request_id, request.method, request.url.path, elapsed, exc,
            )
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "Internal server error",
                    "request_id": request_id,
                },
            )
        elapsed = (time.time() - t0) * 1000
        level = logging.WARNING if response.status_code >= 400 else logging.INFO
        logger.log(
            level,
            "← [%s] %s %s → %d in %.1fms",
            request_id, request.method, request.url.path,
            response.status_code, elapsed,
        )
        response.headers["X-Request-ID"] = request_id
        return response

    # ── Helpers ────────────────────────────────────────────────
    def _derive_user_id(name: str, dob: str, explicit: Optional[str]) -> str:
        if explicit:
            logger.debug("Using explicit user_id='%s'.", explicit)
            return explicit
        seed = f"{name}{dob}"
        derived = hashlib.sha256(seed.encode()).hexdigest()[:16]
        logger.debug("Derived user_id='%s' from name+dob.", derived)
        return derived

    # ── Routes ─────────────────────────────────────────────────
    @app.get("/", tags=["meta"])
    def root():
        logger.debug("GET / — meta endpoint.")
        return {
            "service": "Past Life Insight API (local Gemma)",
            "version": "1.0.0",
            "port": 7002,
            "model": MODEL_ID,
            "model_loaded": _MODEL_CACHE["model"] is not None,
            "endpoints": {
                "POST /insight": "Generate or fetch past life insight",
                "GET /insight/{user_id}": "Retrieve cached insight",
                "GET /archetypes": "List available archetypes",
                "GET /health": "Health check",
                "GET /docs": "Swagger UI",
            },
        }

    @app.get("/health", tags=["meta"])
    def health():
        device = _MODEL_CACHE.get("device")
        loaded = _MODEL_CACHE["model"] is not None
        logger.debug("GET /health — model_loaded=%s device=%s.", loaded, device)
        return {
            "status": "ok",
            "hf_available": HF_AVAILABLE,
            "model_id": MODEL_ID,
            "model_loaded": loaded,
            "device": device,
            "archetype_count": len(ARCHETYPES),
            "time": datetime.now(timezone.utc).isoformat(),
        }

    @app.get(
        "/archetypes",
        response_model=list[ArchetypeInfo],
        tags=["archetypes"],
    )
    def list_archetypes():
        logger.debug("GET /archetypes — returning %d archetypes.", len(ARCHETYPES))
        return [
            ArchetypeInfo(key=k, archetypal_role=v["archetypal_role"])
            for k, v in sorted(ARCHETYPES.items())
        ]

    @app.post(
        "/insight",
        response_model=InsightResponse,
        response_model_exclude_none=True,
        tags=["insight"],
    )
    def generate_insight(req: InsightRequest, include_card: bool = False):
        """Generate (or retrieve cached) past life insight.

        Pass ``?include_card=true`` to also receive the ASCII ``rendered_card``.
        By default it is omitted to keep the response small for mobile clients.
        """
        user_id = _derive_user_id(
            req.name, req.birth_details.date_of_birth, req.user_id,
        )
        logger.info(
            "POST /insight — name='%s' user_id=%s use_gemma=%s hint=%s",
            req.name, user_id, req.use_gemma,
            req.archetype_hint.value if req.archetype_hint else "-",
        )

        archetype_hint_str = (
            req.archetype_hint.value if req.archetype_hint is not None else None
        )

        profile = UserProfile(
            user_id=user_id,
            name=req.name,
            birth_details=BirthDetails(
                date_of_birth=req.birth_details.date_of_birth,
                time_of_birth=req.birth_details.time_of_birth,
                place_of_birth=req.birth_details.place_of_birth,
            ),
            archetype_hint=archetype_hint_str,
        )

        # Request input (without the secret hf_token) for the interaction log.
        req_input = req.model_dump(exclude={"hf_token"})

        # Cached?
        existing = load_insight(user_id)
        if existing and existing.past_life_unlocked:
            logger.info(
                "↩ Returning cached insight for user_id=%s.", user_id,
            )
            resp = InsightResponse(
                is_new=False,
                user_id=user_id,
                archetypal_role=existing.archetypal_role,
                insight_text=existing.insight_text,
                generated_at=existing.generated_at,
                message=ONE_TIME_MESSAGE,
                source="cached",
                rendered_card=_build_card(
                    existing.archetypal_role,
                    existing.insight_text,
                    existing.generated_at,
                    cached=True,
                ) if include_card else None,
            )
            log_interaction(
                endpoint="POST /insight",
                user_id=user_id,
                request_input=req_input,
                output=resp.model_dump(exclude={"rendered_card"}),
            )
            return resp

        # Real astrology: compute Sun / Moon / Ascendant (basic mode) and,
        # when birth time AND place are both given, also Vedic Nakshatra /
        # Rashi / Lagna via past_life.vedic (rich mode).
        astro_facts = compute_astro_facts(
            name=req.name,
            date_of_birth=req.birth_details.date_of_birth,
            time_of_birth=req.birth_details.time_of_birth,
            place_of_birth=req.birth_details.place_of_birth,
            user_seed=user_id,
        )

        # Prefer the sun-sign-driven archetype when the user did not force one.
        archetype_key = (
            req.archetype_hint.value if req.archetype_hint is not None
            else archetype_from_astro(astro_facts) or select_archetype(profile)
        )

        # Pick a per-user opening line so two users don't start with the same
        # sentence even when the archetype repeats.
        opening_line = pick_opening(user_id)

        # Premium output layer: pick one of 12 rotating archetypes (Healer,
        # Scholar, Teacher, Artist, Explorer, Merchant, Guardian, Leader,
        # Mystic, Storyteller, Builder, Navigator) seeded by user_id + sun
        # sign, plus a per-user theme (courage, wisdom, creativity, …).
        sun_abbr = (astro_facts or {}).get("sun_sign", "")[:3].title() if astro_facts else ""
        premium = pick_premium_archetype(sun_abbr, seed=user_id)
        theme = pick_theme(seed=user_id, archetype=premium)
        logger.info(
            "🏺 Premium archetype: %s   theme: %s",
            premium.get("name"), theme,
        )

        if req.use_gemma:
            try:
                payload = build_payload(
                    archetype_key,
                    astro_facts=astro_facts,
                    opening_line=opening_line,
                    premium_archetype=premium,
                    theme=theme,
                )
                insight_text = call_gemma_local(payload, hf_token=req.hf_token)
                source = "gemma"
            except RuntimeError as exc:
                logger.error(
                    "Gemma generation failed for user_id=%s: %s",
                    user_id, exc,
                )
                raise HTTPException(status_code=502, detail=str(exc))
        else:
            logger.info(
                "Using local deterministic renderer for user_id=%s.", user_id,
            )
            insight_text = _render_insight(archetype_key, profile.birth_details)
            source = "local"

        now = datetime.now(timezone.utc).isoformat()
        record = InsightRecord(
            user_id=user_id,
            generated_at=now,
            archetypal_role=ARCHETYPES[archetype_key]["archetypal_role"],
            insight_text=insight_text,
        )
        save_insight(record)
        logger.info(
            "✅ New insight generated: user_id=%s archetype='%s' source=%s",
            user_id, record.archetypal_role, source,
        )

        resp = InsightResponse(
            is_new=True,
            user_id=user_id,
            archetypal_role=record.archetypal_role,
            insight_text=insight_text,
            generated_at=now,
            message=None,
            source=source,
            rendered_card=_build_card(
                record.archetypal_role,
                insight_text,
                now,
                cached=False,
            ) if include_card else None,
        )
        log_interaction(
            endpoint="POST /insight",
            user_id=user_id,
            request_input=req_input,
            output=resp.model_dump(exclude={"rendered_card"}),
        )
        return resp

    @app.get(
        "/insight/{user_id}",
        response_model=InsightResponse,
        response_model_exclude_none=True,
        tags=["insight"],
    )
    def fetch_insight(user_id: str, include_card: bool = False):
        """Retrieve an already-generated insight by user_id.

        Pass ``?include_card=true`` to also receive the ASCII ``rendered_card``.
        """
        logger.info("GET /insight/%s", user_id)
        existing = load_insight(user_id)
        if not existing:
            logger.warning("No insight found for user_id=%s", user_id)
            raise HTTPException(
                status_code=404,
                detail=f"No insight found for user_id '{user_id}'.",
            )
        resp = InsightResponse(
            is_new=False,
            user_id=user_id,
            archetypal_role=existing.archetypal_role,
            insight_text=existing.insight_text,
            generated_at=existing.generated_at,
            message=ONE_TIME_MESSAGE,
            source="cached",
            rendered_card=_build_card(
                existing.archetypal_role,
                existing.insight_text,
                existing.generated_at,
                cached=True,
            ) if include_card else None,
        )
        log_interaction(
            endpoint="GET /insight/{user_id}",
            user_id=user_id,
            request_input={"user_id": user_id, "include_card": include_card},
            output=resp.model_dump(exclude={"rendered_card"}),
        )
        return resp

    @app.delete("/insight/{user_id}", tags=["insight"])
    def delete_insight(
        user_id: str,
        confirm: bool = Query(False, description="Must be true to actually delete."),
    ):
        """Delete a cached insight (admin/testing utility)."""
        logger.info("DELETE /insight/%s confirm=%s", user_id, confirm)
        if not confirm:
            logger.warning(
                "Delete request for user_id=%s without confirm=true — rejected.",
                user_id,
            )
            raise HTTPException(
                status_code=400,
                detail="Pass ?confirm=true to actually delete.",
            )
        path = _storage_path(user_id)
        if not os.path.exists(path):
            logger.warning("No cached insight to delete for user_id=%s.", user_id)
            raise HTTPException(status_code=404, detail="No cached insight found.")
        try:
            os.remove(path)
            logger.info("🗑 Deleted insight for user_id=%s (path=%s).",
                        user_id, path)
        except OSError as exc:
            logger.error("Failed to delete %s: %s", path, exc)
            raise HTTPException(status_code=500, detail=f"Delete failed: {exc}")
        return {"deleted": True, "user_id": user_id}

    # ── Logs ───────────────────────────────────────────────────
    @app.get("/interactions", tags=["logs"])
    def list_interactions(
        limit: int = Query(
            50, ge=1, le=1000,
            description="Number of most-recent records to return (1–1000).",
        ),
        user_id: Optional[str] = Query(
            None,
            description="Optional filter — only return records for this user_id.",
        ),
        endpoint: Optional[str] = Query(
            None,
            description="Optional filter — e.g. 'POST /insight'.",
        ),
    ):
        """Read recent rows of the append-only JSONL interaction log.

        The log lives at ``past_life_storage/interactions.jsonl`` and grows
        by one line per ``POST /insight`` or ``GET /insight/{user_id}``
        call. This endpoint streams the tail of that file back as JSON so
        you can inspect activity without SSH.
        """
        logger.info(
            "GET /interactions limit=%d user_id=%s endpoint=%s",
            limit, user_id or "-", endpoint or "-",
        )
        if not os.path.exists(INTERACTIONS_LOG):
            return {
                "total_returned": 0,
                "log_file": INTERACTIONS_LOG,
                "records": [],
                "note": "No interactions logged yet.",
            }

        # Read newest-first by walking from the end. JSONL is small enough
        # to read in one go (one line per request); only the tail matters.
        try:
            with open(INTERACTIONS_LOG, "r", encoding="utf-8") as fh:
                lines = fh.readlines()
        except OSError as exc:
            logger.error("Could not read %s: %s", INTERACTIONS_LOG, exc)
            raise HTTPException(
                status_code=500,
                detail=f"Could not read interactions log: {exc}",
            )

        records: list[dict] = []
        # Walk from the newest line backwards so the user always sees the
        # latest activity first, regardless of how many filters drop rows.
        for raw in reversed(lines):
            raw = raw.strip()
            if not raw:
                continue
            try:
                rec = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if user_id and rec.get("user_id") != user_id:
                continue
            if endpoint and rec.get("endpoint") != endpoint:
                continue
            records.append(rec)
            if len(records) >= limit:
                break

        return {
            "total_returned": len(records),
            "log_file": INTERACTIONS_LOG,
            "records": records,
        }

    @app.get("/interactions/stats", tags=["logs"])
    def interactions_stats():
        """Aggregate counters over the entire interaction log."""
        logger.debug("GET /interactions/stats")
        stats: dict = {
            "total": 0,
            "by_endpoint": {},
            "by_source": {},
            "by_archetype": {},
            "fresh_vs_cached": {"fresh": 0, "cached": 0},
        }
        if not os.path.exists(INTERACTIONS_LOG):
            stats["log_file"] = INTERACTIONS_LOG
            stats["note"] = "No interactions logged yet."
            return stats

        try:
            with open(INTERACTIONS_LOG, "r", encoding="utf-8") as fh:
                for raw in fh:
                    raw = raw.strip()
                    if not raw:
                        continue
                    try:
                        rec = json.loads(raw)
                    except json.JSONDecodeError:
                        continue
                    stats["total"] += 1
                    ep = rec.get("endpoint", "?")
                    stats["by_endpoint"][ep] = stats["by_endpoint"].get(ep, 0) + 1
                    out = rec.get("output", {}) or {}
                    src = out.get("source", "?")
                    stats["by_source"][src] = stats["by_source"].get(src, 0) + 1
                    arch = out.get("archetypal_role", "?")
                    stats["by_archetype"][arch] = stats["by_archetype"].get(arch, 0) + 1
                    if out.get("is_new"):
                        stats["fresh_vs_cached"]["fresh"] += 1
                    elif out.get("is_new") is False:
                        stats["fresh_vs_cached"]["cached"] += 1
        except OSError as exc:
            logger.error("Could not read %s: %s", INTERACTIONS_LOG, exc)
            raise HTTPException(
                status_code=500,
                detail=f"Could not read interactions log: {exc}",
            )

        stats["log_file"] = INTERACTIONS_LOG
        return stats
