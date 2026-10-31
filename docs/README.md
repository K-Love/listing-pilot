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

The server auto-detects the key and switches from demo mode to live generation. `AI_BASE_URL` points at any OpenAI-compatible Chat Completions API (default `https://api.openai.com/v1`). See [Live AI providers](#live-ai-providers) for Abacus.AI RouteLLM and OpenAI.

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

### Netlify (static site + `/api`)
`netlify.toml` publishes `frontend/`. That is what removes the production 404, which happens when Netlify publishes the repository root and there is no root `index.html`.

Netlify functions do not run Python. `netlify/functions/api.mjs` answers `/api/*` with the same five tools. When `OPENAI_API_KEY` is set in **Site configuration → Environment variables**, generations call the Chat Completions URL from `AI_BASE_URL`. When the key is missing, the call fails, the input is too long, or a rate limit is hit, the function returns the built-in sample copy and says so. Do not put the key in the repo.

Stock outreach templates (`new_listing`, `price_drop`, `open_house`, `follow_up`) stay on the built-in sequence, matching `backend/ai/outreach_engine.py`. The `custom` template is the one that calls the model.

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

Set these in the shell for `python backend/server.py`, or in Netlify under **Site configuration → Environment variables** (all scopes you deploy). Never commit the key.

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `OPENAI_API_KEY` | *(none)* | API key for live generation. The name stays `OPENAI_API_KEY` for Abacus too; only the value changes. |
| `AI_BASE_URL` | `https://api.openai.com/v1` | OpenAI-compatible API root. The client calls `{AI_BASE_URL}/chat/completions`. |
| `AI_MODEL` | *(falls through)* | Model id. Wins over `OPENAI_MODEL` when both are set. |
| `OPENAI_MODEL` | `gpt-4o-mini` | Model id used when `AI_MODEL` is unset. |
| `AI_RATE_LIMIT_PER_HOUR` | `10` | Hosted site only. Live generations per IP per hour. `0` disables this cap. |
| `AI_DAILY_CAP` | `200` | Hosted site only. Live generations per UTC day, shared via Netlify Blobs. `0` disables this cap. |
| `AI_MAX_INPUT_CHARS` | `8000` | Largest prompt sent to the model. Over the cap, the response is sample copy. `0` disables. |
| `AI_MAX_TOKENS` | `800` | Upper bound on `max_tokens` sent to the provider. |
| `AI_MAX_BODY_CHARS` | `24000` | Hosted site only. Larger request bodies are rejected. `0` disables. |
| `PORT` | `8000` | Python server port |
| `PDF_OUTPUT_DIR` | `/tmp` | CMA PDF output directory for the Python server |

`GET /api/health` returns `ai_mode` of `live` or `demo` and `provider_host` (hostname only). It never returns the key. Tool responses include `ai_mode` for that result (`live` only when the model produced it) and `notice` when sample copy was used instead.

## Live AI providers

Abacus.AI RouteLLM **is** OpenAI-compatible for this app. The Chat Completions endpoint is documented as a drop-in for the OpenAI SDK: [OpenAI Chat Completions API](https://abacus.ai/help/developer-platform/route-llm/chat-completions/) and [RouteLLM API reference](https://abacus.ai/help/developer-platform/route-llm/).

**Abacus self-serve** (Site configuration → Environment variables):

| Variable | Value |
|----------|--------|
| `OPENAI_API_KEY` | RouteLLM API key from the Abacus.AI platform |
| `AI_BASE_URL` | `https://routellm.abacus.ai/v1` |
| `AI_MODEL` | `route-llm` |

`route-llm` is the documented router and the default model id on that endpoint. The same docs list explicit model ids (`gpt-4o-mini`, `gpt-5.4`, `claude-sonnet-4-6`, and others). Those tables change, and the Chat Completions page says a human-readable name can differ from the API id (their example is `flux-2-pro` vs `flux2_pro`). Confirm an explicit id with `GET https://routellm.abacus.ai/v1/models` before setting `AI_MODEL` to anything other than `route-llm`.

Enterprise Platform uses a workspace host instead of the self-serve host: `https://<workspace>.abacus.ai/v1` (replace `<workspace>` with the id shown on the RouteLLM API page in that workspace). Same key header: `Authorization: Bearer <your_api_key>`.

**OpenAI** ([Create chat completion](https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create/)):

| Variable | Value |
|----------|--------|
| `OPENAI_API_KEY` | OpenAI API key |
| `AI_BASE_URL` | `https://api.openai.com/v1` (optional; this is the default) |
| `OPENAI_MODEL` or `AI_MODEL` | `gpt-4o-mini` if unset |

The code default remains `gpt-4o-mini`, which that reference still accepts on `POST https://api.openai.com/v1/chat/completions`. The model page ([GPT-4o mini](https://developers.openai.com/api/docs/models/gpt-4o-mini)) currently marks `gpt-4o-mini` as deprecated while still listing Chat Completions as supported. Set `OPENAI_MODEL` or `AI_MODEL` to a current Chat Completions model id if you do not want the default.

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
