# Security — how to report issues

## Scope

This is an **educational portfolio project**, maintained with no SLA and no
guarantees. It is **not** production-ready: no TLS, no centralized secrets,
no distributed rate limiting, no key rotation (see README, out-of-scope notes).

## How to report

**Do not open a public issue with vulnerability details.** Prefer, in this order:

1. GitHub **private vulnerability reporting** (Security tab → Report a vulnerability),
   if enabled on the repository; or
2. A private message to the maintainer via the GitHub profile.

Include: description, reproduction steps, estimated impact and, if any, a
suggested fix. Logs and examples must use **fictitious data** (never real data).

## Useful to report

Authentication/authorization failures, plaintext exposure of notes, record
ownership bypass, committed secrets, vulnerable dependency without a
documented fix.

## Out of reporting scope

- Development secrets clearly marked in `.env.example`
  (local placeholders, never used outside the lab).
- Missing controls listed as out of scope in the README.
- Scanner alerts with no demonstrated impact (send the PoC along).

## Commitment

No guaranteed timeline (personal study project), but every legitimate report
will be reviewed, fixed if valid, and credited in the history, without
exposing sensitive data in the process.
