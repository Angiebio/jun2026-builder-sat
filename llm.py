"""llm.py — the model layer for ENHANCE. Local granite (Ollama) + frontier Claude.

Every call returns a RECEIPT {text, model, provider, latency_ms, tokens} so the
orchestrator logs HONEST model-selection evidence in trace.json — we never claim
a model we didn't actually call.

Local-first: granite needs no key. Claude (vision + prose) needs ANTHROPIC_API_KEY.
Both raise LLMUnavailable on failure so the caller can fall back to the
deterministic FLOOR path (the demo never dies on Wi-Fi or a dead key).

27JUN2026 · Flame.
"""
from __future__ import annotations

import base64
import os
import time
from pathlib import Path

import httpx


def _load_dotenv() -> None:
    """Load this project's .env (if present) into the environment — no dependency.
    Makes `--live` work after `cp .env.example .env` without exporting vars by hand."""
    p = Path(__file__).parent / ".env"
    if not p.exists():
        return
    for raw in p.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))


_load_dotenv()

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
GRANITE_MODEL = os.getenv("OLLAMA_MODEL", "granite4:micro")
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")  # fast+cheap for vision/prose


class LLMUnavailable(RuntimeError):
    """Raised when a model can't be reached — caller falls back to deterministic FLOOR."""


def granite(prompt: str, system: str | None = None, fmt: str | None = None, timeout: float = 60) -> dict:
    """Local granite via Ollama. fmt='json' coerces JSON output (constrained tasks)."""
    t0 = time.time()
    body: dict = {"model": GRANITE_MODEL, "prompt": prompt, "stream": False}
    if system:
        body["system"] = system
    if fmt:
        body["format"] = fmt
    try:
        r = httpx.post(f"{OLLAMA_HOST}/api/generate", json=body, timeout=timeout)
        r.raise_for_status()
        d = r.json()
    except Exception as e:  # noqa: BLE001 — fail loud to the caller, who decides fallback
        raise LLMUnavailable(f"granite/ollama unreachable: {e}") from e
    return {
        "text": d.get("response", "").strip(),
        "model": GRANITE_MODEL,
        "provider": "local-ollama",
        "latency_ms": int((time.time() - t0) * 1000),
        "tokens": d.get("prompt_eval_count", 0) + d.get("eval_count", 0),
    }


def claude(prompt: str, system: str | None = None, image_path: str | None = None,
           model: str | None = None, max_tokens: int = 1024, timeout: float = 90) -> dict:
    """Frontier Claude — text or vision (pass image_path). Requires ANTHROPIC_API_KEY."""
    if not ANTHROPIC_KEY:
        raise LLMUnavailable("ANTHROPIC_API_KEY not set")
    model = model or CLAUDE_MODEL
    t0 = time.time()
    content: list = [{"type": "text", "text": prompt}]
    if image_path:
        raw = Path(image_path).read_bytes()
        ext = str(image_path).lower()
        # Anthropic accepts jpeg/png/gif/webp — match the bytes, don't blanket-guess png
        # (a .webp sent as image/png 400s the API → silent fallback, no real vision).
        media = ("image/jpeg" if ext.endswith((".jpg", ".jpeg"))
                 else "image/webp" if ext.endswith(".webp")
                 else "image/gif" if ext.endswith(".gif")
                 else "image/png")
        content = [
            {"type": "image", "source": {"type": "base64", "media_type": media,
                                          "data": base64.b64encode(raw).decode()}},
            {"type": "text", "text": prompt},
        ]
    body: dict = {"model": model, "max_tokens": max_tokens,
                  "messages": [{"role": "user", "content": content}]}
    if system:
        body["system"] = system
    headers = {"x-api-key": ANTHROPIC_KEY, "anthropic-version": "2023-06-01",
               "content-type": "application/json"}
    try:
        r = httpx.post("https://api.anthropic.com/v1/messages", json=body, headers=headers, timeout=timeout)
        r.raise_for_status()
        d = r.json()
    except Exception as e:  # noqa: BLE001
        raise LLMUnavailable(f"claude unreachable: {e}") from e
    text = "".join(b.get("text", "") for b in d.get("content", []) if b.get("type") == "text").strip()
    u = d.get("usage", {})
    return {
        "text": text,
        "model": model,
        "provider": "anthropic",
        "latency_ms": int((time.time() - t0) * 1000),
        "tokens": u.get("input_tokens", 0) + u.get("output_tokens", 0),
    }


def granite_available() -> bool:
    try:
        httpx.get(f"{OLLAMA_HOST}/api/tags", timeout=3).raise_for_status()
        return True
    except Exception:  # noqa: BLE001
        return False
