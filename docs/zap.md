# Dynamic testing with OWASP ZAP (local lab) — Step 11

Scope: **only the local API** (`localhost:8000`). Never point ZAP at third
parties without written authorization. *Baseline* scan (public surface, no
login); authenticated scan is future work (requires an auth script with refresh).

## Procedure

```bash
cd ~/projects/dataguard-api
. .venv/bin/activate
uvicorn app.main:app --port 8000 &   # terminal 1

# Container -> API connectivity (via host.docker.internal):
docker run --rm curlimages/curl:8.12.1 -s http://host.docker.internal:8000/health

# Baseline (reports in ./zap_out):
mkdir -p zap_out
docker run --name zapbase ghcr.io/zaproxy/zaproxy:stable \
  zap-baseline.py -t http://host.docker.internal:8000 \
  -J report.json -r report.html
docker cp zapbase:/zap/report.json zap_out/
docker cp zapbase:/zap/report.html zap_out/
docker rm zapbase
```

`zap_out/` is git-ignored (local reports, not versioned evidence);
triage goes below, with date and image version.

## Triage (real run)

*Image: `ghcr.io/zaproxy/zaproxy:stable` (pulled 2026-10-14).*
*Target: `http://host.docker.internal:8000` — dev API with local database.*
*Command with `-I` (warnings don't fail); full stdout/console output + `report.json`.*

Result: **66 PASS, 0 FAIL, 1 WARN Informational.**

| Alert | Risk | Verdict |
|---|---|---|
| Storable and Cacheable Content [10049] on `/robots.txt` and `/sitemap.xml` (404) | Informational | **Fixed at the general cause**: 404 responses lacked `Cache-Control`; since the principle also applies to authenticated responses (must not sit in intermediary caches), added `SecurityHeadersMiddleware` (`Cache-Control: no-store` + `X-Content-Type-Options: nosniff`) with tests. Re-ran clean (see below) |
| Spider: `/` returns 404 ("expected 200") | — | **Correct behavior**: API with no root route by design; `/health` is the liveness endpoint |

Re-run after the middleware: `10049-3` gone; in its place, `10049-1 Non-Storable
Content` (Informational) on all 3 URLs — that is the rule's confirmation state
("verified: not storable"), not a problem. Scores: 66 PASS, 0 FAIL,
1 INFO by design. Also confirmed that 404 responses carry
`cache-control: no-store` (curl -I) and that the rule's source (beta, open)
only reaches 10049-3 when no `no-store` is present.

Triage rules: every alert becomes a fix, a documented false positive, or an
accepted risk with justification — never silenced without a record.

## Declared limitations

- Baseline doesn't authenticate: partial coverage (JWT routes not exercised).
- Dynamic scanners find symptoms, they don't prove absence (same caveat as Step 5).
- Not run in CI on purpose: needs the app up, is slow, and has network
  flakiness — CI keeps the deterministic; ZAP is a bench procedure.
