"""
Tests for the CMA Assistant AI module.
All tests run in offline/deterministic mode (no API key required).
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.pop("OPENAI_API_KEY", None)

from ai.cma_assistant import generate_cma, _deterministic_cma, _calculate_stats


SAMPLE_COMPS = [
    {"address": "100 Maple St", "price": 635000, "sqft": 2350, "beds": 4, "baths": 3, "sold_date": "2025-05-15"},
    {"address": "200 Oak Ave", "price": 660000, "sqft": 2450, "beds": 4, "baths": 3, "sold_date": "2025-04-28"},
    {"address": "300 Pine Dr", "price": 645000, "sqft": 2380, "beds": 4, "baths": 2.5, "sold_date": "2025-06-01"},
]


class TestCalculateStats:
    def test_basic_stats(self):
        stats = _calculate_stats(SAMPLE_COMPS)
        assert stats["median"] > 0
        assert stats["mean"] > 0
        assert stats["low"] <= stats["median"] <= stats["high"]

    def test_empty_comps(self):
        stats = _calculate_stats([])
        assert stats["median"] == 0

    def test_single_comp(self):
        stats = _calculate_stats([SAMPLE_COMPS[0]])
        assert stats["median"] == 635000

    def test_ppsf_calculated(self):
        stats = _calculate_stats(SAMPLE_COMPS)
        assert stats["ppsf"] > 0


class TestDeterministicCMA:
    def test_returns_dict(self):
        result = _deterministic_cma("123 Maple St, Austin TX", SAMPLE_COMPS)
        assert isinstance(result, dict)

    def test_required_keys(self):
        result = _deterministic_cma("123 Maple St, Austin TX", SAMPLE_COMPS)
        assert "cma_summary" in result
        assert "estimated_value" in result
        assert "price_range_low" in result
        assert "price_range_high" in result
        assert "comps_used" in result

    def test_estimated_value_in_range(self):
        result = _deterministic_cma("123 Maple St, Austin TX", SAMPLE_COMPS)
        assert result["price_range_low"] <= result["estimated_value"] <= result["price_range_high"]

    def test_comps_count(self):
        result = _deterministic_cma("123 Maple St, Austin TX", SAMPLE_COMPS)
        assert result["comps_used"] == 3

    def test_summary_mentions_address(self):
        result = _deterministic_cma("123 Maple St, Austin TX", SAMPLE_COMPS)
        assert "123 Maple St" in result["cma_summary"]


class TestGenerateCMA:
    def test_generate_cma_demo_mode(self):
        result = generate_cma("456 Oak Ave, Austin TX", SAMPLE_COMPS)
        assert isinstance(result, dict)
        assert "cma_summary" in result
        assert result["estimated_value"] > 0

    def test_generate_cma_single_comp(self):
        result = generate_cma("789 Pine Dr", [SAMPLE_COMPS[0]])
        assert isinstance(result, dict)
        assert result["comps_used"] == 1

    def test_generate_cma_returns_pdf_url_key(self):
        result = generate_cma("123 Test St", SAMPLE_COMPS)
        # cma_pdf_url key should exist (may be None if fpdf2 not installed)
        assert "cma_pdf_url" in result
