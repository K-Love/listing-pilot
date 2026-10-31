"""Live Chat Completions client: configurable host, with demo fallback."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.pop("OPENAI_API_KEY", None)

from fastapi.testclient import TestClient

import server
from services import ai_client

client = TestClient(server.app)

LISTING = {
    "property_details": {
        "address": "123 Maple Street, Austin, TX 78701",
        "beds": 4,
        "baths": 3,
        "sqft": 2400,
        "price": 650000,
        "features": ["pool"],
    },
    "tone": "luxury",
    "length": "short",
}


class _Response:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def test_posts_to_configured_base_and_model(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-secret")
    monkeypatch.setenv("AI_BASE_URL", "https://routellm.abacus.ai/v1/")
    monkeypatch.setenv("AI_MODEL", "route-llm")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4o-mini")
    seen = {}

    def fake_post(url, headers=None, json=None, timeout=None):
        seen["url"] = url
        seen["headers"] = headers
        seen["json"] = json
        seen["timeout"] = timeout
        return _Response({"choices": [{"message": {"content": "  Live listing for you.  "}}]})

    monkeypatch.setattr(ai_client.httpx, "post", fake_post)
    response = client.post("/api/listing-writer", json=LISTING)
    assert response.status_code == 200
    body = response.json()
    assert body["listing_text"] == "Live listing for you."
    assert body["ai_mode"] == "live"
    assert body["word_count"] > 0
    assert seen["url"] == "https://routellm.abacus.ai/v1/chat/completions"
    assert seen["headers"]["Authorization"] == "Bearer sk-test-secret"
    assert seen["json"]["model"] == "route-llm"
    assert seen["json"]["max_tokens"] == 600
    assert seen["json"]["messages"][0]["role"] == "system"
    assert "expert real estate copywriter" in seen["json"]["messages"][0]["content"]
    assert "second person" in seen["json"]["messages"][1]["content"]
    assert "sk-test-secret" not in response.text


def test_openai_model_and_full_completions_url(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-secret")
    monkeypatch.delenv("AI_MODEL", raising=False)
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4o-mini")
    monkeypatch.setenv("AI_BASE_URL", "https://api.openai.com/v1/chat/completions")
    monkeypatch.setenv("AI_MAX_TOKENS", "40")
    seen = {}

    def fake_post(url, headers=None, json=None, timeout=None):
        seen["url"] = url
        seen["json"] = json
        return _Response({"choices": [{"message": {"content": "Short live copy."}}]})

    monkeypatch.setattr(ai_client.httpx, "post", fake_post)
    text = ai_client.generate_text("Write a listing", max_tokens=600)
    assert text == "Short live copy."
    assert seen["url"] == "https://api.openai.com/v1/chat/completions"
    assert seen["json"]["model"] == "gpt-4o-mini"
    assert seen["json"]["max_tokens"] == 40


def test_failure_falls_back_without_logging_the_key(monkeypatch, capsys):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-secret")
    monkeypatch.setenv("AI_BASE_URL", "https://api.openai.com/v1")

    def fake_post(url, headers=None, json=None, timeout=None):
        raise RuntimeError("connect failed sk-test-secret")

    monkeypatch.setattr(ai_client.httpx, "post", fake_post)
    response = client.post("/api/listing-writer", json=LISTING)
    assert response.status_code == 200
    body = response.json()
    assert body["ai_mode"] == "demo"
    assert body["listing_text"] in ai_client._DEMO_RESPONSES
    assert "too long" not in (body.get("notice") or "")
    assert body["notice"]
    assert "sk-test-secret" not in response.text
    captured = capsys.readouterr()
    assert "sk-test-secret" not in captured.out
    assert "sk-test-secret" not in captured.err


def test_overlong_prompt_skips_the_provider(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-secret")
    monkeypatch.setenv("AI_MAX_INPUT_CHARS", "12")
    called = {"n": 0}

    def fake_post(*args, **kwargs):
        called["n"] += 1
        raise AssertionError("provider should not be called")

    monkeypatch.setattr(ai_client.httpx, "post", fake_post)
    response = client.post("/api/listing-writer", json=LISTING)
    body = response.json()
    assert called["n"] == 0
    assert body["ai_mode"] == "demo"
    assert "too long" in body["notice"]
    assert "sk-test-secret" not in response.text


def test_health_reports_host_and_hides_secrets(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-secret")
    monkeypatch.setenv("AI_BASE_URL", "https://sk-test-secret@routellm.abacus.ai/v1")
    response = client.get("/api/health")
    body = response.json()
    assert body["status"] == "ok"
    assert body["ai_mode"] == "live"
    assert body["provider_host"] == "routellm.abacus.ai"
    assert "sk-test-secret" not in response.text
    assert "authorization" not in response.text.lower()


def test_missing_key_does_not_call_provider(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    def fake_post(*args, **kwargs):
        raise AssertionError("provider should not be called")

    monkeypatch.setattr(ai_client.httpx, "post", fake_post)
    ai_client.begin_generation()
    text = ai_client.generate_text("offline please")
    assert text == ai_client._demo_response("offline please")
    assert ai_client.generation_mode() == "demo"


def test_cma_keeps_statistics_and_replaces_narrative(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-secret")
    monkeypatch.setenv("AI_BASE_URL", "https://api.openai.com/v1")

    def fake_post(url, headers=None, json=None, timeout=None):
        prompt = json["messages"][0]["content"]
        assert "licensed real estate appraiser" in prompt
        assert "456 Oak" in prompt
        return _Response({"choices": [{"message": {"content": "Model CMA narrative with a range."}}]})

    monkeypatch.setattr(ai_client.httpx, "post", fake_post)
    response = client.post(
        "/api/cma",
        json={
            "address": "456 Oak Avenue",
            "comps": [
                {
                    "address": "100 Maple St",
                    "price": 635000,
                    "sqft": 2350,
                    "beds": 4,
                    "baths": 3,
                    "sold_date": "2025-05-15",
                }
            ],
        },
    )
    body = response.json()
    assert body["ai_mode"] == "live"
    assert body["cma_summary"] == "Model CMA narrative with a range."
    assert body["estimated_value"] > 0
    assert "sk-test-secret" not in response.text
