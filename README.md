# DataGuard API

API REST educacional para gerenciamento de registros fictícios de atendimento, com autenticação JWT, criptografia de observações sensíveis e trilha de auditoria.

> **Aviso:** projeto de portfólio (nível júnior) para estudo. **Não está pronto para produção**, não garante conformidade legal nem segurança absoluta. Usa apenas dados fictícios. HTTPS, segredos centralizados e demais controles de produção exigiriam configuração adicional.

## Stack

Python 3.12 · FastAPI · PostgreSQL 16 · SQLAlchemy 2.x · Alembic · Pydantic v2 ·
PyJWT · Argon2 · Fernet · slowapi · pytest · Bandit · pip-audit · Gitleaks ·
Docker Compose · GitHub Actions — desenvolvimento em Ubuntu no WSL 2.

## Pré-requisitos

- Ubuntu 24.04 no WSL 2, Docker Desktop com integração WSL ativa
- Python 3.12 + `python3.12-venv`, Git
- Portas livres: `8000` (API), `5432` (Postgres, só loopback)

## Instalação (Ubuntu)

```bash
git clone <repo> && cd dataguard-api
cp .env.example .env

# Segredos locais (nunca commitar o .env):
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

- API: http://localhost:8000 — saúde em `GET /health`
- OpenAPI interativa: http://localhost:8000/docs

## Variáveis de ambiente

| Variável | Obrigatória | Função |
|---|---|---|
| `POSTGRES_USER/POSTGRES_PASSWORD/POSTGRES_DB` | sim | Compose + URL do banco |
| `DATABASE_URL` | não | Sobrescreve a URL montada (CI, testes manuais) |
| `JWT_SECRET_KEY` | sim | Assinatura dos tokens (sem default de propósito) |
| `FERNET_KEY` | sim | Criptografia das observações (sem default, sem fallback) |

## Testes e verificações

```bash
pytest -q                    # suite completa (banco dataguard_test isolado)
bandit -r app                # análise estática (esperado: limpo)
pip-audit                    # CVEs nas dependências
gitleaks detect --source .   # segredos no repo (binário; ver Etapa 5)
```

Banco de testes: `dataguard_test`, criado pelo init do Compose; cada teste
roda em transação com rollback (nada sobrevive).

## Endpoints

Ver `docs/endpoints.md` (tabela completa) e `/docs` com a API no ar.
Resumo: `POST /api/v1/auth/register`, `POST /api/v1/auth/login` (limite
10/min), `GET /api/v1/users/me`, CRUD em `/api/v1/records` (posse verificada;
alheio responde 404), `GET /api/v1/audit-logs` (só admin), `GET /health`.

## Estrutura

```
app/main.py          FastAPI + rate limit + router /api/v1
app/core/            settings (.env), exceções de domínio, limiter
app/db/              engine, sessão, Base + convenção de constraints
app/models/          User, Record, AuditLog (SQLAlchemy 2.x tipado)
app/schemas/         Pydantic v2 (entrada/saída; extra="forbid" nos inputs)
app/api/             deps (get_current_user, require_admin), rotas v1
app/services/        regras: cadastro/login, CRUD com posse
app/security/        Argon2, PyJWT, Fernet (falha fechada no boot)
app/audit/           log_action transacional (sem commit próprio)
migrations/          Alembic (autogenerate sempre revisado antes de aplicar)
tests/               pytest com banco isolado + rollback
docs/                sql_examples.sql (didático), endpoints.md
compose.yaml         Postgres 16 (loopback) + banco de testes no init
```

## Decisões registradas

- UUID como PK (anti-enumeração), Checks em vez de ENUM nativo (migração simples),
  `notes_ciphertext` (nome documenta o conteúdo), `CASCADE` nos registros vs
  `SET NULL` na auditoria, 404 em vez de 403 para registro alheio.
- Detalhes e justificativas nos relatórios das Etapas 0–5.

## Fora de escopo (de propósito)

HTTPS/TLS, Redis para rate limit distribuído, rotação de chaves Fernet,
refresh tokens, observabilidade (logs estruturados/métricas), hardening de
container. Itens para evoluir o portfólio depois.
