"""Local Hugging Face model loader + inference call.

Loads Gemma 4 (``google/gemma-4-E2B-it``, a multimodal gemma4-architecture
model) via :class:`AutoModelForImageTextToText` + :class:`AutoProcessor`, and
exposes :func:`call_gemma_local` which formats the chat template, runs
generation on the chosen device, and returns the decoded text.
"""

from __future__ import annotations

import logging
import os
import time
from typing import Optional

try:
    import torch
    # Gemma 4 (gemma4 architecture) is a multimodal model and must be loaded
    # via the image-text-to-text auto class + a processor (not a plain
    # tokenizer / causal-LM class).
    from transformers import AutoProcessor, AutoModelForImageTextToText
    HF_AVAILABLE = True
except ImportError:                          # pragma: no cover
    HF_AVAILABLE = False

from .models import PastLifePayload
from .prompts import SYSTEM_PROMPT, _build_user_message

logger = logging.getLogger("past_life")


MODEL_ID = "google/gemma-4-E2B-it"
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2

# Cache: loaded once, reused across requests
_MODEL_CACHE: dict = {"processor": None, "model": None, "device": None}


def _load_model(hf_token: Optional[str] = None):
    """Load (and cache) the Gemma model + processor locally."""
    if _MODEL_CACHE["model"] is not None:
        logger.debug("Model cache hit; reusing loaded weights on %s.",
                     _MODEL_CACHE["device"])
        return (
            _MODEL_CACHE["processor"],
            _MODEL_CACHE["model"],
            _MODEL_CACHE["device"],
        )

    if not HF_AVAILABLE:
        logger.critical(
            "transformers / torch are not installed. "
            "Install with: pip install --upgrade transformers torch accelerate"
        )
        raise RuntimeError(
            "transformers / torch are not installed.  "
            "Run:  pip install --upgrade transformers torch accelerate"
        )

    token = (
        hf_token
        or os.environ.get("HF_TOKEN")
        or os.environ.get("HUGGINGFACE_HUB_TOKEN")
    )
    if token:
        logger.debug("HF token available (length=%d).", len(token))
    else:
        logger.warning(
            "No HF token found in args or environment (HF_TOKEN / "
            "HUGGINGFACE_HUB_TOKEN). Loading a gated model may fail."
        )

    if torch.cuda.is_available():
        device = "cuda"
        dtype = torch.bfloat16
        gpu_name = torch.cuda.get_device_name(0)
        gpu_mem = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
        logger.info("CUDA device detected: %s (%.1f GB)", gpu_name, gpu_mem)
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        device = "mps"
        dtype = torch.float16
        logger.info("Apple MPS device detected.")
    else:
        device = "cpu"
        dtype = torch.float32
        logger.warning(
            "No GPU/MPS found — falling back to CPU. Inference will be slow."
        )

    logger.info(
        "⏳ Loading %s on %s (dtype=%s) — first run downloads ~10 GB …",
        MODEL_ID, device, dtype,
    )
    t0 = time.time()

    try:
        # Gemma 4 is multimodal: use a processor + the image-text-to-text class.
        processor = AutoProcessor.from_pretrained(MODEL_ID, token=token)
        logger.debug("Processor loaded.")

        model = AutoModelForImageTextToText.from_pretrained(
            MODEL_ID,
            torch_dtype=dtype,
            device_map="auto" if device != "cpu" else None,
            token=token,
        )
        if device == "cpu":
            model = model.to(device)
        model.eval()

        try:
            n_params = sum(p.numel() for p in model.parameters())
            logger.info(
                "Model loaded: parameters=%.2fB on %s",
                n_params / 1e9, device,
            )
        except Exception:                                     # noqa: BLE001
            logger.debug("Could not count parameters.", exc_info=True)

    except Exception as exc:                                  # noqa: BLE001
        logger.critical("Model load failed: %s", exc, exc_info=True)
        raise

    _MODEL_CACHE.update(processor=processor, model=model, device=device)
    logger.info("✅ Model ready in %.1fs.", time.time() - t0)

    return processor, model, device


def call_gemma_local(
    payload: PastLifePayload,
    hf_token: Optional[str] = None,
) -> str:
    """Send the safe payload to the locally-loaded Gemma model."""
    logger.info("Invoking local Gemma for archetype='%s' …",
                payload.past_life_data.get("archetypal_role", "?"))

    processor, model, device = _load_model(hf_token=hf_token)

    user_msg = _build_user_message(payload)

    # Gemma 4 chat template expects message content as a list of typed parts.
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": SYSTEM_PROMPT + "\n\n" + user_msg},
            ],
        },
    ]

    eos_token_id = getattr(
        getattr(processor, "tokenizer", processor), "eos_token_id", None
    )

    last_exc: Optional[Exception] = None
    for attempt in range(1, MAX_RETRIES + 1):
        t_attempt = time.time()
        try:
            logger.info(
                "Local Gemma call — attempt %d/%d …", attempt, MAX_RETRIES,
            )
            inputs = processor.apply_chat_template(
                messages,
                add_generation_prompt=True,
                tokenize=True,
                return_dict=True,
                return_tensors="pt",
            ).to(model.device)
            input_len = inputs["input_ids"].shape[-1]
            logger.debug("Tokenized prompt → %d tokens.", input_len)

            with torch.inference_mode():
                output_ids = model.generate(
                    **inputs,
                    max_new_tokens=600,
                    do_sample=True,
                    temperature=0.85,
                    top_p=0.95,
                    repetition_penalty=1.05,
                    pad_token_id=eos_token_id,
                )

            generated_ids = output_ids[0][input_len:]
            text = processor.decode(
                generated_ids, skip_special_tokens=True,
            ).strip()

            gen_tokens = len(generated_ids)
            elapsed = time.time() - t_attempt
            logger.debug(
                "Generation stats: new_tokens=%d elapsed=%.2fs "
                "tokens/sec=%.1f",
                gen_tokens, elapsed,
                gen_tokens / elapsed if elapsed > 0 else 0,
            )

            if not text:
                raise ValueError("Empty response from model.")
            word_count = len(text.split())
            # New sectioned format: 150-250 prose words + ~30 header words +
            # 16 disclaimer words + ~10 quote words ≈ 200 total minimum.
            # 140 gives some slack while still catching truncated output.
            if word_count < 140:
                raise ValueError(
                    f"Response too short ({word_count} words). Retrying."
                )
            logger.info(
                "✅ Gemma generated %d words in %.2fs (attempt %d).",
                word_count, elapsed, attempt,
            )
            return text

        except Exception as exc:                     # noqa: BLE001
            last_exc = exc
            logger.warning(
                "Attempt %d/%d failed after %.2fs: %s",
                attempt, MAX_RETRIES, time.time() - t_attempt, exc,
            )
            if attempt == MAX_RETRIES:
                logger.error(
                    "All %d Gemma retries exhausted for archetype '%s'.",
                    MAX_RETRIES,
                    payload.past_life_data.get("archetypal_role", "?"),
                )
                raise RuntimeError(
                    f"All local Gemma retries exhausted: {exc}"
                ) from exc
            logger.info("Retrying in %d seconds …", RETRY_DELAY_SECONDS)
            time.sleep(RETRY_DELAY_SECONDS)

    raise RuntimeError(f"Unexpected control flow: {last_exc}")  # pragma: no cover
