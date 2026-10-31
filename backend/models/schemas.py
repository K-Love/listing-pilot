"""
Pydantic schemas for all API request/response models.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ─── Listing Writer ───────────────────────────────────────────────────────────

class ListingRequest(BaseModel):
    property_details: Dict[str, Any] = Field(
        ...,
        example={
            "address": "123 Maple Street, Austin, TX 78701",
            "beds": 4,
            "baths": 3,
            "sqft": 2400,
            "lot_size": "0.25 acres",
            "year_built": 2018,
            "price": 650000,
            "features": ["open floor plan", "chef's kitchen", "pool", "3-car garage"],
            "neighborhood": "South Congress",
        },
    )
    tone: str = Field(
        default="professional",
        description="luxury | family | investment | casual | professional",
        example="luxury",
    )
    length: str = Field(
        default="medium",
        description="short (~100 words) | medium (~200 words) | long (~350 words)",
        example="medium",
    )


class ListingResponse(BaseModel):
    listing_text: str
    word_count: Optional[int] = None
    ai_mode: str = "demo"
    notice: Optional[str] = None

    def model_post_init(self, __context: Any) -> None:
        if self.word_count is None:
            self.word_count = len(self.listing_text.split())


# ─── CMA Assistant ────────────────────────────────────────────────────────────

class CompSale(BaseModel):
    address: str
    price: float
    sqft: int
    beds: int
    baths: float
    sold_date: str
    distance_miles: Optional[float] = None
    adjustments: Optional[Dict[str, float]] = None


class CMARequest(BaseModel):
    address: str = Field(..., example="456 Oak Avenue, Austin, TX 78702")
    comps: List[CompSale] = Field(..., min_length=1)
    subject_sqft: Optional[int] = Field(None, example=2200)
    subject_beds: Optional[int] = Field(None, example=3)
    subject_baths: Optional[float] = Field(None, example=2.0)


class CMAResponse(BaseModel):
    cma_summary: str
    estimated_value: float
    price_range_low: float
    price_range_high: float
    price_per_sqft: Optional[float] = None
    cma_pdf_url: Optional[str] = None
    comps_used: int
    ai_mode: str = "demo"
    notice: Optional[str] = None


# ─── Social Generator ─────────────────────────────────────────────────────────

class SocialPost(BaseModel):
    platform: str
    content: str
    hashtags: List[str] = []
    character_count: Optional[int] = None

    def model_post_init(self, __context: Any) -> None:
        if self.character_count is None:
            self.character_count = len(self.content)


class SocialRequest(BaseModel):
    property_id: str = Field(..., example="123-maple-st-austin")
    tone: str = Field(default="excited", example="excited")
    platform: str = Field(
        default="all",
        description="instagram | facebook | twitter | linkedin | all",
        example="all",
    )
    property_details: Optional[Dict[str, Any]] = Field(
        None,
        example={
            "address": "123 Maple Street, Austin, TX 78701",
            "price": 650000,
            "beds": 4,
            "baths": 3,
            "sqft": 2400,
            "highlight": "Stunning pool home in South Congress!",
        },
    )


class SocialResponse(BaseModel):
    posts: List[SocialPost]
    ai_mode: str = "demo"
    notice: Optional[str] = None


# ─── Email Generator ──────────────────────────────────────────────────────────

class EmailMessage(BaseModel):
    subject: str
    body: str
    recipient_type: str
    sequence_step: Optional[int] = None
    send_delay_days: Optional[int] = None


class EmailRequest(BaseModel):
    recipient_type: str = Field(
        ...,
        description="buyer | seller | investor | past_client | cold_lead",
        example="buyer",
    )
    context: Dict[str, Any] = Field(
        ...,
        example={
            "agent_name": "Sarah Johnson",
            "property_address": "123 Maple Street, Austin, TX",
            "price": 650000,
            "open_house_date": "Saturday, July 20th at 2 PM",
            "market_condition": "seller's market",
        },
    )
    num_emails: int = Field(default=3, ge=1, le=7)


class EmailResponse(BaseModel):
    emails: List[EmailMessage]
    ai_mode: str = "demo"
    notice: Optional[str] = None


# ─── Outreach Engine ──────────────────────────────────────────────────────────

class Contact(BaseModel):
    name: str
    email: str
    type: str = "lead"
    notes: Optional[str] = None
    phone: Optional[str] = None


class OutreachRequest(BaseModel):
    target_list: List[Contact] = Field(..., min_length=1)
    sequence_template: str = Field(
        default="new_listing",
        description="new_listing | price_drop | open_house | follow_up | custom",
        example="new_listing",
    )
    custom_message: Optional[str] = None


class OutreachResponse(BaseModel):
    status: str
    preview: str
    total_contacts: int
    sequence_steps: int
    estimated_send_days: int
    ai_mode: str = "demo"
    notice: Optional[str] = None
