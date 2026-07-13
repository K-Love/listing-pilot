#!/usr/bin/env bash
# seed_db.sh — Seed the SQLite demo database
# Usage: bash scripts/seed_db.sh

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

DB_FILE="${DB_FILE:-listing_pilot.db}"

echo "🌱 Seeding demo database: $DB_FILE"

if ! command -v sqlite3 &>/dev/null; then
  echo "❌ sqlite3 is required. Install with: brew install sqlite (macOS) or apt install sqlite3 (Linux)"
  exit 1
fi

sqlite3 "$DB_FILE" < backend/data/seed_demo_data.sql

echo "✅ Database seeded successfully!"
echo ""
echo "Tables created:"
sqlite3 "$DB_FILE" ".tables"
echo ""
echo "Sample data:"
echo "  Properties: $(sqlite3 "$DB_FILE" 'SELECT COUNT(*) FROM properties;')"
echo "  Contacts:   $(sqlite3 "$DB_FILE" 'SELECT COUNT(*) FROM contacts;')"
echo "  Campaigns:  $(sqlite3 "$DB_FILE" 'SELECT COUNT(*) FROM campaigns;')"
