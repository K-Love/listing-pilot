"""
Social Media Generator AI Module
=================================
Generates platform-optimized social media posts for real estate listings.

Prompt template example:
    "Write a {tone} Instagram post for a {beds}-bed, {baths}-bath home
     at {address} listed at ${price}. Include relevant hashtags.
     Keep under 2200 characters. End with a call to action."

Fallback: template-based generator with platform-specific formatting.
"""

from __future__ import annotations
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import hashlib
from typing import Any, Dict, List, Optional

from services.ai_client import generate_text


# ─── Platform configs ─────────────────────────────────────────────────────────

_PLATFORM_LIMITS = {
    "twitter": 280,
    "instagram": 2200,
    "facebook": 63206,
    "linkedin": 3000,
}

_HASHTAG_SETS = {
    "luxury": ["#LuxuryRealEstate", "#DreamHome", "#LuxuryLiving", "#HighEnd", "#EstateLife"],
    "excited": ["#JustListed", "#NewListing", "#HomeSweetHome", "#RealEstate", "#ForSale"],
    "professional": ["#RealEstate", "#PropertyForSale", "#HomeBuying", "#RealEstateAgent"],
    "casual": ["#HomeGoals", "#HouseHunting", "#NewHome", "#RealEstate", "#MovingDay"],
}

_LOCATION_HASHTAGS = ["#AustinRealEstate", "#ATXHomes", "#AustinTX", "#TexasRealEstate"]


def _make_post(
    platform: str,
    tone: str,
    details: Dict[str, Any],
    seed: int,
) -> Dict[str, Any]:
    """Generate a single platform post deterministically."""
    address = details.get("address", "this stunning property")
    beds = details.get("beds", 3)
    baths = details.get("baths", 2)
    sqft = details.get("sqft", 1800)
    price = details.get("price", 0)
    highlight = details.get("highlight", f"{beds} bed / {baths} bath / {sqft:,} sqft")
    price_str = f"${price:,}" if price else "Call for price"

    templates = {
        "twitter": [
            f"🏡 Just Listed! {beds}bd/{baths}ba in Austin — {price_str}. {highlight} DM for a showing! #JustListed #AustinRealEstate",
            f"✨ New to market! {beds}-bed home at {price_str}. {highlight} 📍 Austin, TX. Schedule your tour today! #RealEstate #ForSale",
            f"🔑 Don't miss this one! {beds}bd/{baths}ba, {sqft:,} sqft — {price_str}. Link in bio for details. #AustinHomes #NewListing",
        ],
        "instagram": [
            (
                f"✨ JUST LISTED ✨\n\n"
                f"📍 {address}\n"
                f"🛏 {beds} Bedrooms | 🛁 {baths} Bathrooms | 📐 {sqft:,} Sq Ft\n"
                f"💰 {price_str}\n\n"
                f"{highlight}\n\n"
                "This incredible home won't last long! Swipe to see all the photos and "
                "DM me to schedule your private showing. 🏡\n\n"
                "#JustListed #AustinRealEstate #HomeSweetHome #DreamHome #RealEstate "
                "#ForSale #AustinTX #NewListing #HouseHunting #LuxuryHomes"
            ),
            (
                f"🏡 Your dream home just hit the market!\n\n"
                f"📍 {address}\n"
                f"✅ {beds} beds | {baths} baths | {sqft:,} sqft\n"
                f"💵 {price_str}\n\n"
                f"Featuring: {highlight}\n\n"
                "Comment below or send a DM to book your tour! 👇\n\n"
                "#NewListing #AustinHomes #RealEstate #HomeBuying #ForSale #ATX"
            ),
        ],
        "facebook": [
            (
                f"🏡 NEW LISTING ALERT!\n\n"
                f"Just listed this beautiful {beds}-bedroom, {baths}-bathroom home "
                f"in Austin, TX!\n\n"
                f"📍 {address}\n"
                f"📐 {sqft:,} square feet\n"
                f"💰 Listed at {price_str}\n\n"
                f"✨ Highlights: {highlight}\n\n"
                "This home is move-in ready and won't last long in today's market. "
                "Contact me today to schedule a private showing or learn more!\n\n"
                "👉 Like this post and share with anyone who might be looking for their perfect home!"
            ),
        ],
        "linkedin": [
            (
                f"Excited to announce a new listing in Austin, TX! 🏡\n\n"
                f"Property: {beds}BR / {baths}BA | {sqft:,} sqft\n"
                f"Address: {address}\n"
                f"Price: {price_str}\n\n"
                f"Key features: {highlight}\n\n"
                "If you or someone in your network is looking for a quality home in the Austin market, "
                "I'd love to connect. Reach out directly to schedule a showing or discuss the current market.\n\n"
                "#RealEstate #AustinRealEstate #PropertyForSale #HomeBuying"
            ),
        ],
    }

    posts_for_platform = templates.get(platform, templates["instagram"])
    content = posts_for_platform[seed % len(posts_for_platform)]

    hashtags = _HASHTAG_SETS.get(tone, _HASHTAG_SETS["excited"])[:3] + _LOCATION_HASHTAGS[:2]

    return {
        "platform": platform,
        "content": content,
        "hashtags": hashtags,
        "character_count": len(content),
    }


def generate_social_posts(
    property_id: str,
    tone: str = "excited",
    platform: str = "all",
    property_details: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Generate social media posts for a property listing.

    Args:
        property_id: Property identifier or address.
        tone: Post tone — excited | professional | casual | luxury
        platform: Target platform — instagram | facebook | twitter | linkedin | all
        property_details: Optional property info dict.

    Returns:
        List of post dicts with platform, content, hashtags.
    """
    details = property_details or {
        "address": property_id,
        "beds": 3,
        "baths": 2,
        "sqft": 1800,
        "price": 550000,
        "highlight": "Open floor plan, updated kitchen, large backyard",
    }

    seed = int(hashlib.md5(property_id.encode()).hexdigest(), 16)

    if platform == "all":
        platforms = ["instagram", "facebook", "twitter", "linkedin"]
    else:
        platforms = [platform.lower()]

    if not os.getenv("OPENAI_API_KEY"):
        return [_make_post(p, tone, details, seed) for p in platforms]

    # AI-powered generation
    posts = []
    for plat in platforms:
        limit = _PLATFORM_LIMITS.get(plat, 2200)
        prompt = (
            f"Write a {tone} {plat} post for a real estate listing.\n"
            f"Property: {details.get('beds')}bd/{details.get('baths')}ba, "
            f"{details.get('sqft', 0):,} sqft at {details.get('address', property_id)}.\n"
            f"Price: ${details.get('price', 0):,}\n"
            f"Highlight: {details.get('highlight', 'beautiful home')}\n"
            f"Platform character limit: {limit}\n"
            f"Include relevant hashtags. End with a call to action."
        )
        content = generate_text(prompt, max_tokens=400)
        hashtags = _HASHTAG_SETS.get(tone, _HASHTAG_SETS["excited"])[:3]
        posts.append({
            "platform": plat,
            "content": content,
            "hashtags": hashtags,
            "character_count": len(content),
        })

    return posts
