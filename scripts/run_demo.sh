#!/usr/bin/env bash
# run_demo.sh — Start the KeyProse demo server
# Usage: bash scripts/run_demo.sh

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "KeyProse: the AI back office for listing agents"
echo "======================================"
echo ""

# Check Python
if ! command -v python3 &>/dev/null; then
  echo "❌ Python 3 is required. Install from https://python.org"
  exit 1
fi

PYTHON=$(command -v python3)
echo "✅ Python: $($PYTHON --version)"

# Install dependencies if needed
if ! $PYTHON -c "import fastapi" 2>/dev/null; then
  echo ""
  echo "📦 Installing dependencies..."
  $PYTHON -m pip install -r backend/requirements.txt --quiet
  echo "✅ Dependencies installed"
fi

# Check for OpenAI key
if [ -n "$OPENAI_API_KEY" ]; then
  echo "✅ OpenAI API key detected — live AI mode enabled"
else
  echo "ℹ️  No OPENAI_API_KEY set — running in demo mode (fully functional)"
  echo "   To enable live AI: export OPENAI_API_KEY=sk-your-key"
fi

echo ""
echo "🚀 Starting server on http://localhost:8000"
echo "   API docs: http://localhost:8000/docs"
echo "   Press Ctrl+C to stop"
echo ""

# Start the server
PORT=${PORT:-8000}
$PYTHON backend/server.py
