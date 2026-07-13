# Transfer Instructions

This document outlines the steps to transfer the **Real Estate AI Business-in-a-Box** codebase to the buyer.

---

## What's Included

- ✅ Full source code (GitHub repository)
- ✅ All documentation (README, API reference, onboarding guide, demo script)
- ✅ Test suite (30+ tests, all passing)
- ✅ CI/CD pipeline (GitHub Actions)
- ✅ Demo data (sample listings, CMA data, brand kit)
- ✅ Release zip (`listing-pilot.zip`)

---

## Transfer Steps

### Step 1: GitHub Repository Transfer

1. Seller goes to: `https://github.com/SELLER_USERNAME/listing-pilot/settings`
2. Scroll to **"Danger Zone"** → **"Transfer"**
3. Enter buyer's GitHub username
4. Confirm transfer

**Alternative:** Buyer forks the repo, seller deletes their copy after confirmation.

### Step 2: Verify Transfer

Buyer confirms:
```bash
git clone https://github.com/BUYER_USERNAME/listing-pilot.git
cd listing-pilot
python backend/server.py
# Visit http://localhost:8000 — should work immediately
```

### Step 3: Update Repository References

After transfer, update these files with your GitHub username:
- `docs/README.md` — replace `YOUR_USERNAME` with your GitHub username
- `.github/workflows/ci.yml` — badge URL (optional)

### Step 4: Deploy to Your Infrastructure

Follow [INSTALLATION.md](INSTALLATION.md) to deploy to Railway, Render, or Fly.io.

### Step 5: Configure Your OpenAI Key

```bash
# On your deployment platform, set:
OPENAI_API_KEY=sk-your-key-here
```

---

## Assets Checklist

| Asset | Location | Status |
|-------|----------|--------|
| Source code | GitHub repo | ✅ Included |
| Backend (FastAPI) | `backend/` | ✅ Included |
| Frontend (HTML/CSS/JS) | `frontend/` | ✅ Included |
| AI modules | `backend/ai/` | ✅ Included |
| Test suite | `backend/tests/` | ✅ Included |
| Documentation | `docs/` | ✅ Included |
| Demo data | `demo_data/` | ✅ Included |
| CI/CD pipeline | `.github/workflows/` | ✅ Included |
| Release zip | `release/listing-pilot.zip` | ✅ Included |

---

## Post-Transfer Support

The codebase is fully documented and self-contained. For questions:

1. Read `docs/ONBOARDING.md` — covers all common setup scenarios
2. Read `docs/API_REFERENCE.md` — full endpoint documentation
3. Run `pytest backend/tests/ -v` — verify everything works
4. Check `http://localhost:8000/docs` — interactive API explorer

---

## License

This software is transferred under the MIT License. See [LICENSE.txt](LICENSE.txt).

The buyer receives full rights to:
- Use commercially
- Modify and customize
- Resell or white-label
- Deploy to any infrastructure

No ongoing royalties or attribution required (though appreciated).
