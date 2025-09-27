# Repository File Audit and Purpose

This document summarizes the key files and folders in the repository, what they do, and whether they are required for the current (v2.1) implementation.

Status legend:
- ✅ Required now
- 🟡 Optional/legacy-compatible
- ❌ Safe to remove (suggested cleanup)

## Root
- README.md — Project overview, quick start, and docs links. ✅
- requirements.txt — Python deps for backend. ✅
- run.py — Main entry point (factory-based app). ✅
- .env, .env.example — Environment config. ✅ (example optional)
- LICENSE — MIT license. ✅
- logs/ — Runtime logs folder. ✅ (created at runtime)
- tests/, test_api.py — Unit tests. 🟡 (keep; useful for CI)

## Backend (legacy)
- backend/app.py — Legacy monolithic Flask app with working endpoints; kept for compatibility. 🟡
- backend/db.py — Legacy JSON/Mongo helpers used by legacy app. 🟡
- backend/ml_model.py — Recommendation logic used by legacy routes. 🟡
- backend/distance_matrix.py, migrate_data.py, verify_migration.py — Utilities/scripts predominantly for legacy flows. 🟡

Notes: Primary runtime uses the `app/` package. Legacy backend remains callable via `python -m backend.app` if needed.

## New Application (primary)
- app/main.py — Flask app factory, blueprint registration, health, static serving, legacy aliases. ✅
- app/config.py — Environment and app configuration (port 3000 by default). ✅
- app/api/ — API blueprints:
  - __init__.py — Registers routes under `/api`. ✅
  - internships.py — `/api/internships` (Atlas-only runtime). ✅
  - recommendations.py — Personalized and by-internship recommendations. ✅
  - profiles.py — Profile create/get endpoints. ✅
  - auth.py — Signup/login/logout (+ status). ✅
- app/core/ — Core services (db manager, ML engine, etc.). ✅
- app/utils/ — Logging, response helpers, error handling. ✅
- app/models/ — Data model placeholders. 🟡 (kept for growth)

## Frontend
- frontend/pages/index.html — Main app UI (search + AI right panel). ✅
- frontend/pages/profile.html — Profile management with skills/city selectors. ✅
- frontend/pages/login.html — Auth UI. ✅
- frontend/assets/js/app.js — Primary client logic for index page. ✅
- frontend/assets/css/style.css — Styles. ✅
- frontend/app.js — Older/alternate script not referenced by pages. 🟡 (can remove if unused)
- frontend/components/, frontend/shared/ — Placeholders for growth. 🟡

## Data
- data/internships.json — Source data for seeding/migration. 🟡 (not used at runtime in Atlas-only mode)
- data/profiles.json — Legacy dev/migration only. 🟡
- data/login-info.json — Legacy dev/migration only. 🟡
- data/skills_synonyms.json — Legacy dev/migration only. 🟡

## Docs
- docs/README.md — Docs index. ✅
- docs/api/API_REFERENCE.md — Endpoint details; updated to 127.0.0.1:3000. ✅
- docs/architecture/LEGACY_VS_NEW_COMPARISON.md — Explains migration; still useful for context. ✅
- docs/architecture/DETAILED_FLOW_ANALYSIS.md — Request/data flow details (new vs legacy). ✅
- docs/guides/DEVELOPMENT_GUIDE.md — Setup, run, and troubleshooting. ✅
- docs/guides/RESTRUCTURE_GUIDE.md — Summary of restructuring. ✅
- docs/guides/ISSUES_RESOLVED.md — Running log of fixes. 🟡
- docs/guides/SUCCESS_SUMMARY.md — Summary of improvements. 🟡

## Recommendations for Cleanup (optional)
- Remove `frontend/app.js` once confirmed unused by any page. Currently, `frontend/pages/index.html` loads `../assets/js/app.js`.
- Consider moving legacy backend into `legacy/` or marking clearly in README if you plan to maintain only the new app.
- Consolidate duplicate docs and ensure dates/versions are kept in sync (done for core files).

## Operational Notes
- Default dev endpoint is http://127.0.0.1:3000 with same-origin API and static serving via `app/main.py`.
- Atlas-only mode: set `DISABLE_JSON_FALLBACK=True` in `.env`; runtime does not read/write JSON files.
- Profiles are upserted; recommendations support both personalized and similar-by-internship modes.
