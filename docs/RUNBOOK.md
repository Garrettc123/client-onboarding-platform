# Runbook

## Onboarding stuck in pending

1. Check `onboarding_runs` where status=pending
2. Ensure onboarding-worker process is running
3. Inspect `last_error` on failed rows

## Dead letter

1. Query `onboarding_runs` status=dead_letter
2. Fix root cause (token, API limits, name collision)
3. Reset: `update onboarding_runs set status='pending', attempts=0 where id=...`

## Deploy failed

1. `gh run list --workflow=ci-cd.yml`
2. Rollback: `gh workflow run rollback.yml -f mode=commit-sha -f sha=...`
3. Confirm `/health` returns 200
