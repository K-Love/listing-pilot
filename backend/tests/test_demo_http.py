"""HTTP demo API: FastAPI routes and the Netlify function handler."""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.pop("OPENAI_API_KEY", None)

from fastapi.testclient import TestClient

import server
from demo_http import handle_api, normalize_path

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "netlify", "functions"))
from api import handler  # noqa: E402


client = TestClient(server.app)

LISTING = {
    "property_details": {
        "address": "123 Maple Street, Austin, TX 78701",
        "beds": 4,
        "baths": 3,
        "sqft": 2400,
        "price": 650000,
        "neighborhood": "South Congress",
        "features": ["pool", "chef's kitchen"],
    },
    "tone": "luxury",
    "length": "short",
}

COMPS = {
    "address": "456 Oak Avenue, Austin, TX 78702",
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
}


def test_health_demo_mode():
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["ai_mode"] == "demo"


def test_homepage_links_every_tool():
    response = client.get("/")
    assert response.status_code == 200
    html = response.text
    for path in ("/tools/listing", "/tools/cma", "/tools/social", "/tools/email", "/tools/outreach"):
        assert path in html
    assert "https://github.com/K-Love/listing-pilot" in html
    assert "</html>" in html.lower()


@pytest.mark.parametrize(
    "path",
    ["/tools/listing", "/tools/cma", "/tools/social", "/tools/email", "/tools/outreach"],
)
def test_tool_pages_render(path):
    response = client.get(path)
    assert response.status_code == 200
    assert "<form" in response.text or "generate" in response.text.lower()


def test_unknown_page_uses_branded_404():
    response = client.get("/missing-page")
    assert response.status_code == 404
    assert "Page not found" in response.text


def test_listing_email_outreach_round_trip():
    listing = client.post("/api/listing-writer", json=LISTING)
    assert listing.status_code == 200
    assert "Maple" in listing.json()["listing_text"] or "bedroom" in listing.json()["listing_text"].lower()

    emails = client.post(
        "/api/email",
        json={
            "recipient_type": "buyer",
            "context": {"agent_name": "Sarah Johnson", "address": "123 Maple Street", "first_name": "Alex"},
            "num_emails": 2,
        },
    )
    assert emails.status_code == 200
    assert len(emails.json()["emails"]) == 2
    assert "Sarah Johnson" in emails.json()["emails"][0]["body"]

    outreach = client.post(
        "/api/outreach",
        json={
            "target_list": [{"name": "Alex Rivera", "email": "alex@example.com", "type": "buyer"}],
            "sequence_template": "open_house",
        },
    )
    assert outreach.status_code == 200
    body = outreach.json()
    assert body["status"] == "ready"
    assert body["total_contacts"] == 1
    assert "Alex Rivera" in body["preview"]


def test_cma_pdf_downloads():
    created = client.post("/api/cma", json=COMPS)
    assert created.status_code == 200
    payload = created.json()
    assert payload["estimated_value"] > 0
    assert payload["cma_pdf_url"]
    downloaded = client.get(payload["cma_pdf_url"])
    assert downloaded.status_code == 200
    assert downloaded.content.startswith(b"%PDF")


def test_netlify_handler_matches_demo_api_and_inlines_pdf(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-should-not-be-used")
    health = handler({"httpMethod": "GET", "path": "/api/health"}, None)
    assert health["statusCode"] == 200
    assert '"ai_mode": "demo"' in health["body"]
    assert os.environ.get("OPENAI_API_KEY") == "sk-should-not-be-used"

    cma = handler(
        {
            "httpMethod": "POST",
            "path": "/.netlify/functions/api/cma",
            "body": '{"address":"456 Oak Avenue","comps":[{"address":"100 Maple St","price":635000,"sqft":2350,"beds":4,"baths":3,"sold_date":"2025-05-15"}]}',
        },
        None,
    )
    assert cma["statusCode"] == 200
    assert "data:application/pdf;base64," in cma["body"]


def test_normalize_path_accepts_function_splat():
    assert normalize_path("/.netlify/functions/api/listing-writer") == "/api/listing-writer"
    assert normalize_path("/api/health/") == "/api/health"


def test_handler_rejects_bad_json():
    result = handle_api("POST", "/api/listing-writer", {})
    assert result.status == 422
    response = handler({"httpMethod": "POST", "path": "/api/email", "body": "{"}, None)
    assert response["statusCode"] == 400
