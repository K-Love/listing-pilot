"""
Pluggable AI client.

- If OPENAI_API_KEY is set → calls OpenAI Chat Completions API
- Otherwise → returns deterministic demo output (works fully offline)

Usage:
    from services.ai_client import generate_text
    text = generate_text("Write a listing for a 3-bed home in Austin")
"""

import os
import hashlib
import textwrap
from typing import Optional


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


def _demo_response(prompt: str) -> str:
    """Return a deterministic demo response based on prompt hash."""
    h = int(hashlib.md5(prompt.encode()).hexdigest(), 16)
    return _DEMO_RESPONSES[h % len(_DEMO_RESPONSES)]


def generate_text(
    prompt: str,
    max_tokens: int = 512,
    system_message: Optional[str] = None,
    temperature: float = 0.7,
) -> str:
    """
    Generate text using OpenAI if API key is available, else return demo output.

    Args:
        prompt: The user prompt / instruction.
        max_tokens: Maximum tokens to generate.
        system_message: Optional system role message.
        temperature: Sampling temperature (0.0–1.0).

    Returns:
        Generated text string.
    """
    api_key = os.getenv("OPENAI_API_KEY")

    if api_key:
        return _call_openai(prompt, max_tokens, system_message, temperature, api_key)
    else:
        return _demo_response(prompt)


def _call_openai(
    prompt: str,
    max_tokens: int,
    system_message: Optional[str],
    temperature: float,
    api_key: str,
) -> str:
    """Call OpenAI Chat Completions API."""
    try:
        import httpx  # lightweight, already in requirements

        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})

        response = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
            },
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()

    except Exception as exc:
        # Graceful fallback to demo mode on any API error
        print(f"[ai_client] OpenAI call failed ({exc}), falling back to demo mode.")
        return _demo_response(prompt)
