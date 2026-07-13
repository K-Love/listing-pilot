"""
Tests for the Social Media Generator AI module.
All tests run in offline/deterministic mode (no API key required).
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.pop("OPENAI_API_KEY", None)

from ai.social_generator import generate_social_posts, _make_post


SAMPLE_DETAILS = {
    "address": "123 Maple Street, Austin, TX 78701",
    "beds": 4,
    "baths": 3,
    "sqft": 2400,
    "price": 650000,
    "highlight": "Stunning pool home in South Congress!",
}


class TestMakePost:
    def test_instagram_post(self):
        post = _make_post("instagram", "excited", SAMPLE_DETAILS, 0)
        assert post["platform"] == "instagram"
        assert len(post["content"]) > 50
        assert isinstance(post["hashtags"], list)

    def test_twitter_post_exists(self):
        post = _make_post("twitter", "excited", SAMPLE_DETAILS, 0)
        assert post["platform"] == "twitter"
        assert len(post["content"]) > 10

    def test_facebook_post(self):
        post = _make_post("facebook", "professional", SAMPLE_DETAILS, 0)
        assert post["platform"] == "facebook"

    def test_linkedin_post(self):
        post = _make_post("linkedin", "professional", SAMPLE_DETAILS, 0)
        assert post["platform"] == "linkedin"

    def test_character_count_set(self):
        post = _make_post("instagram", "excited", SAMPLE_DETAILS, 0)
        assert post["character_count"] == len(post["content"])


class TestGenerateSocialPosts:
    def test_all_platforms(self):
        posts = generate_social_posts("123-maple", "excited", "all", SAMPLE_DETAILS)
        platforms = {p["platform"] for p in posts}
        assert "instagram" in platforms
        assert "facebook" in platforms
        assert "twitter" in platforms
        assert "linkedin" in platforms

    def test_single_platform(self):
        posts = generate_social_posts("123-maple", "excited", "instagram", SAMPLE_DETAILS)
        assert len(posts) == 1
        assert posts[0]["platform"] == "instagram"

    def test_returns_list(self):
        posts = generate_social_posts("test-property", "professional", "all", SAMPLE_DETAILS)
        assert isinstance(posts, list)
        assert len(posts) > 0

    def test_deterministic_same_input(self):
        p1 = generate_social_posts("abc123", "excited", "instagram", SAMPLE_DETAILS)
        p2 = generate_social_posts("abc123", "excited", "instagram", SAMPLE_DETAILS)
        assert p1[0]["content"] == p2[0]["content"]

    def test_no_property_details_uses_defaults(self):
        posts = generate_social_posts("some-property-id", "excited", "twitter")
        assert len(posts) == 1
        assert isinstance(posts[0]["content"], str)

    def test_luxury_tone(self):
        posts = generate_social_posts("luxury-home", "luxury", "instagram", SAMPLE_DETAILS)
        assert len(posts) == 1
