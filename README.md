# Valhalla Starter

FastAPI + Postgres + Redis backend, minimal Next.js frontend. Dockerized.

## Quick Start
1) Copy env and start:
```bash
cp .env.example .env
docker compose up --build
```

Seed an admin:

curl -sS -X POST http://localhost:8000/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"changeme","full_name":"Admin","role":"admin"}'

Login to get tokens:

curl -sS -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"changeme"}'

Call a protected route:

curl -sS "http://localhost:8000/api/v1/leads?limit=10" -H "token: <ACCESS_TOKEN>"

Frontend:

Open http://localhost:3000

Click Login, then Load Leads

Useful URLs

API live: GET /api/v1/health/live → {"status":"ok"}

OpenAPI: GET /api/v1/openapi.json

Frontend: http://localhost:3000

Project Structure

backend/ FastAPI app (JWT auth, users/leads/deals, underwriting stub)

frontend/ Next.js app (simple test page + API helper)

docker-compose.yml dev stack (Postgres, Redis, API, Web)

Dev Tips

Change SECRET_KEY in .env

Pydantic v2 (from_attributes = True)

Tables auto-create on boot; add Alembic later for migrations

Tests
docker compose exec api pytest -q app/tests

### Background Jobs (RQ)
- Worker runs in `worker` service.
- Enqueue email:
  ```bash
  ACCESS=...  # Bearer
  curl -sS -X POST "http://localhost:8000/api/v1/jobs/email?subject=Hello&body=Test" \
    -H "Authorization: Bearer $ACCESS" \
    -H "Content-Type: application/json" \
    -d '["dev@example.com"]'
  ```

Enrich a lead:

curl -sS -X POST "http://localhost:8000/api/v1/jobs/lead/1/enrich" \
  -H "Authorization: Bearer $ACCESS"

Check status:

curl -sS "http://localhost:8000/api/v1/jobs/<JOB_ID>" \
  -H "Authorization: Bearer $ACCESS"

Next Steps

Switch auth header to Authorization: Bearer <token>

Add Alembic migrations

Wire Redis for rate limiting / task queues

Replace services/ai/heimdall.py with real logic
