# Installation Guide

## System Requirements

- Python 3.11 or higher
- pip (Python package manager)
- Git
- 512MB RAM minimum (1GB recommended)
- Any OS: macOS, Linux, Windows (WSL recommended on Windows)

---

## Local Installation

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/listing-pilot.git
cd listing-pilot
```

### 2. Install Dependencies

```bash
pip install -r backend/requirements.txt
```

### 3. Start the Server

```bash
python backend/server.py
```

### 4. Verify Installation

```bash
curl http://localhost:8000/api/health
# Expected: {"status":"ok","version":"1.0.0","ai_mode":"demo"}
```

Open `http://localhost:8000` in your browser.

---

## Enable Live AI

```bash
export OPENAI_API_KEY=sk-your-openai-key-here
python backend/server.py
```

The server auto-detects the key and enables live AI generation.

---

## Production Deployment

### Docker

```bash
# Create Dockerfile in repo root:
cat > Dockerfile << 'EOF'
FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
ENV PORT=8000
CMD ["python", "backend/server.py"]
EOF

# Build and run
docker build -t keyprose .
docker run -p 8000:8000 \
  -e OPENAI_API_KEY=sk-your-key \
  keyprose
```

### Railway (Recommended)

1. Push code to GitHub
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Select your `listing-pilot` repo
4. Add environment variable: `OPENAI_API_KEY`
5. Deploy — Railway auto-detects Python

**Procfile** (create in repo root if needed):
```
web: python backend/server.py
```

### Render

1. Go to [render.com](https://render.com) → New Web Service
2. Connect GitHub repo
3. **Build Command:** `pip install -r backend/requirements.txt`
4. **Start Command:** `python backend/server.py`
5. Add env var: `OPENAI_API_KEY`

### Fly.io

```bash
# Install flyctl: https://fly.io/docs/hands-on/install-flyctl/
fly launch --name keyprose
fly secrets set OPENAI_API_KEY=sk-your-key
fly deploy
```

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | No | *(demo mode)* | OpenAI API key for live generation |
| `OPENAI_MODEL` | No | `gpt-4o-mini` | OpenAI model to use |
| `PORT` | No | `8000` | Server port |
| `PDF_OUTPUT_DIR` | No | `/tmp` | Directory for generated PDFs |

---

## Running Tests

```bash
pytest backend/tests/ -v
```

All 30+ tests run in offline mode — no API key required.

---

## Troubleshooting

**`ModuleNotFoundError: No module named 'fastapi'`**
```bash
pip install -r backend/requirements.txt
```

**`Address already in use`**
```bash
PORT=8001 python backend/server.py
```

**`Permission denied` on scripts**
```bash
chmod +x scripts/run_demo.sh scripts/seed_db.sh
```

**CORS errors in browser**
Add your frontend URL to `allow_origins` in `backend/server.py`.
