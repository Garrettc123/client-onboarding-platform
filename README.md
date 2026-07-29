# Client Onboarding Platform

Zero-touch client onboarding: Pipedrive deal won → FastAPI webhook → durable workers → GitHub repo + ClickUp space + Supabase state.

## Architecture

```
client-onboarding-platform/
├── api/                 # FastAPI application
├── database/            # SQL migrations, RLS, seed
├── workers/             # Onboarding, retry, dead-letter
├── github/              # Actions, PR & issue templates
├── terraform/           # Railway, Cloudflare, Supabase, secrets
├── docker/              # Local & production containers
├── monitoring/          # Prometheus, Grafana, Alertmanager
└── docs/                # API reference, deployment, runbooks
```

## Quick Start

```bash
cp .env.example .env
docker compose -f docker/docker-compose.yml up --build
psql $DATABASE_URL -f database/migrations/001_init.sql
uvicorn api.main:app --reload --port 8000
python -m workers.onboarding_worker
```

## Required Secrets

| Secret | Purpose |
|--------|--------|
| `SUPABASE_URL` / `SUPABASE_SERVICE_KEY` | State & events |
| `PIPEDRIVE_WEBHOOK_SECRET` | Verify webhooks |
| `GITHUB_TOKEN` | Provision client repos |
| `CLICKUP_API_TOKEN` | Provision ClickUp spaces |
| `RAILWAY_TOKEN` / `RAILWAY_SERVICE_ID` | Deploy |
| `NOTION_TOKEN` / `NOTION_DEPLOY_PAGE_ID` | Status updates |
| `LINEAR_API_KEY` | Incident creation |

## Event Flow

1. Pipedrive deal status → `won`
2. Webhook hits `POST /webhooks/pipedrive`
3. Event written to `system_events` + `onboarding_runs`
4. Onboarding worker picks up job
5. Creates GitHub repo, ClickUp space, records client row
6. Retries / dead-letter on failure
7. Health + deploy notifications to Notion / Linear

See `docs/` for full reference.
