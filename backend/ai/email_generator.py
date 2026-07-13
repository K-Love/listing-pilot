"""
Email Generator AI Module
==========================
Generates targeted real estate email campaigns for different recipient types.

Prompt template example:
    "Write a {recipient_type} real estate email from agent {agent_name}
     about the property at {address}. Include subject line.
     Tone: professional but warm. Include a clear CTA."

Fallback: template-based email sequences (no API key needed).
"""

from __future__ import annotations
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from typing import Any, Dict, List

from services.ai_client import generate_text


# ─── Email templates ──────────────────────────────────────────────────────────

_TEMPLATES: Dict[str, List[Dict[str, Any]]] = {
    "buyer": [
        {
            "subject": "🏡 New Listing Alert: {address} — Just Hit the Market!",
            "body": (
                "Hi {first_name},\n\n"
                "I wanted to reach out personally because I just listed a property that I think "
                "you're going to love.\n\n"
                "📍 {address}\n"
                "🛏 {beds} Bedrooms | 🛁 {baths} Bathrooms | 📐 {sqft} Sq Ft\n"
                "💰 Listed at ${price:,}\n\n"
                "This home features {highlight} and is located in one of Austin's most sought-after "
                "neighborhoods. Homes like this don't stay on the market long — especially in today's "
                "{market_condition}.\n\n"
                "I'd love to schedule a private showing for you. Are you available this weekend?\n\n"
                "Best,\n{agent_name}\n{agent_phone}"
            ),
            "sequence_step": 1,
            "send_delay_days": 0,
        },
        {
            "subject": "Following up — Did you get a chance to look at {address}?",
            "body": (
                "Hi {first_name},\n\n"
                "I wanted to follow up on the listing I sent over earlier this week — "
                "{address}.\n\n"
                "I've had a lot of interest in this property, and I'd hate for you to miss out. "
                "If you'd like to schedule a showing or have any questions, just reply to this email "
                "or give me a call at {agent_phone}.\n\n"
                "Also, if this particular home isn't quite right, I have a few other properties "
                "coming to market soon that might be a better fit. Let me know what you're looking for!\n\n"
                "Best,\n{agent_name}"
            ),
            "sequence_step": 2,
            "send_delay_days": 3,
        },
        {
            "subject": "Last chance — {address} has an offer pending",
            "body": (
                "Hi {first_name},\n\n"
                "Quick update: {address} has received significant interest and we may have an offer "
                "coming in soon.\n\n"
                "If you've been on the fence, now is the time to act. I can arrange a showing "
                "as early as today.\n\n"
                "Even if this one doesn't work out, I'm actively searching for properties that "
                "match your criteria. Let's connect this week to make sure you're first in line "
                "for the next great listing.\n\n"
                "Call or text me anytime: {agent_phone}\n\n"
                "Best,\n{agent_name}"
            ),
            "sequence_step": 3,
            "send_delay_days": 7,
        },
    ],
    "seller": [
        {
            "subject": "Your home could sell for ${estimated_value:,} in today's market",
            "body": (
                "Hi {first_name},\n\n"
                "I've been tracking the real estate market in your neighborhood closely, and I wanted "
                "to share some exciting news: homes similar to yours are selling for top dollar right now.\n\n"
                "Based on recent comparable sales, your home at {address} could be worth "
                "${estimated_value:,} or more in today's {market_condition}.\n\n"
                "I'd love to provide you with a free, no-obligation Comparative Market Analysis (CMA) "
                "so you can see exactly what your home is worth. This takes about 20 minutes and "
                "could be worth thousands of dollars to you.\n\n"
                "Would you be open to a quick call this week?\n\n"
                "Best,\n{agent_name}\n{agent_phone}"
            ),
            "sequence_step": 1,
            "send_delay_days": 0,
        },
        {
            "subject": "Free home valuation for {address} — expires Friday",
            "body": (
                "Hi {first_name},\n\n"
                "I reached out earlier about your home's value in today's market. "
                "I wanted to follow up because I've completed a preliminary analysis and "
                "the numbers are very encouraging.\n\n"
                "I'd like to walk you through the full report at your convenience. "
                "There's no obligation — just valuable information to help you make "
                "an informed decision about your largest asset.\n\n"
                "Reply to this email or call me at {agent_phone} to schedule a time.\n\n"
                "Best,\n{agent_name}"
            ),
            "sequence_step": 2,
            "send_delay_days": 4,
        },
    ],
    "investor": [
        {
            "subject": "Investment opportunity: {address} — {cap_rate}% cap rate",
            "body": (
                "Hi {first_name},\n\n"
                "I have an investment property that I think deserves your attention.\n\n"
                "📍 {address}\n"
                "💰 Asking: ${price:,}\n"
                "📈 Estimated Cap Rate: {cap_rate}%\n"
                "🏠 {beds}bd/{baths}ba | {sqft} sqft\n\n"
                "This property offers strong rental income potential in a high-demand corridor. "
                "Recent renovations reduce near-term capex, and the location commands premium rents.\n\n"
                "Full pro forma and rent roll available upon request. "
                "Serious inquiries only — this one won't last.\n\n"
                "Best,\n{agent_name}\n{agent_phone}"
            ),
            "sequence_step": 1,
            "send_delay_days": 0,
        },
    ],
    "past_client": [
        {
            "subject": "Checking in — how's the new home treating you?",
            "body": (
                "Hi {first_name},\n\n"
                "It's been a while since we worked together, and I just wanted to check in "
                "and see how you're enjoying your home!\n\n"
                "The market has shifted quite a bit since you purchased, and I wanted to let you "
                "know that your home has likely appreciated significantly. If you're ever curious "
                "about your current home value, I'm happy to run a quick analysis — no strings attached.\n\n"
                "Also, if you know anyone who's thinking about buying or selling, I'd be honored "
                "by the referral. My business is built on relationships like ours.\n\n"
                "Hope all is well!\n\n{agent_name}\n{agent_phone}"
            ),
            "sequence_step": 1,
            "send_delay_days": 0,
        },
    ],
    "cold_lead": [
        {
            "subject": "Austin real estate market update — {month} {year}",
            "body": (
                "Hi {first_name},\n\n"
                "I wanted to share a quick market update for Austin real estate this month.\n\n"
                "📊 Key stats:\n"
                "• Median home price: ${median_price:,}\n"
                "• Average days on market: {avg_dom} days\n"
                "• Inventory: {inventory_level}\n\n"
                "Whether you're thinking about buying, selling, or just staying informed, "
                "I'm here as a resource. No pressure — just good information.\n\n"
                "Feel free to reply with any questions or to get a personalized market report "
                "for your specific neighborhood.\n\n"
                "Best,\n{agent_name}\n{agent_phone}"
            ),
            "sequence_step": 1,
            "send_delay_days": 0,
        },
    ],
}


