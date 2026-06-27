"""
============================================================
  Past Life (Gatha Janma) Insight Generator  +  FastAPI
  ─────────────────────────────────────────────────────────
  Thin entrypoint. All implementation lives in the
  ``past_life/`` package — see ``past_life/__init__.py`` for
  the module map.

  • Builds a safe, archetypal payload from a user profile.
  • Uses the LOCAL Hugging Face model `google/gemma-4-E2B-it`
    via the `transformers` library  (NO external API).
  • Real astrology via `kerykeion` (name + DOB only).
  • Enforces one-time-only storage & retrieval.
  • FastAPI service exposed on port 7002.
  • Model is preloaded at server startup so the first request
    does NOT pay the load cost.
============================================================
INSTALL REQUIREMENTS
--------------------
    pip install --upgrade transformers torch accelerate pillow
    pip install fastapi "uvicorn[standard]" pydantic
    pip install kerykeion           # real astrology

RUN
---
    python Past_Life.py                  # API on :7002
    python Past_Life.py --cli            # interactive CLI
    python Past_Life.py --port 7002      # custom port
    python Past_Life.py --no-preload     # skip startup model load
    python Past_Life.py --log-level DEBUG --log-file app.log
============================================================
"""

from __future__ import annotations

import hashlib
import os

# Importing this package configures the shared logger and triggers
# top-level imports for transformers / kerykeion (which are heavy).
from past_life.archetypes import ARCHETYPES
from past_life.logging_setup import configure_logging
from past_life.models import UserProfile

# `past_life.api` defines the FastAPI ``app`` object that uvicorn runs.
from past_life.api import FASTAPI_AVAILABLE, app
from past_life.gemma import MODEL_ID
import past_life.api as _api_module


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Past Life (Gatha Janma) Insight Generator – local Gemma + FastAPI",
    )
    parser.add_argument(
        "--cli", action="store_true",
        help="Run the original interactive CLI instead of the API server.",
    )
    parser.add_argument(
        "--host", default="0.0.0.0",
        help="Host for the API server (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port", type=int, default=7002,
        help="Port for the API server (default: 7002)",
    )
    parser.add_argument(
        "--no-preload", action="store_true",
        help="Skip preloading the model at server startup.",
    )

    # ── Logging flags ────────────────────────────────────────
    parser.add_argument(
        "--log-level",
        default=os.environ.get("LOG_LEVEL", "INFO"),
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging verbosity (default: INFO).",
    )
    parser.add_argument(
        "--log-file",
        default=os.environ.get("LOG_FILE"),
        help="Optional path to a rotating log file (e.g., logs/app.log).",
    )

    # legacy CLI flags (only used with --cli)
    parser.add_argument("--user-id", default=None)
    parser.add_argument(
        "--archetype", default=None, choices=list(ARCHETYPES.keys()),
    )
    parser.add_argument(
        "--generate", action="store_true",
        help="Run the local Gemma model (downloads ~10 GB on first run).",
    )
    parser.add_argument("--hf-token", default=None)
    parser.add_argument("--list-archetypes", action="store_true")
    parser.add_argument("--skip-birth", action="store_true")

    cli_args = parser.parse_args()

    # ── Reconfigure logging based on CLI flags ────────────────
    logger = configure_logging(level=cli_args.log_level, log_file=cli_args.log_file)
    logger.info(
        "Past Life service starting (log_level=%s, log_file=%s)",
        cli_args.log_level, cli_args.log_file or "<console only>",
    )

    # ── list archetypes ───────────────────────────────────────
    if cli_args.list_archetypes:
        print("\n  Available Archetypes\n  " + "─" * 40)
        for key, data in sorted(ARCHETYPES.items()):
            print(f"    {key:.<30} {data['archetypal_role']}")
        print()
        raise SystemExit(0)

    # ── CLI mode ──────────────────────────────────────────────
    if cli_args.cli:
        from past_life.orchestrator import get_past_life_insight
        from past_life.renderer import _print_card, render_and_print
        from past_life.selection import prompt_birth_details

        logger.info("Launching interactive CLI mode.")
        name = "User"
        birth_details = None

        if not cli_args.skip_birth and not cli_args.archetype:
            name, birth_details = prompt_birth_details()

        user_id = cli_args.user_id
        if not user_id:
            if birth_details:
                seed = f"{name}{birth_details.date_of_birth}"
                user_id = hashlib.sha256(seed.encode()).hexdigest()[:16]
            else:
                user_id = "demo_user_001"
        logger.debug("CLI user_id resolved to '%s'.", user_id)

        profile = UserProfile(
            user_id=user_id,
            name=name,
            birth_details=birth_details,
            archetype_hint=cli_args.archetype,
        )

        try:
            if cli_args.generate:
                result = get_past_life_insight(profile, hf_token=cli_args.hf_token)
                _print_card(
                    role=result["archetypal_role"],
                    text=result["insight_text"],
                    generated_at=result["generated_at"],
                    cached=not result["is_new"],
                )
            else:
                render_and_print(profile)
        except Exception as exc:                                   # noqa: BLE001
            logger.critical("CLI run failed: %s", exc, exc_info=True)
            raise SystemExit(1)

        raise SystemExit(0)

    # ── API server mode (default) ────────────────────────────
    if not FASTAPI_AVAILABLE:
        logger.critical("FastAPI is not installed.")
        raise RuntimeError(
            "FastAPI is not installed.\n"
            "Run:  pip install fastapi \"uvicorn[standard]\" pydantic"
        )

    try:
        import uvicorn
    except ImportError:
        logger.critical("uvicorn is not installed.")
        raise RuntimeError(
            "uvicorn is not installed.\n"
            "Run:  pip install \"uvicorn[standard]\""
        )

    if cli_args.no_preload:
        _api_module.PRELOAD_MODEL_ON_STARTUP = False
        logger.info("Model preload disabled via --no-preload.")

    banner = (
        "\n" + "═" * 60 + "\n"
        f"  🌿  Past Life Insight API  (local Gemma)\n"
        f"  Model       : {MODEL_ID}\n"
        f"  Listening   : http://{cli_args.host}:{cli_args.port}\n"
        f"  Swagger UI  : http://{cli_args.host}:{cli_args.port}/docs\n"
        f"  ReDoc       : http://{cli_args.host}:{cli_args.port}/redoc\n"
        f"  Preload     : {'yes' if _api_module.PRELOAD_MODEL_ON_STARTUP else 'no (lazy)'}\n"
        f"  Log level   : {cli_args.log_level}\n"
        f"  Log file    : {cli_args.log_file or '<console only>'}\n"
        + "═" * 60 + "\n"
    )
    print(banner)
    logger.info(
        "Starting uvicorn on %s:%d (preload=%s)",
        cli_args.host, cli_args.port, _api_module.PRELOAD_MODEL_ON_STARTUP,
    )

    # Give uvicorn its own log_level so we don't silence its startup banner.
    uvicorn_log_level = cli_args.log_level.lower()
    try:
        uvicorn.run(
            app,
            host=cli_args.host,
            port=cli_args.port,
            log_level=uvicorn_log_level,
        )
    except Exception as exc:                                       # noqa: BLE001
        logger.critical("uvicorn crashed: %s", exc, exc_info=True)
        raise
