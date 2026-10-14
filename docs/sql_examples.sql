-- docs/sql_examples.sql
-- Exemplos didaticos sobre as TRES tabelas do DataGuard (dados ficticios).
-- Como usar: docker compose exec db psql -U dataguard -d dataguard -f <arquivo>
-- A aplicacao continua usando ORM parametrizado; aqui e aprendizado de SQL.

-- 1) FILTRO simples: todos os registros abertos.
-- Quando usar: visao operacional do que esta pendente.
SELECT id, title, status
  FROM records
 WHERE status = 'open';

-- 2) FILTRO + ORDENACAO: suporte mais recente primeiro.
-- Quando usar: filas por categoria, do novo para o antigo.
SELECT title, category, created_at
  FROM records
 WHERE category = 'suporte'
 ORDER BY created_at DESC;

-- 3) JUNCAO (INNER JOIN): registros com o e-mail do dono.
-- Quando usar: enriquecer o registro com dados do proprietario.
SELECT r.title, r.status, u.email AS owner_email
  FROM records AS r
  JOIN users AS u ON u.id = r.owner_id
 WHERE u.email = 'ana@example.com';

-- 4) AGREGACAO: quantos registros por status.
-- Quando usar: painel resumido, contagens por grupo.
SELECT status, COUNT(*) AS total
  FROM records
 GROUP BY status
 ORDER BY total DESC;

-- 5) JUNCAO + AGREGACAO: registros por categoria de um usuario.
-- Quando usar: perfil de uso por pessoa, sem expor observacoes.
SELECT r.category, COUNT(*) AS total
  FROM records AS r
  JOIN users AS u ON u.id = r.owner_id
 WHERE u.email = 'ana@example.com'
 GROUP BY r.category
 ORDER BY total DESC;

-- 6) PAGINACAO com LIMIT/OFFSET (pagina 2, tamanho 20).
-- OFFSET = (pagina - 1) * tamanho. Simples; para tabelas gigantes prefira
-- paginacao por chave (WHERE created_at < ... ORDER BY ... LIMIT ...),
-- que nao degrada nas ultimas paginas.
SELECT id, title, created_at
  FROM records
 ORDER BY created_at DESC, id DESC
 LIMIT 20 OFFSET 20;

-- 7) AUDITORIA: ultimas tentativas negadas.
-- Quando usar: detectar sondagem (alguem tentando ler o que nao e seu).
SELECT actor_id, action, resource_type, resource_id, created_at
  FROM audit_logs
 WHERE result = 'denied'
 ORDER BY created_at DESC
 LIMIT 20;

-- 8) AUDITORIA com LEFT JOIN: trilha com e-mail do ator, se houver.
-- LEFT (e nao INNER) porque actor_id pode ser NULL (usuario removido ou
-- acao anonima); com INNER essas linhas sumiriam da trilha.
SELECT a.action, a.result, u.email AS actor_email, a.created_at
  FROM audit_logs AS a
  LEFT JOIN users AS u ON u.id = a.actor_id
 ORDER BY a.created_at DESC
 LIMIT 20;

-- 9) VERIFICACAO de unicidade: e-mails duplicados (esperado: 0 linhas).
-- Quando usar: sanidade apos importacoes ou migracoes manuais.
SELECT email, COUNT(*) AS total
  FROM users
 GROUP BY email
HAVING COUNT(*) > 1;

-- 10) PAGINACAO POR CHAVE: mesmos 20 mais recentes que o marco (ts, id).
-- Comparacao de tupla usa o indice (created_at, id): nao varre nem descarta
-- como o OFFSET. Troque os literais pelo next_cursor decodificado.
SELECT id, title, created_at
  FROM records
 WHERE (created_at, id) < ('2026-01-01T00:00:00+00:00', '00000000-0000-0000-0000-000000000000')
 ORDER BY created_at DESC, id DESC
 LIMIT 20;
