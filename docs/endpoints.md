# Endpoints — DataGuard API (`/api/v1`)

Formato de erro padrão: `{"detail": "..."}` — sem stack trace, sem dados internos.
Falhas de validação: `422` com o detalhe do campo. Login sob rate limit: `429`.

## Auth (público)

| Método | Path | Corpo | Respostas |
|---|---|---|---|
| POST | `/auth/register` | `{email, password}` (8–128 chars; sem `role`) | `201` perfil · `409` e-mail usado · `422` inválido/`role` enviado |
| POST | `/auth/login` | form OAuth2 (`username`=e-mail, `password`) | `200` `{access_token, refresh_token, token_type}` · `401` genérico · `429` abuso |
| POST | `/auth/refresh` | `{refresh_token}` (uso único; reuso revoga a família) | `200` par novo · `401` inválido/expirado/reutilizado · `429` abuso |
| POST | `/auth/logout` | `{refresh_token}` (idempotente: desconhecido também dá `204`) | `204` sem corpo |

## Usuário (JWT)

| Método | Path | Respostas |
|---|---|---|
| GET | `/users/me` | `200` perfil (sem hash) · `401` sem token/adulterado/expirado |

## Registros (JWT + posse; alheio ou inexistente = `404`)

| Método | Path | Corpo/Query | Respostas |
|---|---|---|---|
| POST | `/records` | `{title ≤200, category ≤50, notes ≤10000}` (nasce `open`) | `201` (com `notes` em claro p/ o dono) |
| GET | `/records` | `?page≥1` `?page_size 1–100` (padrão 20) | `200` `{items, total, page, page_size}` (só os autorizados) |
| GET | `/records/cursor` | `?cursor` opaco `?limit 1–100` (padrão 20) | `200` `{items, next_cursor}` (`null` no fim) · `422` cursor adulterado |
| GET | `/records/{id}` | UUID (`422` se malformado) | `200` · `404` |
| PATCH | `/records/{id}` | qualquer subconjunto de `{title, category, notes, status∈open\|in_progress\|closed}` | `200` · `404` · `422` |
| DELETE | `/records/{id}` | — | `204` (sem corpo) · `404` |

## Auditoria (só admin)

| Método | Path | Respostas |
|---|---|---|
| GET | `/audit-logs` | `200` paginado (comum: `403`; anônimo: `401`) |

## Infra

| Método | Path | Respostas |
|---|---|---|
| GET | `/health` | `200` `{"status":"ok"}` (sem auth) |
| GET | `/metrics` | `200` texto Prometheus (contadores por processo; sem auth) |

## Fluxo típico

1. `POST /auth/register` → `201`
2. `POST /auth/login` (form) → `200` com `access_token`
3. Enviar `Authorization: Bearer <token>` nas demais chamadas
4. No Swagger (`/docs`), o botão **Authorize** aceita `username`/`password` do login
