-- Reports of a measurement that looks wrong, filed from the site's Reports page (web/assets/js/ui/reports.js).
-- Run once in the Supabase project's SQL editor. Anyone can read the reports; a signed-in visitor can file one; a
-- maintainer (a row in public.maintainers) can attach the pull request that fixes it and close it.

create table if not exists public.maintainers (
  user_id uuid primary key references auth.users (id) on delete cascade
);

create table if not exists public.measurement_reports (
  id bigint generated always as identity primary key,
  created_at timestamptz not null default now(),
  user_id uuid default auth.uid() references auth.users (id) on delete set null,  -- kept when the account goes; the insert policy holds it to the filer
  reporter text check (length(reporter) <= 120),  -- the account's name, shown beside the report
  source text not null default 'results' check (source in ('results', 'quality')),  -- the table it was flagged from
  row_id text,                          -- that table's row, so the report links back to the exact measurement
  hardware text not null,
  engine text not null,
  model text not null,
  workload text not null,               -- a Quality report's task
  value text,                           -- the number the site showed
  note text not null check (length(note) between 10 and 4000),
  fix_url text check (fix_url is null or fix_url ~ '^https://github\.com/'),
  status text not null default 'open' check (status in ('open', 'fixed', 'not_a_bug'))
);

alter table public.maintainers enable row level security;
alter table public.measurement_reports enable row level security;

create or replace function public.is_maintainer() returns boolean
  language sql stable security definer set search_path = public
  as $$ select exists (select 1 from public.maintainers where user_id = auth.uid()) $$;

-- a signed-in visitor can ask whether they are a maintainer (the page shows the fix field only then)
drop policy if exists "maintainers read self" on public.maintainers;
create policy "maintainers read self" on public.maintainers for select to authenticated using (user_id = auth.uid());

drop policy if exists "reports are public" on public.measurement_reports;
create policy "reports are public" on public.measurement_reports for select using (true);

drop policy if exists "signed-in visitors file reports" on public.measurement_reports;
drop policy if exists "anyone files reports" on public.measurement_reports;
create policy "signed-in visitors file reports" on public.measurement_reports for insert to authenticated
  with check (user_id = auth.uid() and fix_url is null and status = 'open');

drop policy if exists "maintainers close reports" on public.measurement_reports;
create policy "maintainers close reports" on public.measurement_reports for update to authenticated
  using (public.is_maintainer()) with check (public.is_maintainer());

-- a maintainer, added by their account's id (Authentication → Users):
-- insert into public.maintainers (user_id) values ('<user uuid>');
