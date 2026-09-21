# PRD — Ririn / Si-Scoring Kalteng (branch `balanga`)

## Original problem statement
Clone `https://github.com/rianianggun/Ririn.git` (branch `balanga`), install all dependencies (backend `requirements.txt` + frontend `package.json`), create the gitignored `.env` files, and run the app in **minimal mode** (no Stripe / LLM keys). Verify backend responds on :8001, frontend loads the Login page, and Admin/Penilai/Verifikator/Perangkat dashboards are reachable after auth.

## What the app is
Sistem Penilaian Tipologi Perangkat Daerah (PP 18/2016) for Pemprov Kalimantan Tengah. Roles: `admin`, `perangkat` (submits data), `verifikator` (verifies), `penilai` (scores → Tipe A/B/C). FastAPI + Motor/MongoDB backend, React 19 + CRACO + Tailwind/shadcn frontend, JWT auth (PyJWT + bcrypt), openpyxl exports, optional Emergent object storage + LLM scoring helpers, optional Stripe.

## Architecture / setup done (2026-06)
- Repo copied into `/app` (backend → `/app/backend`, frontend → `/app/frontend`), preserving `/app/.git` and `/app/.emergent`.
- Backend deps: all of `requirements.txt` installed except `emergentintegrations==0.2.0` and the `litellm` wheel, which conflict when pinned together — both were already present in the environment (0.2.0 / 1.80.0) and `server.py` does not import them directly, so nothing was stubbed.
- Frontend deps: `yarn install --frozen-lockfile` succeeded incl. `@emergentbase/*` dev tooling (no fallback needed).
- `/app/backend/.env`: `MONGO_URL`, `DB_NAME=ririn`, `CORS_ORIGINS`, `FRONTEND_URL` (used by CORS middleware), `JWT_SECRET`, `ADMIN_EMAIL=admin@ririn.go.id`, `ADMIN_PASSWORD=Admin123!`. Note: `EmailStr` rejects `.local` TLDs, hence `.go.id`.
- `/app/frontend/.env`: `REACT_APP_BACKEND_URL` (preview URL), `WDS_SOCKET_PORT=443`.
- Services run via supervisor (backend :8001, frontend :3000, mongodb). `seed()` on startup creates admin + 3 demo users, indicators, and the current-year period.
- Minimal mode: `EMERGENT_LLM_KEY` absent → "Storage init failed: 400" is logged at startup and file upload / AI scoring are dormant; Stripe absent.

## Verification (testing agent, iteration_4.json) — all passed
- Login for all 4 roles returns token + role; `/api/auth/me` works with Bearer, 403 without.
- Login page renders; each role lands on its dashboard (Panel Administrator / Dashboard Penilai / Dashboard Verifikator / Dashboard Perangkat Daerah); "Keluar" returns to `/login`.

## Re-setup from `rianianggun/balanga1` branch `clone1` (2026-09)
- Cloned to `/tmp/balanga1`, diffed vs `/app`: source identical except 2 backend test files; synced via rsync (excluding `.git`, `.emergent`, `.env`, `node_modules`). Repo has no `yarn.lock`; kept existing `/app/frontend/yarn.lock` (package.json identical).
- Backend: `pip install -r requirements.txt` (minus `emergentintegrations`/`litellm` pins, already present in venv). Frontend: `rm -rf node_modules && yarn install --frozen-lockfile` (first attempt hit EEXIST symlink race; clean retry succeeded, 945 pkgs).
- `.env` files already present incl. `EMERGENT_LLM_KEY` and `SEED_DEMO=true` → startup logs "Storage initialized" + "Demo submissions seeded" (406 PP 18/2016 indicators loaded).
- Verified: `POST /api/auth/login` admin returns JWT; frontend compiled, `/login` renders Balanga login page. Credentials in `/app/memory/test_credentials.md`.

## Backlog / next steps
- P1: Add `EMERGENT_LLM_KEY` to enable object storage (evidence uploads) and AI scoring helpers.
- P1: Add Stripe keys if payments are needed.
- P2: Set `FRONTEND_URL` to the production domain on deploy.
