# Buyer Onboarding Guide

Welcome! This guide walks you through everything you need to launch **KeyProse** after purchase.

---

## Step 1: Get the Code

```bash
# Clone from GitHub (repo transferred to you)
git clone https://github.com/YOUR_USERNAME/listing-pilot.git
cd listing-pilot
```

---

## Step 2: Run Locally (5 minutes)

```bash
# Install Python dependencies
pip install -r backend/requirements.txt

# Start the server
python backend/server.py

# Visit: http://localhost:8000
# API docs: http://localhost:8000/docs
```

✅ **Works immediately in demo mode** — no API key needed.

---

## Step 3: Enable Live AI

1. Get an OpenAI API key at [platform.openai.com](https://platform.openai.com)
2. Set the environment variable:
   ```bash
   export OPENAI_API_KEY=sk-your-key-here
   ```
3. Restart the server — it auto-detects the key.

For Abacus.AI RouteLLM or another OpenAI-compatible host, also set `AI_BASE_URL` and `AI_MODEL`. The Netlify site reads the same variables under **Site configuration → Environment variables**. Exact values and doc links are in the [README](README.md#live-ai-providers).

**Default model:** `gpt-4o-mini` (override with `OPENAI_MODEL` or `AI_MODEL`)
**Cost estimate:** ~$0.001–0.005 per listing generation on that default model

---

## Step 4: Deploy to Production

### Option A: Railway (Easiest — ~5 min)

1. Create account at [railway.app](https://railway.app)
2. Connect your GitHub repo
3. Railway auto-detects Python and deploys
4. Add env var: `OPENAI_API_KEY`
5. Your app is live at `https://your-app.railway.app`

**Cost:** ~$5/month for hobby tier

### Option B: Render

1. Create account at [render.com](https://render.com)
2. New → Web Service → Connect GitHub repo
3. **Build Command:** `pip install -r backend/requirements.txt`
4. **Start Command:** `python backend/server.py`
5. Add env var: `OPENAI_API_KEY`

**Cost:** Free tier available (spins down after inactivity)

### Option C: Fly.io

```bash
# Install flyctl
curl -L https://fly.io/install.sh | sh

# Deploy
fly launch
fly secrets set OPENAI_API_KEY=sk-...
fly deploy
```

**Cost:** ~$3-7/month

### Option D: VPS (DigitalOcean, Linode, etc.)

```bash
# On your server
git clone https://github.com/YOUR_USERNAME/listing-pilot.git
cd listing-pilot
pip install -r backend/requirements.txt

# Run with systemd or screen
export OPENAI_API_KEY=sk-...
python backend/server.py

# Or use gunicorn for production
pip install gunicorn
gunicorn backend.server:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

---

## Step 5: Customize Your Brand

### Update the Logo
Replace `frontend/assets/logo.svg` with your logo.

### Update Colors
Edit the CSS variables in each HTML file:
```css
:root {
  --primary: #1e50a0;  /* Change to your brand color */
  --accent: #f59e0b;   /* Change to your accent color */
}
```

### Update the App Name
Search and replace "KeyProse" across the frontend HTML files. The wordmark is `frontend/assets/logo.svg` and the favicon is `frontend/assets/favicon.svg`.

### Custom Domain
Point your domain to your deployment and update CORS settings in `backend/server.py`. `keyprose.com` is the planned primary domain and `keyprose.app` is the alternate; neither is registered or set in this repo:
```python
allow_origins=["https://yourdomain.com"]
```

---

## Step 6: Add Authentication (Optional)

The API is open by default. To add simple API key auth:

```python
# In backend/server.py, add:
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Security

security = HTTPBearer()
API_KEY = os.getenv("API_KEY", "demo-key")

async def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    if credentials.credentials != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return credentials.credentials
```

---

## Step 7: Connect a Database (Optional)

The demo uses SQLite seed data. For production, add PostgreSQL:

```bash
pip install sqlalchemy asyncpg
```

```python
# Add to backend/server.py
from sqlalchemy.ext.asyncio import create_async_engine
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./listing_pilot.db")
```

---

## Recommended Tech Stack for Scaling

| Layer | Recommendation |
|-------|---------------|
| Hosting | Railway or Fly.io |
| Database | PostgreSQL (Supabase free tier) |
| Auth | Clerk.dev or Auth0 |
| Payments | Stripe (add subscription billing) |
| Email sending | Resend or SendGrid |
| Monitoring | Sentry (free tier) |

---

## Support Resources

- **API Docs:** `http://your-app/docs`
- **Test Suite:** `pytest backend/tests/ -v`
- **Demo Script:** See [DEMO_SCRIPT.md](DEMO_SCRIPT.md)
- **Installation:** See [../release/INSTALLATION.md](../release/INSTALLATION.md)

---

## Common Issues

**Port already in use:**
```bash
PORT=8001 python backend/server.py
```

**Module not found errors:**
```bash
cd listing-pilot
pip install -r backend/requirements.txt
python backend/server.py  # Run from repo root
```

**CORS errors in browser:**
The server allows all origins by default. If you restrict origins, add your frontend URL to `allow_origins` in `server.py`.
