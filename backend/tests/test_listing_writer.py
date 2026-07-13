"""
Tests for the Listing Writer AI module.
All tests run in offline/deterministic mode (no API key required).
"""

import os
import sys
import pytest

# Ensure backend is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Force demo mode
os.environ.pop("OPENAI_API_KEY", None)

from ai.listing_writer import generate_listing, _deterministic_listing


SAMPLE_PROPERTY = {
    "address": "123 Maple Street, Austin, TX 78701",
    "beds": 4,
    "baths": 3,
    "sqft": 2400,
    "year_built": 2018,
    "price": 650000,
    "features": ["open floor plan", "chef's kitchen", "pool"],
    "neighborhood": "South Congress",
}


class TestDeterministicListing:
    def test_returns_string(self):
        result = _deterministic_listing(SAMPLE_PROPERTY, "professional", "medium")
        assert isinstance(result, str)
        assert len(result) > 50

    def test_short_length_is_shorter(self):
        short = _deterministic_listing(SAMPLE_PROPERTY, "professional", "short")
        long = _deterministic_listing(SAMPLE_PROPERTY, "professional", "long")
        assert len(short) < len(long)

    def test_contains_property_details(self):
        result = _deterministic_listing(SAMPLE_PROPERTY, "professional", "medium")
        # Should mention beds or baths
        assert "4" in result or "bedroom" in result.lower()

    def test_luxury_tone(self):
        result = _deterministic_listing(SAMPLE_PROPERTY, "luxury", "medium")
        assert isinstance(result, str)
        assert len(result) > 50

    def test_family_tone(self):
        result = _deterministic_listing(SAMPLE_PROPERTY, "family", "medium")
        assert isinstance(result, str)

    def test_investment_tone(self):
        result = _deterministic_listing(SAMPLE_PROPERTY, "investment", "short")
        assert isinstance(result, str)

    def test_unknown_tone_falls_back(self):
        result = _deterministic_listing(SAMPLE_PROPERTY, "unknown_tone_xyz", "short")
        assert isinstance(result, str)
        assert len(result) > 10

    def test_minimal_property_details(self):
        result = _deterministic_listing({}, "professional", "short")
        assert isinstance(result, str)


class TestGenerateListing:
    def test_generate_listing_demo_mode(self):
        result = generate_listing(SAMPLE_PROPERTY, "professional", "medium")
        assert isinstance(result, str)
        assert len(result) > 50

    def test_generate_listing_all_lengths(self):
        for length in ["short", "medium", "long"]:
            result = generate_listing(SAMPLE_PROPERTY, "professional", length)
            assert isinstance(result, str), f"Failed for length={length}"

    def test_generate_listing_all_tones(self):
        for tone in ["luxury", "family", "investment", "casual", "professional"]:
            result = generate_listing(SAMPLE_PROPERTY, tone, "short")
            assert isinstance(result, str), f"Failed for tone={tone}"

    def test_deterministic_same_input_same_output(self):
        r1 = generate_listing(SAMPLE_PROPERTY, "professional", "medium")
        r2 = generate_listing(SAMPLE_PROPERTY, "professional", "medium")
        assert r1 == r2
