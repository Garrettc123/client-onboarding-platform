# Deployment

1. Create Supabase project → run `database/migrations/001_init.sql`
2. Set GitHub Actions secrets (see `terraform/secrets/required.tfvars.example`)
3. Create Railway service linked to this repo
4. Push to `main` → CI deploys via `serviceInstanceDeployV2`
5. Point Pipedrive webhook to `https://<service>/webhooks/pipedrive`
6. Start workers (Railway multi-service or docker-compose)

Rollback:

```bash
gh workflow run rollback.yml -f mode=commit-sha -f sha=<good-sha>
```
