# API Reference

Base URL: `https://<service>/`

## Health

`GET /health`

```json
{ "status": "ok", "service": "client-onboarding-platform", "timestamp": "..." }
```

## Webhooks

`POST /webhooks/pipedrive`

Headers: `X-Pipedrive-Signature` (optional when secret unset in dev)

When deal `status=won`, enqueues an `onboarding_runs` row.

## Clients

`GET /clients?status=active&limit=50`

`GET /clients/{id}`

`GET /clients/{id}/runs`
