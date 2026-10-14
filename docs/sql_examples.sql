-- docs/sql_examples.sql
-- Didactic examples over the THREE DataGuard tables (fictitious data).
-- Usage: docker compose exec db psql -U dataguard -d dataguard -f <file>
-- The application keeps using parameterized ORM; this is for learning SQL.

-- 1) Simple FILTER: all open records.
-- When to use: operational view of what is pending.
SELECT id, title, status
  FROM records
 WHERE status = 'open';

-- 2) FILTER + ORDERING: newest support first.
-- When to use: queues by category, newest to oldest.
SELECT title, category, created_at
  FROM records
 WHERE category = 'suporte'
 ORDER BY created_at DESC;

-- 3) JOIN (INNER JOIN): records with the owner's e-mail.
-- When to use: enrich the record with owner data.
SELECT r.title, r.status, u.email AS owner_email
  FROM records AS r
  JOIN users AS u ON u.id = r.owner_id
 WHERE u.email = 'ana@example.com';

-- 4) AGGREGATION: how many records per status.
-- When to use: summary dashboard, counts per group.
SELECT status, COUNT(*) AS total
  FROM records
 GROUP BY status
 ORDER BY total DESC;

-- 5) JOIN + AGGREGATION: records per category for one user.
-- When to use: usage profile per person, without exposing notes.
SELECT r.category, COUNT(*) AS total
  FROM records AS r
  JOIN users AS u ON u.id = r.owner_id
 WHERE u.email = 'ana@example.com'
 GROUP BY r.category
 ORDER BY total DESC;

-- 6) Pagination with LIMIT/OFFSET (page 2, size 20).
-- OFFSET = (page - 1) * size. Simple; for huge tables prefer
-- keyset pagination (WHERE created_at < ... ORDER BY ... LIMIT ...),
-- which does not degrade on the last pages.
SELECT id, title, created_at
  FROM records
 ORDER BY created_at DESC, id DESC
 LIMIT 20 OFFSET 20;

-- 7) AUDIT: latest denied attempts.
-- When to use: detect probing (someone trying to read what is not theirs).
SELECT actor_id, action, resource_type, resource_id, created_at
  FROM audit_logs
 WHERE result = 'denied'
 ORDER BY created_at DESC
 LIMIT 20;

-- 8) AUDIT with LEFT JOIN: trail with actor e-mail, when present.
-- LEFT (not INNER) because actor_id can be NULL (removed user or
-- anonymous action); with INNER those rows would vanish from the trail.
SELECT a.action, a.result, u.email AS actor_email, a.created_at
  FROM audit_logs AS a
  LEFT JOIN users AS u ON u.id = a.actor_id
 ORDER BY a.created_at DESC
 LIMIT 20;

-- 9) UNIQUENESS check: duplicate e-mails (expected: 0 rows).
-- When to use: sanity after manual imports or migrations.
SELECT email, COUNT(*) AS total
  FROM users
 GROUP BY email
HAVING COUNT(*) > 1;

-- 10) KEYSET PAGINATION: same newest 20 after the marker (ts, id).
-- Tuple comparison uses the (created_at, id) index: no scanning or discarding
-- like OFFSET. Swap the literals for the decoded next_cursor.
SELECT id, title, created_at
  FROM records
 WHERE (created_at, id) < ('2026-01-01T00:00:00+00:00', '00000000-0000-0000-0000-000000000000')
 ORDER BY created_at DESC, id DESC
 LIMIT 20;
