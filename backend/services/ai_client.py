"""
Pluggable AI client.

- If OPENAI_API_KEY is set → calls an OpenAI-compatible Chat Completions API
- Otherwise → returns deterministic demo output (works fully offline)

The endpoint is AI_BASE_URL (default https://api.openai.com/v1). The model is
AI_MODEL, then OPENAI_MODEL, then gpt-4o-mini. Any Chat Completions host works,
including Abacus.AI RouteLLM.

Usage:
    from services.ai_client import generate_text
    text = generate_text("Write a listing for a 3-bed home in Austin")
"""

import os
import re
import hashlib
from contextvars import ContextVar
from typing import Optional
from urllib.parse import urlparse

import httpx


# ─── Demo corpus ──────────────────────────────────────────────────────────────
# Deterministic responses keyed by prompt hash prefix so tests are stable.

_DEMO_RESPONSES = [
    (
        "Welcome to this stunning property that perfectly blends modern elegance with "
        "everyday comfort. Featuring an open-concept floor plan bathed in natural light, "
        "this home offers a chef-inspired kitchen with quartz countertops, stainless steel "
        "appliances, and a large center island perfect for entertaining. The spacious primary "
        "suite includes a spa-like ensuite and walk-in closet. Step outside to a beautifully "
        "landscaped backyard with a covered patio — ideal for Texas evenings. Located minutes "
        "from top-rated schools, dining, and shopping. This is the one you've been waiting for!"
    ),
    (
        "Discover the perfect blend of luxury and livability in this exceptional residence. "
        "Soaring ceilings and designer finishes greet you at every turn, while the gourmet "
        "kitchen — complete with professional-grade appliances and custom cabinetry — will "
        "delight the most discerning chef. Retreat to the primary suite, a true sanctuary "
        "featuring a spa bath and custom closet system. The resort-style backyard with pool "
        "and outdoor kitchen is an entertainer's dream. Nestled in a sought-after neighborhood "
        "with top schools and easy highway access. Schedule your private showing today!"
    ),
    (
        "Exceptional investment opportunity in one of Austin's fastest-growing corridors. "
        "This well-maintained property offers strong rental income potential with recent "
        "updates throughout. The functional floor plan maximizes usable square footage, "
        "while the low-maintenance yard keeps operating costs down. Walking distance to "
        "public transit, restaurants, and retail — tenants love the location. Cap rate "
        "analysis available upon request. Don't miss this turnkey addition to your portfolio."
    ),
]

_mode: ContextVar[str] = ContextVar("keyprose_ai_mode", default="demo")
_notice: ContextVar[Optional[str]] = ContextVar("keyprose_ai_notice", default=None)
_failed: ContextVar[bool] = ContextVar("keyprose_ai_failed", default=False)

_FAIL_NOTICE = "The model call failed, so this is sample output."
_LONG_NOTICE = "This request is too long for a live generation. Showing sample output."


def begin_generation() -> None:
    """Reset per-request live/demo bookkeeping."""
    _mode.set("demo")
    _notice.set(None)
    _failed.set(False)


def generation_mode() -> str:
    return _mode.get()


def generation_notice() -> Optional[str]:
    return _notice.get()


def _mark_live() -> None:
    if not _failed.get():
        _mode.set("live")


def _mark_demo(notice: Optional[str] = None) -> None:
    _failed.set(True)
    _mode.set("demo")
    if notice and not _notice.get():
        _notice.set(notice)


def _demo_response(prompt: str) -> str:
    """Return a deterministic demo response based on prompt hash."""
    h = int(hashlib.md5(prompt.encode()).hexdigest(), 16)
    return _DEMO_RESPONSES[h % len(_DEMO_RESPONSES)]


def _api_key() -> str:
    return (os.getenv("OPENAI_API_KEY") or "").strip()


def live_enabled() -> bool:
    return bool(_api_key())


def configured_model() -> str:
    return (os.getenv("AI_MODEL") or os.getenv("OPENAI_MODEL") or "gpt-4o-mini").strip() or "gpt-4o-mini"


def _base_url() -> str:
    return (os.getenv("AI_BASE_URL") or "https://api.openai.com/v1").strip()


def provider_host() -> str:
    """Hostname of the configured Chat Completions API. Never includes the key."""
    parsed = urlparse(_base_url())
    return parsed.hostname or ""


def chat_completions_url() -> str:
    base = _base_url().rstrip("/")
    parsed = urlparse(base)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ValueError("AI_BASE_URL must be an http(s) URL")
    if base.endswith("/chat/completions"):
        return base
    return base + "/chat/completions"


def _configured_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or str(raw).strip() == "":
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    if value < 0:
        return default
    return value


def _max_tokens(requested: int) -> int:
    cap = _configured_int("AI_MAX_TOKENS", 800)
    if cap <= 0:
        cap = 800
    try:
        asked = int(requested)
    except (TypeError, ValueError):
        asked = cap
    return max(1, min(asked, cap))


def _input_cap() -> Optional[int]:
    cap = _configured_int("AI_MAX_INPUT_CHARS", 8000)
    if cap == 0:
        return None
    return cap if cap > 0 else 8000


def _redact(text: str) -> str:
    key = _api_key()
    if key:
        text = text.replace(key, "[redacted]")
    text = re.sub(r"Bearer\s+\S+", "Bearer [redacted]", text, flags=re.IGNORECASE)
    text = re.sub(r"sk-[A-Za-z0-9_\-]{8,}", "[redacted]", text)
    return text


def generate_text(
    prompt: str,
    max_tokens: int = 512,
    system_message: Optional[str] = None,
    temperature: float = 0.7,
) -> str:
    """
    Generate text using a Chat Completions API if a key is available,
    else return demo output.

    Args:
        prompt: The user prompt / instruction.
        max_tokens: Maximum tokens to generate.
        system_message: Optional system role message.
        temperature: Sampling temperature (0.0–1.0).

    Returns:
        Generated text string.
    """
    api_key = _api_key()

    if not api_key:
        return _demo_response(prompt)

    cap = _input_cap()
    incoming = len(prompt) + len(system_message or "")
    if cap is not None and incoming > cap:
        _mark_demo(_LONG_NOTICE)
        return _demo_response(prompt)

    return _call_model(prompt, max_tokens, system_message, temperature, api_key)


def _call_model(
    prompt: str,
    max_tokens: int,
    system_message: Optional[str],
    temperature: float,
    api_key: str,
) -> str:
    """Call an OpenAI-compatible Chat Completions endpoint."""
    try:
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})

        response = httpx.post(
            chat_completions_url(),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": configured_model(),
                "messages": messages,
                "max_tokens": _max_tokens(max_tokens),
                "temperature": temperature,
            },
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        if not isinstance(content, str) or not content.strip():
            raise ValueError("empty completion")
        _mark_live()
        return content.strip()

    except Exception as exc:
        # Graceful fallback to demo mode on any API error. Never log the key.
        print(f"[ai_client] model call failed ({_redact(str(exc))}), falling back to demo mode.")
        _mark_demo(_FAIL_NOTICE)
        return _demo_response(prompt)
