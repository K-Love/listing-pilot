"""
Outreach Engine AI Module
==========================
Generates multi-touch outreach sequences for real estate lead nurturing.

Prompt template example:
    "Create a {sequence_template} outreach sequence for {n} contacts.
     Generate a {steps}-step sequence with subject lines and preview text.
     Personalize for contact type: {contact_type}."

Fallback: template-based sequence generator (no API key needed).
"""

from __future__ import annotations
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from typing import Any, Dict, List, Optional

from services.ai_client import generate_text


# ─── Sequence templates ───────────────────────────────────────────────────────

_SEQUENCES: Dict[str, Dict[str, Any]] = {
    "new_listing": {
        "steps": 4,
        "days": [0, 3, 7, 14],
        "preview": (
            "Step 1 (Day 0): 'Just Listed — You Need to See This!' — Announce the new listing with key details.\n"
            "Step 2 (Day 3): 'Have You Seen the Photos?' — Share listing photos and open house info.\n"
            "Step 3 (Day 7): 'Still Available — Schedule Your Showing' — Urgency follow-up.\n"
            "Step 4 (Day 14): 'Market Update + Similar Listings' — Keep warm with alternatives."
        ),
    },
    "price_drop": {
        "steps": 3,
        "days": [0, 2, 5],
        "preview": (
            "Step 1 (Day 0): 'Price Reduced — Now's Your Chance!' — Announce price reduction.\n"
            "Step 2 (Day 2): 'Don't Miss This Deal' — Reinforce value at new price.\n"
            "Step 3 (Day 5): 'Final Call — Offer Deadline Approaching' — Create urgency."
        ),
    },
    "open_house": {
        "steps": 3,
        "days": [0, 1, 2],
        "preview": (
            "Step 1 (Day 0): 'You're Invited — Open House This Weekend!' — Save the date.\n"
            "Step 2 (Day 1): 'Tomorrow! Open House Reminder + Directions' — Day-before reminder.\n"
            "Step 3 (Day 2): 'Thank You for Visiting / Sorry We Missed You' — Post-event follow-up."
        ),
    },
    "follow_up": {
        "steps": 5,
        "days": [0, 3, 7, 14, 30],
        "preview": (
            "Step 1 (Day 0): 'Great Meeting You!' — Personalized follow-up after first contact.\n"
            "Step 2 (Day 3): 'Resources I Promised' — Deliver value (market report, guides).\n"
            "Step 3 (Day 7): 'Checking In — Any Questions?' — Soft check-in.\n"
            "Step 4 (Day 14): 'New Listings That Match Your Criteria' — Curated property alerts.\n"
            "Step 5 (Day 30): 'Monthly Market Update' — Long-term nurture."
        ),
    },
    "custom": {
        "steps": 3,
        "days": [0, 5, 10],
        "preview": (
            "Step 1 (Day 0): Custom introduction message.\n"
            "Step 2 (Day 5): Custom follow-up with value add.\n"
            "Step 3 (Day 10): Custom closing / CTA."
        ),
    },
}


def generate_outreach(
    target_list: List[Any],
    sequence_template: str = "new_listing",
    custom_message: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate a multi-touch outreach sequence.

    Args:
        target_list: List of Contact objects or dicts.
        sequence_template: Sequence type — new_listing | price_drop | open_house | follow_up | custom
        custom_message: Optional custom message for 'custom' template.

    Returns:
        Dict with status, preview, total_contacts, sequence_steps, estimated_send_days.
    """
    # Normalize contacts
    contacts = []
    for c in target_list:
        if hasattr(c, "model_dump"):
            contacts.append(c.model_dump())
        elif isinstance(c, dict):
            contacts.append(c)
        else:
            contacts.append({"name": str(c), "email": "", "type": "lead"})

    template_key = sequence_template.lower() if sequence_template.lower() in _SEQUENCES else "custom"
    seq = _SEQUENCES[template_key]

    n_contacts = len(contacts)
    n_steps = seq["steps"]
    days = seq["days"]
    estimated_days = max(days) if days else 0

    if not os.getenv("OPENAI_API_KEY") or template_key != "custom":
        preview = seq["preview"]
        if custom_message and template_key == "custom":
            preview = f"Custom sequence based on: '{custom_message[:100]}...'\n\n" + preview

        # Personalize preview with first contact name
        if contacts:
            first = contacts[0].get("name", "your leads")
            preview = f"Outreach sequence for {n_contacts} contact(s) starting with {first}:\n\n" + preview

        return {
            "status": "ready",
            "preview": preview,
            "total_contacts": n_contacts,
            "sequence_steps": n_steps,
            "estimated_send_days": estimated_days,
        }

    # AI-powered custom sequence
    contact_summary = ", ".join(
        f"{c.get('name', 'Contact')} ({c.get('type', 'lead')})" for c in contacts[:5]
    )
    if len(contacts) > 5:
        contact_summary += f" and {len(contacts) - 5} more"

    prompt = (
        f"Create a {n_steps}-step real estate outreach sequence for these contacts: {contact_summary}.\n"
        f"Template type: {sequence_template}.\n"
        f"{'Custom message context: ' + custom_message if custom_message else ''}\n"
        f"For each step, provide: Day number, Subject line, 1-sentence preview.\n"
        "Format: 'Step N (Day X): Subject — Preview'"
    )

    preview = generate_text(prompt, max_tokens=400)

    return {
        "status": "ready",
        "preview": preview,
        "total_contacts": n_contacts,
        "sequence_steps": n_steps,
        "estimated_send_days": estimated_days,
    }
