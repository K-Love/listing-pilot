# KeyProse

> **KeyProse: the AI back office for listing agents.** 5 AI-powered tools for real estate professionals. Generate MLS listings, CMA reports, social posts, email campaigns, and outreach sequences — in seconds, not hours.

The Git repository is still named `listing-pilot`. API routes and environment variables are unchanged.

Planned domains, not registered and not configured in this app: `keyprose.com` and `keyprose.app`. There is no canonical URL setting. After one is purchased, point it at the host and set CORS `allow_origins` in `backend/server.py`. Do not hardcode the domain.

[![CI](https://github.com/YOUR_USERNAME/listing-pilot/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_USERNAME/listing-pilot/actions)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green.svg)](https://fastapi.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](../release/LICENSE.txt)

---

## 🚀 Quick Start (2 minutes)

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/listing-pilot.git
cd listing-pilot

# 2. Install dependencies
pip install -r backend/requirements.txt

# 3. Start the server
python backend/server.py

# 4. Open your browser
open http://localhost:8000
# API docs: http://localhost:8000/docs
```

**That's it.** Works fully offline in demo mode — no API key needed.

---

## 🔑 Enable Live AI (Optional)

```bash
export OPENAI_API_KEY=sk-your-key-here
python backend/server.py
```

The server auto-detects the key and switches from demo mode to live OpenAI generation.

---

## 🛠 Tools Included

| Tool | Endpoint | Description |
|------|----------|-------------|
| **Listing Writer** | `POST /api/listing-writer` | MLS descriptions in 5 tones × 3 lengths |
| **CMA Assistant** | `POST /api/cma` | Market analysis + PDF report |
| **Social Generator** | `POST /api/social` | Instagram, Facebook, Twitter, LinkedIn posts |
| **Email Campaigns** | `POST /api/email` | Buyer/seller/investor drip sequences |
| **Outreach Engine** | `POST /api/outreach` | Multi-touch lead nurturing sequences |

---

## 📁 Project Structure

```
listing-pilot/
├── backend/
│   ├── server.py              # FastAPI app (start here)
│   ├── requirements.txt
│   ├── ai/                    # AI modules (pluggable OpenAI or demo)
│   │   ├── listing_writer.py
│   │   ├── cma_assistant.py
│   │   ├── social_generator.py
│   │   ├── email_generator.py
│   │   └── outreach_engine.py
│   ├── models/schemas.py      # Pydantic request/response models
│   ├── services/
│   │   ├── ai_client.py       # OpenAI wrapper with demo fallback
│   │   └── pdf_generator.py   # CMA PDF generation
│   ├── data/seed_demo_data.sql
│   └── tests/                 # Pytest test suite
├── frontend/
│   ├── index.html             # Landing page
│   └── tools/                 # Tool UIs (listing, cma, social)
├── docs/                      # Documentation
├── demo_data/                 # Sample data files
├── scripts/                   # Helper scripts
└── release/                   # Buyer handoff materials
```

---

## 🐳 Docker Deployment

```dockerfile
# Dockerfile (create in root)
FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "backend/server.py"]
```

```bash
# Build and run
docker build -t keyprose .
docker run -p 8000:8000 -e OPENAI_API_KEY=sk-... keyprose
```

---

## ☁️ Cloud Deployment

### Railway (Recommended — 5 minutes)
```bash
npm install -g @railway/cli
railway login
railway init
railway up
```

### Render
1. Connect your GitHub repo at render.com
2. Set **Build Command**: `pip install -r backend/requirements.txt`
3. Set **Start Command**: `python backend/server.py`
4. Add env var: `OPENAI_API_KEY`

### Fly.io
```bash
fly launch
fly secrets set OPENAI_API_KEY=sk-...
fly deploy
```

### Netlify (static preview + demo API)
`netlify.toml` publishes `frontend/`. That is what removes the production 404, which happens when Netlify publishes the repository root and there is no root `index.html`.

Netlify functions do not run Python. `netlify/functions/api.mjs` answers `/api/*` with a JavaScript demo of the same five endpoints, always in demo mode. For the Python app and optional OpenAI generation, run `python backend/server.py` or the included `Dockerfile` on a Python host.

---

## 🧪 Running Tests

```bash
cd listing-pilot
pip install -r backend/requirements.txt
pytest backend/tests/ -v
```

All tests run in offline/demo mode — no API key required.

---

## ⚙️ Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `OPENAI_API_KEY` | *(none)* | Enables live AI generation |
| `OPENAI_MODEL` | `gpt-4o-mini` | OpenAI model to use |
| `PORT` | `8000` | Server port |
| `PDF_OUTPUT_DIR` | `/tmp` | CMA PDF output directory |

---

## 📖 API Documentation

Interactive docs available at `http://localhost:8000/docs` (Swagger UI) and `http://localhost:8000/redoc`.

See [API_REFERENCE.md](API_REFERENCE.md) for full endpoint documentation with examples.

---

## 🤝 Support & Customization

This is a complete, production-ready codebase. Common customizations:

- **Add authentication**: Add FastAPI middleware or use a service like Clerk/Auth0
- **Connect a database**: Replace the seed SQL with SQLAlchemy + PostgreSQL
- **Custom AI prompts**: Edit the prompt templates in each `backend/ai/*.py` module
- **White-label**: Update branding in `frontend/` HTML files and `frontend/assets/logo.svg`
- **Add more tools**: Follow the pattern in any `backend/ai/` module

---

## 📄 License

MIT License — see [LICENSE.txt](../release/LICENSE.txt)
