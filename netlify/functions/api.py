"""Netlify Function that serves the demo API on the static buyer site.

The public preview always runs in demo mode so a site-wide OPENAI_API_KEY
cannot be billed by anonymous visitors. Self-hosting uses backend/server.py.
"""

from __future__ import annotations

import base64
import json
import os
import sys
import tempfile


def _candidate_backends():
    here = os.path.dirname(os.path.abspath(__file__))
    return [
        os.path.abspath(os.path.join(here, "vendor", "backend")),
        os.path.abspath(os.path.join(here, "..", "..", "backend")),
        os.path.abspath(os.path.join(here, "backend")),
        "/var/task/backend",
        "/var/task/vendor/backend",
        "/var/task/netlify/functions/vendor/backend",
    ]


def _add_backend_to_path():
    for path in _candidate_backends():
        if os.path.isdir(os.path.join(path, "ai")):
            if path not in sys.path:
                sys.path.insert(0, path)
            return path
    return None


_BACKEND = _add_backend_to_path()
_IMPORT_ERROR = None
try:
    if _BACKEND is None:
        raise ImportError(
            "Could not find the backend package. Looked in: "
            + ", ".join(_candidate_backends())
        )
    from demo_http import handle_api
except Exception as exc:  # pragma: no cover - only hits a broken bundle
    handle_api = None
    _IMPORT_ERROR = exc


def _headers(content_type="application/json"):
    return {
        "Content-Type": content_type,
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
        "Cache-Control": "no-store",
    }


def _json(status, payload):
    return {
        "statusCode": status,
        "headers": _headers(),
        "body": json.dumps(payload),
    }


def _inline_pdf(body):
    url = body.get("cma_pdf_url") or ""
    if not url.startswith("/api/cma/pdf/"):
        return body
    filename = url.rsplit("/", 1)[-1]
    directory = os.getenv("PDF_OUTPUT_DIR", tempfile.gettempdir())
    full = os.path.join(directory, filename)
    if not os.path.isfile(full):
        cloned = dict(body)
        cloned["cma_pdf_url"] = None
        return cloned
    with open(full, "rb") as handle:
        encoded = base64.b64encode(handle.read()).decode("ascii")
    cloned = dict(body)
    cloned["cma_pdf_url"] = "data:application/pdf;base64," + encoded
    return cloned


def handler(event, context):
    saved_key = os.environ.pop("OPENAI_API_KEY", None)
    try:
        return _handler(event or {})
    finally:
        if saved_key is not None:
            os.environ["OPENAI_API_KEY"] = saved_key


def _handler(event):
    if handle_api is None:
        return _json(500, {"detail": f"Demo API failed to load: {_IMPORT_ERROR}"})

    method = event.get("httpMethod") or "GET"
    if method.upper() == "OPTIONS":
        return _json(204, {})

    raw = event.get("body") or ""
    if event.get("isBase64Encoded") and raw:
        raw = base64.b64decode(raw).decode("utf-8")

    payload = None
    if raw:
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            return _json(400, {"detail": "Invalid JSON"})

    result = handle_api(method, event.get("path") or "", payload)
    if result.media_type == "application/pdf":
        return {
            "statusCode": result.status,
            "headers": {
                **_headers("application/pdf"),
                "Content-Disposition": "attachment; filename=cma-report.pdf",
            },
            "isBase64Encoded": True,
            "body": base64.b64encode(result.body).decode("ascii"),
        }

    body = result.body if isinstance(result.body, dict) else {"detail": "ok"}
    if result.status == 200 and "cma_pdf_url" in body:
        body = _inline_pdf(body)
    return _json(result.status, body)
