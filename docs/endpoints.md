# Endpoints — DataGuard API (`/api/v1`)

Standard error format: `{"detail": "..."}` — no stack traces, no internal data.
Validation failures: `422` with the field detail. Login under rate limit: `429`.

## Auth (public)

| Method | Path | Body | Responses |
|---|---|---|---|
| POST | `/auth/register` | `{email, password}` (8–128 chars; no `role`) | `201` profile · `409` e-mail taken · `422` invalid/`role` sent |
| POST | `/auth/login` | OAuth2 form (`username`=e-mail, `password`) | `200` `{access_token, refresh_token, token_type}` · `401` generic · `429` abuse |
| POST | `/auth/refresh` | `{refresh_token}` (single use; reuse revokes the family) | `200` new pair · `401` invalid/expired/reused · `429` abuse |
| POST | `/auth/logout` | `{refresh_token}` (idempotent: unknown also returns `204`) | `204` no body |

## User (JWT)

| Method | Path | Responses |
|---|---|---|
| GET | `/users/me` | `200` profile (no hash) · `401` missing/tampered/expired token |

## Records (JWT + ownership; foreign or missing = `404`)

| Method | Path | Body/Query | Responses |
|---|---|---|---|
| POST | `/records` | `{title ≤200, category ≤50, notes ≤10000}` (born `open`) | `201` (with plaintext `notes` for the owner) |
| GET | `/records` | `?page≥1` `?page_size 1–100` (default 20) | `200` `{items, total, page, page_size}` (authorized ones only) |
| GET | `/records/cursor` | opaque `?cursor` `?limit 1–100` (default 20) | `200` `{items, next_cursor}` (`null` at the end) · `422` tampered cursor |
| GET | `/records/{id}` | UUID (`422` if malformed) | `200` · `404` |
| PATCH | `/records/{id}` | any subset of `{title, category, notes, status∈open\|in_progress\|closed}` | `200` · `404` · `422` |
| DELETE | `/records/{id}` | — | `204` (no body) · `404` |

## Audit (admin only)

| Method | Path | Responses |
|---|---|---|
| GET | `/audit-logs` | `200` paginated (common: `403`; anonymous: `401`) |

## Infra

| Method | Path | Responses |
|---|---|---|
| GET | `/health` | `200` `{"status":"ok"}` (no auth) |
| GET | `/metrics` | `200` Prometheus text (per-process counters; no auth) |

## Typical flow

1. `POST /auth/register` → `201`
2. `POST /auth/login` (form) → `200` with `access_token`
3. Send `Authorization: Bearer <token>` on all other calls
4. In Swagger (`/docs`), the **Authorize** button accepts the login `username`/`password`
