# Demo Script — KeyProse

**Total demo time:** ~8 minutes  
**Audience:** Potential buyers, investors, real estate agents  
**Goal:** Show all 5 tools working end-to-end in demo mode

---

## Pre-Demo Setup (2 min before)

```bash
# Start the server
python backend/server.py

# Verify it's running
curl http://localhost:8000/api/health
# Expected: {"status":"ok","version":"1.0.0","ai_mode":"demo"}

# Open browser tabs:
# Tab 1: http://localhost:8000 (landing page)
# Tab 2: http://localhost:8000/tools/listing
# Tab 3: http://localhost:8000/tools/cma
# Tab 4: http://localhost:8000/tools/social
# Tab 5: http://localhost:8000/docs
```

---

## Demo Flow

### [0:00] Opening — Landing Page

> *"This is KeyProse: the AI back office for listing agents. Let me show you what it does."*

- Show the landing page at `http://localhost:8000`
- Point out the 5 tools in the grid
- Note the "Demo Mode Active" banner — **works without any API key**
- Mention: *"Add an OpenAI key and it switches to live AI generation instantly"*

---

### [1:00] Tool 1 — Listing Writer

> *"Let's start with the most-used tool: the Listing Writer."*

Navigate to `http://localhost:8000/tools/listing`

1. Click **"Load Sample Property"** — watch the form fill instantly
2. Change **Tone** to "Luxury"
3. Change **Length** to "Long"
4. Click **"✨ Generate Listing"**
5. Show the result — point out word count badge
6. Click **"📋 Copy to Clipboard"**

> *"In 2 seconds, we have a polished MLS description ready to paste into any listing platform."*

**API demo (optional):**
```bash
curl -X POST http://localhost:8000/api/listing-writer \
  -H "Content-Type: application/json" \
  -d '{"property_details":{"address":"123 Maple St","beds":4,"baths":3,"sqft":2400},"tone":"luxury","length":"medium"}'
```

---

### [2:30] Tool 2 — CMA Assistant

> *"Next, the CMA tool. This is a huge time-saver for agents."*

Navigate to `http://localhost:8000/tools/cma`

1. Click **"Load Sample Data"**
2. Show the 3 comparable sales pre-filled
3. Click **"📊 Generate CMA Report"**
4. Show the valuation results:
   - Estimated value card
   - Price range (low/high)
   - Price per sq ft
   - Market analysis summary
5. Mention: *"With OpenAI enabled, it also generates a downloadable PDF"*

> *"What used to take 30 minutes now takes 10 seconds."*

---

### [4:00] Tool 3 — Social Media Generator

> *"Now let's generate social posts for the same property."*

Navigate to `http://localhost:8000/tools/social`

1. Click **"Load Sample Property"**
2. Set Platform to **"All Platforms"**
3. Set Tone to **"Excited"**
4. Click **"✨ Generate Posts"**
5. Show all 4 platform posts:
   - Instagram (with hashtags)
   - Facebook (longer format)
   - Twitter/X (under 280 chars)
   - LinkedIn (professional tone)
6. Click copy on the Instagram post

> *"Four platform-optimized posts in one click. Each respects the character limits and best practices for that platform."*

---

### [5:30] Tool 4 — Email Campaigns (API Demo)

> *"The email generator creates full drip sequences."*

Show in Swagger UI at `http://localhost:8000/docs`:

1. Expand `POST /api/email`
2. Click "Try it out"
3. Use this payload:
```json
{
  "recipient_type": "buyer",
  "num_emails": 3,
  "context": {
    "first_name": "John",
    "agent_name": "Sarah Johnson",
    "address": "123 Maple Street, Austin TX",
    "price": 650000
  }
}
```
4. Execute and show the 3-email sequence with subjects, bodies, and send delays

> *"A complete 3-email buyer sequence — personalized, with the right timing built in."*

---

### [6:30] Tool 5 — Outreach Engine (API Demo)

> *"Finally, the outreach engine for lead nurturing."*

In Swagger UI:

1. Expand `POST /api/outreach`
2. Try it out with:
```json
{
  "target_list": [
    {"name": "John Smith", "email": "john@email.com", "type": "buyer"},
    {"name": "Sarah Lee", "email": "sarah@email.com", "type": "seller"}
  ],
  "sequence_template": "new_listing"
}
```
3. Show the sequence preview with all steps and timing

---

### [7:30] Closing — Technical Overview

> *"Here's what you're getting with this codebase:"*

- **FastAPI backend** — production-ready, async, auto-documented
- **Pluggable AI** — demo mode works offline; OpenAI drops in with one env var
- **Static frontend** — no build step, works with any CDN
- **Full test suite** — `pytest backend/tests/ -v` runs 30+ tests
- **CI/CD** — GitHub Actions workflow included
- **Docker ready** — one command to containerize
- **Complete docs** — API reference, onboarding guide, demo script

> *"This is a complete, working SaaS product. You can have it live on Railway in under 10 minutes."*

---

## Q&A Talking Points

**"Can I add my own AI model?"**
> Yes — edit `backend/services/ai_client.py`. The `generate_text()` function is the single integration point. Swap in any LLM API.

**"Can I add user accounts / billing?"**
> Yes — the FastAPI backend is standard Python. Add Clerk for auth and Stripe for billing. The ONBOARDING.md has the recommended stack.

**"What's the ongoing cost?"**
> Hosting: ~$5-7/month on Railway or Fly.io. AI: ~$0.001-0.005 per generation with gpt-4o-mini. Very low cost to operate.

**"Is the code clean / maintainable?"**
> Each AI tool is a separate module in `backend/ai/`. Adding a new tool means adding one file and one endpoint. The codebase is intentionally simple and well-documented.
