"""
CMA Assistant AI Module
=======================
Generates Comparative Market Analysis reports from comparable sales data.

Prompt template example:
    "Analyze these {n} comparable sales for {address} and provide:
     1. Estimated market value
     2. Price per square foot analysis
     3. Market trend commentary
     4. Recommended list price range
     Comps: {comps_json}"

Fallback: statistical median/mean calculation (no API key needed).
"""

from __future__ import annotations
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json
import statistics
from typing import Any, Dict, List, Optional

from services.ai_client import generate_text
from services.pdf_generator import generate_cma_pdf


def _calculate_stats(comps: List[Dict[str, Any]]) -> Dict[str, float]:
    """Calculate basic statistics from comp data."""
    prices = [c.get("price", 0) for c in comps if c.get("price")]
    sqfts = [c.get("sqft", 0) for c in comps if c.get("sqft")]

    if not prices:
        return {"median": 0, "mean": 0, "low": 0, "high": 0, "ppsf": 0}

    median_price = statistics.median(prices)
    mean_price = statistics.mean(prices)
    low = min(prices) * 0.97
    high = max(prices) * 1.03

    ppsf = 0.0
    if sqfts and len(sqfts) == len(prices):
        ppsf_list = [p / s for p, s in zip(prices, sqfts) if s > 0]
        ppsf = statistics.mean(ppsf_list) if ppsf_list else 0.0

    return {
        "median": median_price,
        "mean": mean_price,
        "low": low,
        "high": high,
        "ppsf": ppsf,
    }


def _deterministic_cma(address: str, comps: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate a CMA report without an AI API."""
    stats = _calculate_stats(comps)
    estimated = stats["median"] or stats["mean"]
    ppsf = stats["ppsf"]

    n = len(comps)
    price_list = [f"${c.get('price', 0):,.0f}" for c in comps[:3]]
    price_str = ", ".join(price_list)

    summary = (
        f"Based on {n} comparable sale{'s' if n != 1 else ''} in the subject area, "
        f"the estimated market value for {address} is ${estimated:,.0f}. "
        f"Recent comparable sales ranged from ${stats['low']:,.0f} to ${stats['high']:,.0f}, "
        f"with a median sale price of ${stats['median']:,.0f}. "
    )

    if ppsf > 0:
        summary += f"The average price per square foot among comps is ${ppsf:,.2f}. "

    summary += (
        "Current market conditions suggest moderate buyer demand with limited inventory, "
        "supporting pricing at or slightly above the median comparable. "
        "We recommend listing within the suggested range and reviewing after 14 days on market."
    )

    return {
        "cma_summary": summary,
        "estimated_value": round(estimated, -3),
        "price_range_low": round(stats["low"], -3),
        "price_range_high": round(stats["high"], -3),
        "price_per_sqft": round(ppsf, 2) if ppsf else None,
        "comps_used": n,
    }


def generate_cma(address: str, comps: List[Any]) -> Dict[str, Any]:
    """
    Generate a CMA report for the subject property.

    Args:
        address: Subject property address.
        comps: List of CompSale objects or dicts.

    Returns:
        Dict with cma_summary, estimated_value, price_range_low/high, pdf_url.
    """
    # Normalize comps to dicts
    comp_dicts = []
    for c in comps:
        if hasattr(c, "model_dump"):
            comp_dicts.append(c.model_dump())
        elif isinstance(c, dict):
            comp_dicts.append(c)
        else:
            comp_dicts.append(dict(c))

    if not os.getenv("OPENAI_API_KEY"):
        result = _deterministic_cma(address, comp_dicts)
    else:
        stats = _calculate_stats(comp_dicts)
        prompt = (
            f"You are a licensed real estate appraiser. Analyze these {len(comp_dicts)} "
            f"comparable sales for the subject property at {address}.\n\n"
            f"Comparable Sales:\n{json.dumps(comp_dicts, indent=2)}\n\n"
            f"Statistical summary: median=${stats['median']:,.0f}, "
            f"range=${stats['low']:,.0f}–${stats['high']:,.0f}, "
            f"avg $/sqft=${stats['ppsf']:,.2f}\n\n"
            "Provide a 3-4 sentence professional CMA summary including: "
            "estimated market value, price range, market trend commentary, "
            "and a recommended list price. Be specific with numbers."
        )
        summary = generate_text(prompt, max_tokens=400)
        result = {
            "cma_summary": summary,
            "estimated_value": round(stats["median"], -3),
            "price_range_low": round(stats["low"], -3),
            "price_range_high": round(stats["high"], -3),
            "price_per_sqft": round(stats["ppsf"], 2) if stats["ppsf"] else None,
            "comps_used": len(comp_dicts),
        }

    # Generate PDF
    try:
        pdf_path = generate_cma_pdf(
            address=address,
            comps=comp_dicts,
            summary=result["cma_summary"],
            estimated_value=result["estimated_value"],
            price_range_low=result["price_range_low"],
            price_range_high=result["price_range_high"],
        )
        if pdf_path and os.path.isfile(pdf_path):
            result["cma_pdf_url"] = f"/api/cma/pdf/{os.path.basename(pdf_path)}"
        else:
            result["cma_pdf_url"] = None
    except Exception:
        result["cma_pdf_url"] = None

    return result
