# DataGuard API

[![CI](https://github.com/FredHM00/dataguard-api/actions/workflows/ci.yaml/badge.svg)](https://github.com/FredHM00/dataguard-api/actions)

Educational REST API for managing fictitious service records, with JWT authentication, encryption of sensitive notes, and audit trail.

> **Warning:** portfolio project (junior level) for study. **Not production-ready** — it does not guarantee legal compliance or absolute security. Uses fictitious data only. HTTPS, centralized secrets, and other production controls would require additional setup.

## Stack

Python 3.12 · FastAPI · PostgreSQL 16 · SQLAlchemy 2.x · Alembic · Pydantic v2 ·
PyJWT · Argon2 · Fernet · slowapi · pytest · Bandit · pip-audit · Gitleaks ·
Docker Compose · GitHub Actions — developed on Ubuntu under WSL 2.

## Prerequisites

- Ubuntu 24.04 on WSL 2, Docker Desktop with WSL integration enabled
- Python 3.12 + `python3.12-venv`, Git
- Free ports: `8000` (API), `5432` (Postgres, loopback only)

## Installation (Ubuntu)

```bash
git clone <repo> && cd dataguard-api
cp .env.example .env

# Local secrets (never commit .env):
echo "JWT_SECRET_KEY=$(openssl rand -base64 48)" >> .env
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" >> /tmp/fkey
echo "FERNET_KEY=$(cat /tmp/fkey)" >> .env && rm /tmp/fkey
```

```bash
docker compose up -d
python3 -m venv .venv && . .venv/bin/activate
pip install -e .
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

Via container (hardened image, non-root, healthcheck; it uses the Compose
network, so the local `.env` stays the same — the service only overrides
`POSTGRES_HOST` and `RATELIMIT_STORAGE_URI`):

```bash
docker compose up -d --build
docker compose exec db psql -U dataguard -d dataguard -c "SELECT 1"
curl -s localhost:8000/health
```

## Local HTTPS (Caddy, internal CA)

Compose starts Caddy terminating TLS on `127.0.0.1:443` with a self-signed
certificate (`tls internal`) and HSTS. Proof:

```bash
curl -sk -D - https://localhost/health -o /dev/null   # -k: internal CA, lab only
```

Conscious tradeoff: `-k` trusts any certificate — acceptable against your own
lab, forbidden as a habit. In production, the same Caddyfile with a real domain
issues public ACME automatically (no `tls internal`), the API port would no
longer be published, and `uvicorn` would stay behind the proxy.

- API: http://localhost:8000 — health at `GET /health`
- Interactive OpenAPI: http://localhost:8000/docs

## Environment variables

| Variable | Required | Purpose |
|---|---|---|
| `POSTGRES_USER/POSTGRES_PASSWORD/POSTGRES_DB` | yes | Compose + database URL |
| `DATABASE_URL` | no | Overrides the assembled URL (CI, manual tests) |
| `JWT_SECRET_KEY` | yes | Token signing (no default on purpose) |
| `FERNET_KEY` | no (legacy) | Old single key; use `FERNET_KEYS` |
| `FERNET_KEYS` | yes (one of the two) | List `new,current,…` — first encrypts, all decrypt |
| `RATELIMIT_STORAGE_URI` | no | `memory://` (default, single process) or `redis://127.0.0.1:6379` (distributed; Compose already starts Redis) |

## Tests and checks

```bash
pytest -q                    # full suite (isolated dataguard_test database)
bandit -r app                # static analysis (expected: clean)
pip-audit                    # CVEs in dependencies
gitleaks detect --source .   # secrets in the repo (binary; see Step 5)
# ZAP baseline (bench, app running): see docs/zap.md
```

Test database: `dataguard_test`, created by the Compose init; each test runs
in a transaction with rollback (nothing survives).

## Endpoints

See `docs/endpoints.md` (full table) and `/docs` with the API running.
Summary: `POST /api/v1/auth/register`, `POST /api/v1/auth/login` (10/min
limit, returns access+refresh pair), `POST /api/v1/auth/refresh` (rotation),
`POST /api/v1/auth/logout`, `GET /api/v1/users/me`, CRUD on `/api/v1/records`
(ownership enforced; foreign records answer 404), `GET /api/v1/audit-logs`
(admin only), `GET /health`, `GET /metrics`.

## Observability (bench)

JSON logs on stdout (one line per request: method, sanitized path, status,
duration, generated or echoed `X-Request-ID`). No query strings and no bodies
in logs. Counters on `/metrics` (in-memory, per process — real Prometheus
would require the official client). In dev, uvicorn also logs each request
(duplicated with ours).

## Structure

```
app/main.py          FastAPI + rate limit + router /api/v1
app/core/            settings (.env), domain exceptions, limiter
app/db/              engine, session, Base + constraint naming convention
app/models/          User, Record, AuditLog, RefreshToken (typed SQLAlchemy 2.x)
app/schemas/         Pydantic v2 (input/output; extra="forbid" on inputs)
app/api/             deps (get_current_user, require_admin), v1 routes
app/services/        rules: signup/login, refresh with rotation, owned CRUD
app/security/        Argon2, PyJWT, Fernet KeyRing + rotate (fail-closed at boot)
app/audit/           transactional log_action (no commit of its own)
migrations/          Alembic (autogenerate always reviewed before applying)
tests/               pytest with isolated database + rollback
docs/                sql_examples.sql (didactic), endpoints.md
compose.yaml         Postgres 16 + Redis (loopback) + hardened API + test DB in init
Dockerfile           slim image, non-root uid 10000, no .env, stdlib healthcheck
.dockerignore        ensures secrets and tooling never enter the image
```

## Recorded decisions

- UUID as PK (anti-enumeration), CHECKs instead of native ENUM (simple
  migrations), `notes_ciphertext` (name documents the content), `CASCADE` on
  records vs `SET NULL` on audit, 404 instead of 403 for foreign records.
- Details and rationale in the Step 0–5 reports.

## Fernet key rotation (no downtime)

Losing the keys = losing the notes (irreversible); rotating without
re-encrypting = old records unreadable. Procedure:

```bash
# 1. Generate the new key and make it PRIMARY (current becomes fallback):
#    FERNET_KEYS=<new>,<current>
# 2. Restart the API (writes with the new key, reads with both — zero downtime)
# 3. Re-encrypt everything:
.venv/bin/python -m app.security.rotate
# 4. Remove the old one: FERNET_KEYS=<new> + restart
# 5. Securely discard the old key and back up the new one outside the repo
```

## Future work (out of this cycle)

Kubernetes manifests, Postgres backup/restore, metric alerts.
The portfolio cycle (Steps 0–14) is closed.