def _fill_template(template: str, context: Dict[str, Any]) -> str:
    """Fill template placeholders with context values."""
    defaults = {
        "first_name": "there",
        "agent_name": "Your Agent",
        "agent_phone": "(512) 555-0100",
        "address": "the property",
        "beds": 3,
        "baths": 2,
        "sqft": "1,800",
        "price": 550000,
        "highlight": "modern finishes and a great location",
        "market_condition": "seller's market",
        "estimated_value": 600000,
        "cap_rate": "6.2",
        "month": "July",
        "year": "2025",
        "median_price": 485000,
        "avg_dom": 18,
        "inventory_level": "low (2.1 months supply)",
    }
    merged = {**defaults, **context}

    try:
        return template.format(**merged)
    except (KeyError, ValueError):
        # If format fails, return template as-is
        return template


def generate_emails(
    recipient_type: str,
    context: Dict[str, Any],
    num_emails: int = 3,
) -> List[Dict[str, Any]]:
    """
    Generate a targeted email sequence.

    Args:
        recipient_type: buyer | seller | investor | past_client | cold_lead
        context: Template variables (agent_name, address, price, etc.)
        num_emails: Number of emails to generate (1–7)

    Returns:
        List of email dicts with subject, body, sequence_step, send_delay_days.
    """
    rtype = recipient_type.lower().replace(" ", "_")
    templates = _TEMPLATES.get(rtype, _TEMPLATES["buyer"])

    if not os.getenv("OPENAI_API_KEY"):
        emails = []
        for tmpl in templates[:num_emails]:
            emails.append({
                "subject": _fill_template(tmpl["subject"], context),
                "body": _fill_template(tmpl["body"], context),
                "recipient_type": recipient_type,
                "sequence_step": tmpl.get("sequence_step", len(emails) + 1),
                "send_delay_days": tmpl.get("send_delay_days", 0),
            })
        return emails

    # AI-powered generation
    emails = []
    for i in range(min(num_emails, 5)):
        step = i + 1
        delay = [0, 3, 7, 14, 21][i]
        prompt = (
            f"Write email #{step} in a {num_emails}-email sequence for a {recipient_type} "
            f"in real estate. Context: {context}. "
            f"This is sent {delay} days after the first contact. "
            "Include: subject line (prefix with 'Subject: '), then the email body. "
            "Keep it under 200 words. Professional but warm tone. Clear CTA."
        )
        raw = generate_text(prompt, max_tokens=350)
        lines = raw.strip().split("\n")
        subject = lines[0].replace("Subject:", "").strip() if lines else f"Follow-up #{step}"
        body = "\n".join(lines[1:]).strip() if len(lines) > 1 else raw

        emails.append({
            "subject": subject,
            "body": body,
            "recipient_type": recipient_type,
            "sequence_step": step,
            "send_delay_days": delay,
        })

    return emails
