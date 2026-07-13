"""
Real Estate AI Business-in-a-Box — FastAPI Server
Start with: python backend/server.py
API docs:   http://localhost:8000/docs
"""

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import sys

# Ensure backend package is importable
sys.path.insert(0, os.path.dirname(__file__))

from models.schemas import (
    ListingRequest, ListingResponse,
    CMARequest, CMAResponse,
    SocialRequest, SocialResponse,
    EmailRequest, EmailResponse,
    OutreachRequest, OutreachResponse,
)
from ai.listing_writer import generate_listing
from ai.cma_assistant import generate_cma
from ai.social_generator import generate_social_posts
from ai.email_generator import generate_emails
from ai.outreach_engine import generate_outreach

app = FastAPI(
    title="Real Estate AI Business-in-a-Box",
    description=(
        "AI-powered tools for real estate professionals: "
        "listing writer, CMA assistant, social media generator, "
        "email campaigns, and outreach automation."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — allow all origins for demo; tighten in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend static files
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.isdir(FRONTEND_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIR, "assets")), name="assets")

    @app.get("/", include_in_schema=False)
    async def serve_index():
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

    @app.get("/tools/{tool_name}", include_in_schema=False)
    async def serve_tool(tool_name: str):
        path = os.path.join(FRONTEND_DIR, "tools", f"{tool_name}.html")
        if os.path.exists(path):
            return FileResponse(path)
        raise HTTPException(status_code=404, detail="Tool not found")


# ─── Endpoints ────────────────────────────────────────────────────────────────

@app.post("/api/listing-writer", response_model=ListingResponse, tags=["Listing Writer"])
async def listing_writer(req: ListingRequest):
    """
    Generate a professional MLS listing description.

    - **property_details**: dict with address, beds, baths, sqft, features, etc.
    - **tone**: 'luxury', 'family', 'investment', 'casual' (default: 'professional')
    - **length**: 'short' (~100 words), 'medium' (~200 words), 'long' (~350 words)
    """
    try:
        result = generate_listing(req.property_details, req.tone, req.length)
        return ListingResponse(listing_text=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/cma", response_model=CMAResponse, tags=["CMA Assistant"])
async def cma_report(req: CMARequest):
    """
    Generate a Comparative Market Analysis report.

    - **address**: subject property address
    - **comps**: list of comparable sales (address, price, sqft, beds, baths, sold_date)
    """
    try:
        result = generate_cma(req.address, req.comps)
        return CMAResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/social", response_model=SocialResponse, tags=["Social Generator"])
async def social_posts(req: SocialRequest):
    """
    Generate platform-optimized social media posts.

    - **property_id**: identifier or address of the property
    - **tone**: 'excited', 'professional', 'casual', 'luxury'
    - **platform**: 'instagram', 'facebook', 'twitter', 'linkedin', 'all'
    """
    try:
        posts = generate_social_posts(req.property_id, req.tone, req.platform, req.property_details)
        return SocialResponse(posts=posts)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/email", response_model=EmailResponse, tags=["Email Generator"])
async def email_campaign(req: EmailRequest):
    """
    Generate targeted email campaigns.

    - **recipient_type**: 'buyer', 'seller', 'investor', 'past_client', 'cold_lead'
    - **context**: dict with property info, agent name, market conditions, etc.
    """
    try:
        emails = generate_emails(req.recipient_type, req.context)
        return EmailResponse(emails=emails)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/outreach", response_model=OutreachResponse, tags=["Outreach Engine"])
async def outreach_sequence(req: OutreachRequest):
    """
    Generate a multi-touch outreach sequence.

    - **target_list**: list of contact dicts (name, email, type, notes)
    - **sequence_template**: 'new_listing', 'price_drop', 'open_house', 'follow_up', 'custom'
    """
    try:
        result = generate_outreach(req.target_list, req.sequence_template, req.custom_message)
        return OutreachResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health", tags=["System"])
async def health():
    """Health check endpoint."""
    return {"status": "ok", "version": "1.0.0", "ai_mode": "openai" if os.getenv("OPENAI_API_KEY") else "demo"}


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=True)
