"""Request dispatch for the FastAPI server and the Docker image.

The public Netlify preview cannot run this Python package. It serves a
JavaScript demo of the same routes from netlify/functions/api.mjs.
"""

from __future__ import annotations

import os
import tempfile
from typing import Any, Optional

from pydantic import ValidationError

from models.schemas import (
    CMARequest,
    CMAResponse,
    EmailRequest,
    EmailResponse,
    ListingRequest,
    ListingResponse,
    OutreachRequest,
    OutreachResponse,
    SocialRequest,
    SocialResponse,
)
from ai.cma_assistant import generate_cma
from ai.email_generator import generate_emails
from ai.listing_writer import generate_listing
from ai.outreach_engine import generate_outreach
from ai.social_generator import generate_social_posts


class ApiResult:
    def __init__(self, status: int, body: Any, media_type: str = "application/json"):
        self.status = status
        self.body = body
        self.media_type = media_type


def normalize_path(path: str) -> str:
    """Reduce a browser path or a Netlify function path to `/api/...`."""
    path = (path or "").split("?")[0]
    marker = "/api/"
    idx = path.find(marker)
    if idx >= 0:
        path = path[idx:]
    else:
        token = "/functions/api"
        found = path.find(token)
        if found >= 0:
            rest = path[found + len(token):]
            path = "/api" + (rest if rest.startswith("/") else f"/{rest}")
        elif path and not path.startswith("/api"):
            path = "/api/" + path.lstrip("/")
    if len(path) > 1:
        path = path.rstrip("/")
    return path or "/"


def handle_api(method: str, path: str, payload: Optional[Any]) -> ApiResult:
    method = (method or "GET").upper()
    path = normalize_path(path)

    if method == "OPTIONS":
        return ApiResult(204, {})

    try:
        if path == "/api/health" and method == "GET":
            return ApiResult(
                200,
                {
                    "status": "ok",
                    "version": "1.0.0",
                    "ai_mode": "openai" if os.getenv("OPENAI_API_KEY") else "demo",
                },
            )

        if path == "/api/listing-writer" and method == "POST":
            req = ListingRequest.model_validate(payload or {})
            text = generate_listing(req.property_details, req.tone, req.length)
            return ApiResult(200, ListingResponse(listing_text=text).model_dump())

        if path == "/api/cma" and method == "POST":
            req = CMARequest.model_validate(payload or {})
            result = generate_cma(req.address, req.comps)
            return ApiResult(200, CMAResponse(**result).model_dump())

        if path == "/api/social" and method == "POST":
            req = SocialRequest.model_validate(payload or {})
            posts = generate_social_posts(
                req.property_id, req.tone, req.platform, req.property_details
            )
            return ApiResult(200, SocialResponse(posts=posts).model_dump())

        if path == "/api/email" and method == "POST":
            req = EmailRequest.model_validate(payload or {})
            emails = generate_emails(req.recipient_type, req.context, req.num_emails)
            return ApiResult(200, EmailResponse(emails=emails).model_dump())

        if path == "/api/outreach" and method == "POST":
            req = OutreachRequest.model_validate(payload or {})
            result = generate_outreach(
                req.target_list, req.sequence_template, req.custom_message
            )
            return ApiResult(200, OutreachResponse(**result).model_dump())

        if path.startswith("/api/cma/pdf/") and method == "GET":
            return _read_pdf(path.rsplit("/", 1)[-1])

        return ApiResult(404, {"detail": "Not found"})
    except ValidationError as exc:
        return ApiResult(422, {"detail": exc.errors()})
    except Exception as exc:
        return ApiResult(500, {"detail": str(exc)})


def _read_pdf(filename: str) -> ApiResult:
    safe = filename.replace(".", "").replace("_", "")
    if (
        not filename.endswith(".pdf")
        or "/" in filename
        or "\\" in filename
        or ".." in filename
        or not safe.isalnum()
    ):
        return ApiResult(400, {"detail": "Invalid filename"})

    directory = os.getenv("PDF_OUTPUT_DIR", tempfile.gettempdir())
    full = os.path.abspath(os.path.join(directory, filename))
    if os.path.dirname(full) != os.path.abspath(directory):
        return ApiResult(400, {"detail": "Invalid filename"})
    if not os.path.isfile(full):
        return ApiResult(404, {"detail": "PDF not found"})

    with open(full, "rb") as handle:
        return ApiResult(200, handle.read(), "application/pdf")
