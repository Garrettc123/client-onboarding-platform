-- Client Onboarding Platform — initial schema
-- Run: psql $DATABASE_URL -f database/migrations/001_init.sql

create extension if not exists "pgcrypto";

-- system_events (matches prior Garcar ops schema)
create table if not exists public.system_events (
  id            uuid primary key default gen_random_uuid(),
  event_type    text not null
                check (event_type in (
                  'deployment',
                  'rollback',
                  'pipedrive_webhook',
                  'onboarding_started',
                  'onboarding_completed',
                  'onboarding_failed',
                  'health_fail',
                  'incident',
                  'manual'
                )),
  payload       jsonb not null default '{}'::jsonb,
  created_at    timestamptz not null default now(),
  sha           text generated always as (payload->>'sha') stored,
  status        text generated always as (payload->>'status') stored,
  actor         text generated always as (payload->>'actor') stored
);

create index if not exists system_events_event_type_idx on public.system_events (event_type);
create index if not exists system_events_created_at_idx on public.system_events (created_at desc);
create index if not exists system_events_payload_gin on public.system_events using gin (payload);

-- clients
create table if not exists public.clients (
  id              uuid primary key default gen_random_uuid(),
  org_name        text not null,
  deal_id         text unique,
  person_name     text,
  status          text not null default 'provisioning'
                  check (status in ('provisioning', 'active', 'paused', 'churned', 'failed')),
  github_repo     text,
  clickup_space_id text,
  metadata        jsonb not null default '{}'::jsonb,
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now()
);

create index if not exists clients_status_idx on public.clients (status);
create index if not exists clients_deal_id_idx on public.clients (deal_id);

-- onboarding_runs (worker queue)
create table if not exists public.onboarding_runs (
  id              uuid primary key default gen_random_uuid(),
  client_id       uuid references public.clients(id) on delete set null,
  deal_id         text,
  title           text,
  org_name        text not null,
  person_name     text,
  source          text not null default 'pipedrive',
  status          text not null default 'pending'
                  check (status in ('pending', 'running', 'succeeded', 'failed', 'dead_letter')),
  attempts        int not null default 0,
  max_attempts    int not null default 5,
  last_error      text,
  result          jsonb not null default '{}'::jsonb,
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now(),
  started_at      timestamptz,
  finished_at     timestamptz
);

create index if not exists onboarding_runs_status_idx on public.onboarding_runs (status);
create index if not exists onboarding_runs_created_at_idx on public.onboarding_runs (created_at);

-- RLS
alter table public.system_events enable row level security;
alter table public.clients enable row level security;
alter table public.onboarding_runs enable row level security;

create policy "Service role full access system_events"
  on public.system_events for all
  using (auth.role() = 'service_role')
  with check (auth.role() = 'service_role');

create policy "Service role full access clients"
  on public.clients for all
  using (auth.role() = 'service_role')
  with check (auth.role() = 'service_role');

create policy "Service role full access onboarding_runs"
  on public.onboarding_runs for all
  using (auth.role() = 'service_role')
  with check (auth.role() = 'service_role');

create policy "Authenticated read clients"
  on public.clients for select to authenticated using (true);

create policy "Authenticated read onboarding_runs"
  on public.onboarding_runs for select to authenticated using (true);

create policy "Authenticated read system_events"
  on public.system_events for select to authenticated using (true);
