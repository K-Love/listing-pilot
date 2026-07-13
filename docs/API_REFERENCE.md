# API Reference — Real Estate AI

Base URL: `http://localhost:8000` (local) or your deployed URL.

Interactive docs: `GET /docs` (Swagger UI) | `GET /redoc` (ReDoc)

---

## Authentication

No authentication required in demo mode. To add API key auth, set `API_KEY` env var and include:
```
Authorization: Bearer YOUR_API_KEY
```

---

## Endpoints

### `GET /api/health`

Health check.

**Response:**
```json
{
  "status": "ok",
  "version": "1.0.0",
  "ai_mode": "demo"
}
```

---

### `POST /api/listing-writer`

Generate a professional MLS listing description.

**Request:**
```json
{
  "property_details": {
    "address": "123 Maple Street, Austin, TX 78701",
    "beds": 4,
    "baths": 3,
    "sqft": 2400,
    "lot_size": "0.25 acres",
    "year_built": 2018,
    "price": 650000,
    "features": ["open floor plan", "chef's kitchen", "pool", "3-car garage"],
    "neighborhood": "South Congress"
  },
  "tone": "luxury",
  "length": "medium"
}
```

**Parameters:**
| Field | Type | Options | Default |
|-------|------|---------|---------|
| `tone` | string | `luxury`, `family`, `investment`, `casual`, `professional` | `professional` |
| `length` | string | `short` (~100w), `medium` (~200w), `long` (~350w) | `medium` |

**Response:**
```json
{
  "listing_text": "Welcome to an extraordinary residence where sophistication meets comfort...",
  "word_count": 198
}
```

---

### `POST /api/cma`

Generate a Comparative Market Analysis report.

**Request:**
```json
{
  "address": "456 Oak Avenue, Austin, TX 78702",
  "subject_sqft": 1850,
  "subject_beds": 3,
  "subject_baths": 2.0,
  "comps": [
    {
      "address": "100 Maple St, Austin TX",
      "price": 635000,
      "sqft": 2350,
      "beds": 4,
      "baths": 3,
      "sold_date": "2025-05-15",
      "distance_miles": 0.2
    },
    {
      "address": "200 Oak Ave, Austin TX",
      "price": 660000,
      "sqft": 2450,
      "beds": 4,
      "baths": 3,
      "sold_date": "2025-04-28",
      "distance_miles": 0.4
    }
  ]
}
```

**Response:**
```json
{
  "cma_summary": "Based on 2 comparable sales in the subject area, the estimated market value for 456 Oak Avenue is $648,000...",
  "estimated_value": 648000,
  "price_range_low": 616000,
  "price_range_high": 680000,
  "price_per_sqft": 272.50,
  "cma_pdf_url": "/api/cma/pdf/cma_20250713_143022.pdf",
  "comps_used": 2
}
```

---

### `POST /api/social`

Generate platform-optimized social media posts.

**Request:**
```json
{
  "property_id": "123-maple-st-austin",
  "tone": "excited",
  "platform": "all",
  "property_details": {
    "address": "123 Maple Street, Austin, TX 78701",
    "price": 650000,
    "beds": 4,
    "baths": 3,
    "sqft": 2400,
    "highlight": "Stunning pool home in South Congress!"
  }
}
```

**Parameters:**
| Field | Type | Options | Default |
|-------|------|---------|---------|
| `tone` | string | `excited`, `luxury`, `professional`, `casual` | `excited` |
| `platform` | string | `instagram`, `facebook`, `twitter`, `linkedin`, `all` | `all` |

**Response:**
```json
{
  "posts": [
    {
      "platform": "instagram",
      "content": "✨ JUST LISTED ✨\n\n📍 123 Maple Street, Austin, TX 78701\n🛏 4 Bedrooms | 🛁 3 Bathrooms | 📐 2,400 Sq Ft\n💰 $650,000\n\nStunning pool home in South Congress!...",
      "hashtags": ["#JustListed", "#AustinRealEstate", "#HomeSweetHome"],
      "character_count": 312
    },
    {
      "platform": "twitter",
      "content": "🏡 Just Listed! 4bd/3ba in Austin — $650,000. Stunning pool home! DM for a showing! #JustListed #AustinRealEstate",
      "hashtags": ["#JustListed", "#AustinRealEstate"],
      "character_count": 112
    }
  ]
}
```

---

### `POST /api/email`

Generate targeted email campaign sequences.

**Request:**
```json
{
  "recipient_type": "buyer",
  "num_emails": 3,
  "context": {
    "first_name": "John",
    "agent_name": "Sarah Johnson",
    "agent_phone": "(512) 555-0100",
    "address": "123 Maple Street, Austin, TX",
    "price": 650000,
    "beds": 4,
    "baths": 3,
    "highlight": "stunning pool and chef's kitchen",
    "market_condition": "seller's market"
  }
}
```

**Parameters:**
| Field | Type | Options | Default |
|-------|------|---------|---------|
| `recipient_type` | string | `buyer`, `seller`, `investor`, `past_client`, `cold_lead` | required |
| `num_emails` | integer | 1–7 | `3` |

**Response:**
```json
{
  "emails": [
    {
      "subject": "🏡 New Listing Alert: 123 Maple Street — Just Hit the Market!",
      "body": "Hi John,\n\nI wanted to reach out personally because I just listed a property...",
      "recipient_type": "buyer",
      "sequence_step": 1,
      "send_delay_days": 0
    },
    {
      "subject": "Following up — Did you get a chance to look at 123 Maple Street?",
      "body": "Hi John,\n\nI wanted to follow up on the listing I sent over...",
      "recipient_type": "buyer",
      "sequence_step": 2,
      "send_delay_days": 3
    }
  ]
}
```

---

### `POST /api/outreach`

Generate a multi-touch outreach sequence.

**Request:**
```json
{
  "target_list": [
    {
      "name": "John Smith",
      "email": "john@email.com",
      "type": "buyer",
      "notes": "Looking in 78701, budget $500-700k"
    },
    {
      "name": "Sarah Lee",
      "email": "sarah@email.com",
      "type": "seller"
    }
  ],
  "sequence_template": "new_listing",
  "custom_message": null
}
```

**Parameters:**
| Field | Type | Options | Default |
|-------|------|---------|---------|
| `sequence_template` | string | `new_listing`, `price_drop`, `open_house`, `follow_up`, `custom` | `new_listing` |

**Response:**
```json
{
  "status": "ready",
  "preview": "Outreach sequence for 2 contact(s) starting with John Smith:\n\nStep 1 (Day 0): 'Just Listed — You Need to See This!'...",
  "total_contacts": 2,
  "sequence_steps": 4,
  "estimated_send_days": 14
}
```

---

## Error Responses

All endpoints return standard HTTP error codes:

```json
{
  "detail": "Error description"
}
```

| Code | Meaning |
|------|---------|
| `400` | Bad request / validation error |
| `422` | Unprocessable entity (Pydantic validation) |
| `500` | Internal server error |

---

## Rate Limits

No rate limits in demo mode. When using OpenAI, limits are governed by your OpenAI plan.
