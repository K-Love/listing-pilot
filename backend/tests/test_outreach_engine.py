"""
Tests for the Outreach Engine AI module.
All tests run in offline/deterministic mode (no API key required).
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.pop("OPENAI_API_KEY", None)

from ai.outreach_engine import generate_outreach


SAMPLE_CONTACTS = [
    {"name": "John Smith", "email": "john@email.com", "type": "buyer", "notes": "Looking in 78701"},
    {"name": "Sarah Lee", "email": "sarah@email.com", "type": "seller", "notes": "Wants to sell by Sept"},
    {"name": "Mike Chen", "email": "mike@invest.com", "type": "investor", "notes": "6%+ cap rate"},
]


class TestGenerateOutreach:
    def test_new_listing_sequence(self):
        result = generate_outreach(SAMPLE_CONTACTS, "new_listing")
        assert result["status"] == "ready"
        assert result["total_contacts"] == 3
        assert result["sequence_steps"] > 0

    def test_price_drop_sequence(self):
        result = generate_outreach(SAMPLE_CONTACTS[:1], "price_drop")
        assert result["status"] == "ready"
        assert result["sequence_steps"] == 3

    def test_open_house_sequence(self):
        result = generate_outreach(SAMPLE_CONTACTS, "open_house")
        assert result["status"] == "ready"
        assert result["sequence_steps"] == 3

    def test_follow_up_sequence(self):
        result = generate_outreach(SAMPLE_CONTACTS, "follow_up")
        assert result["status"] == "ready"
        assert result["sequence_steps"] == 5

    def test_custom_sequence(self):
        result = generate_outreach(SAMPLE_CONTACTS, "custom", "Special promotion for VIP clients")
        assert result["status"] == "ready"

    def test_unknown_template_falls_back(self):
        result = generate_outreach(SAMPLE_CONTACTS, "nonexistent_template")
        assert result["status"] == "ready"

    def test_required_keys_present(self):
        result = generate_outreach(SAMPLE_CONTACTS, "new_listing")
        assert "status" in result
        assert "preview" in result
        assert "total_contacts" in result
        assert "sequence_steps" in result
        assert "estimated_send_days" in result

    def test_preview_is_string(self):
        result = generate_outreach(SAMPLE_CONTACTS, "new_listing")
        assert isinstance(result["preview"], str)
        assert len(result["preview"]) > 20

    def test_single_contact(self):
        result = generate_outreach([SAMPLE_CONTACTS[0]], "follow_up")
        assert result["total_contacts"] == 1

    def test_contact_name_in_preview(self):
        result = generate_outreach(SAMPLE_CONTACTS, "new_listing")
        assert "John Smith" in result["preview"]

    def test_estimated_days_positive(self):
        result = generate_outreach(SAMPLE_CONTACTS, "follow_up")
        assert result["estimated_send_days"] >= 0
