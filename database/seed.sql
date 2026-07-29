-- Optional seed for local development
insert into public.system_events (event_type, payload)
values (
  'manual',
  jsonb_build_object(
    'message', 'seed',
    'actor', 'scaffold',
    'timestamp', now()
  )
) on conflict do nothing;
