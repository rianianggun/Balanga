# Setup log — `rianianggun/Balanga` branch `Clone2` → `/app` (2026-09-25)

## Source
- Repo: https://github.com/rianianggun/Balanga.git, branch `Clone2` (capital C, verified via `git branch --show-current`).
- Commit: `9567035` ("Auto-generated changes").
- Method: clone `--branch Clone2 --single-branch` → `/tmp/balanga_src`, then `rsync -a --delete` into `/app` excluding `.git/`, `.emergent/`, `backend/.env`, `frontend/.env`, `node_modules/`, `.ruff_cache/`. Old `.env` files backed up to `/tmp/envbak/` (ephemeral).

## Diff vs previous `/app` content
- **Assumption in the plan was wrong**: `/app` was NOT the `balanga1@clone1` project. It was a bare Emergent template (single commit `af312cc "Initial commit"`, no git remote, template `server.py`, empty `memory/test_credentials.md`, `.env` with `DB_NAME="test_database"`, no `JWT_SECRET`).
- Consequence: `/app/.git` has **no remote** configured — "Save to GitHub" will need a target; nothing pointed to `balanga1`. Not changed, per instruction.
- Added by sync: `backend/{ai_scoring,demo_seed,exports,surat}.py`, `backend/data/*.xlsx`, `backend/tests/`, `backend/pytest.ini`, `backend_test.py`, `design_guidelines.json`, full `frontend/src/{pages,components,context,lib}`, `frontend/public/latar.jpg`, `memory/PRD.md`, `test_reports/*`, `.gitconfig`.
- Removed by `--delete`: template `/app/yarn.lock` (root) and template `/app/frontend/yarn.lock` (repo ships **no** `yarn.lock`).

## Environment variables
`/app/backend/.env` (not committed):
- Preserved: `MONGO_URL`, `DB_NAME="test_database"` (template value kept as instructed; repo README/PRD suggests `balanga`), `CORS_ORIGINS`.
- Added: `JWT_SECRET` (new random), `FRONTEND_URL` (= preview URL; `server.py` uses it for `CORSMiddleware.allow_origins`, default would be `http://localhost:3000` and block the preview frontend), `ADMIN_EMAIL=admin@ririn.go.id`, `ADMIN_PASSWORD=Admin123!` (matches `backend_test.py` / `test_setup_verification.py`), `SEED_DEMO=true`, `EMERGENT_LLM_KEY` (from Emergent env via internal tool; not written anywhere else).
- Env vars read by backend (`server.py`, `ai_scoring.py`): `MONGO_URL`, `DB_NAME`, `INTEGRATION_PROXY_URL` (optional, pod env), `EMERGENT_LLM_KEY`, `JWT_SECRET`, `FRONTEND_URL`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`, `SEED_DEMO`. **No Stripe variable is read anywhere** in the backend → `STRIPE_API_KEY` intentionally not added (no consumer). No empty required vars remain.
- `/app/frontend/.env`: untouched (`REACT_APP_BACKEND_URL`, `WDS_SOCKET_PORT`, `ENABLE_HEALTH_CHECK`).

## Dependencies
Backend (venv `/root/.venv`, Python 3.11.16 → pandas 3.0.5 / numpy 2.4.6 OK):
- `pip install -r requirements.txt --extra-index-url $EMERGENT_PYPI_INDEX` → **ResolutionImpossible**: `emergentintegrations==0.2.0` depends on `litellm @ <same wheel URL>` and pip refuses two direct-URL requirements for one package.
- Workaround: installed `requirements.txt` minus the `emergentintegrations`/`litellm` lines, then `pip install emergentintegrations==0.2.0 --extra-index-url ...` separately. `litellm 1.80.0` (exact wheel) was already in venv.
- **No runtime pins changed.** Final: fastapi 0.110.1, starlette 0.37.2, pydantic 2.13.5, motor 3.3.1, pymongo 4.6.3, emergentintegrations 0.2.0 (venv had 0.2.1, downgraded to pin), litellm 1.80.0, pandas 3.0.5 (venv had 3.0.6, downgraded to pin), google-genai 2.23.0. `pip check`: no broken requirements. `requirements.txt` untouched.
- Dev tools (black/mypy/flake8/isort/pytest) installed at pinned versions, no changes needed.

Frontend (Yarn 1.22.22):
- `yarn install --frozen-lockfile` not applicable: **repo has no `frontend/yarn.lock`**. Ran plain `yarn install` → success in 63s, new `yarn.lock` generated at `/app/frontend/yarn.lock` (untracked; commit it if you want reproducible installs).
- `@emergentbase/overlay@0.1.29` and `@emergentbase/visual-edits@1.0.13` from `assets.emergent.sh` downloaded fine (only a harmless `vite>=6` peer warning).

## Smoke test results
Backend (after `supervisorctl restart backend`):
- Startup log clean: `Indikator PP 18/2016 dimuat dari Excel: 406`, `Storage initialized`, `Demo submissions seeded`, `Application startup complete`. Seed ran against existing `test_database` without duplicate errors.
- `GET /api/` → **404** (no root route exists in this codebase; `GET /api/indicators` → 401 without token confirms routing works). Not "fixed" — code unchanged.
- `POST /api/auth/login` admin → 200, JWT returned, role `admin`.

Frontend (after `supervisorctl restart frontend`): `webpack compiled successfully`, `/login` renders "Balanga" login page, 0 console errors.

`backend_test.py` (against preview URL): **52/54 passed**. Failed as-is:
- `Notifications have event items` — only period notifications present for the test user (data-dependent).
- `Submit submission` — HTTP 400 (data/state-dependent; not investigated, no code touched).

`pytest tests/` (root): no tests collected (only `__init__.py`).
`pytest backend/tests/` (pytest.ini `-n 2 --dist loadscope`, targets `localhost:8001`): **25 passed, 17 errors**. All 17 errors are `401` at login in `test_pp18_e2e.py` / `test_pp18_iter3.py`, which hardcode admin `riani.anggun.adp@gmail.com / Admin@2026` — that account is not seeded (env admin is `admin@ririn.go.id`). Environment/credential mismatch, not a code failure. `test_setup_verification.py` and `test_iter5_backend.py` fully pass.

## Reminders / known gaps
- **Rotate `EMERGENT_LLM_KEY`** — it was exposed in chat earlier. Key lives only in `/app/backend/.env`.
- Git: no remote on `/app/.git`; branch content is untracked in the local repo. Set remote before "Save to GitHub".
- `DB_NAME` still `test_database`; rename to `balanga` if desired (requires re-seed → fresh startup does it automatically).
- Stripe: not used by the code; nothing configured.
- Optional: seed `riani.anggun.adp@gmail.com` admin (or set `ADMIN_EMAIL/ADMIN_PASSWORD` to it) if the older e2e tests must pass.
