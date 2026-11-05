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

-- Submitted results: an engine's team sends a better number with what it takes to reproduce it, kept beside the
-- reports and published only once rerun on the project's machines (status verified)
alter table public.measurement_reports add column if not exists kind text not null default 'report' check (kind in ('report', 'result'));
alter table public.measurement_reports add column if not exists version text check (length(version) <= 200);
alter table public.measurement_reports add column if not exists config text check (length(config) <= 8000);
alter table public.measurement_reports add column if not exists link text check (link is null or link ~ '^https://');
alter table public.measurement_reports drop constraint if exists measurement_reports_status_check;
alter table public.measurement_reports add constraint measurement_reports_status_check check (status in ('open', 'fixed', 'not_a_bug', 'verified', 'rejected'));

-- for now a result can be submitted without an account; a report still needs one
drop policy if exists "anyone submits results" on public.measurement_reports;
create policy "anyone submits results" on public.measurement_reports for insert to anon
  with check (kind = 'result' and user_id is null and fix_url is null and status = 'open');

-- an outlier closed by a maintainer: the outliers are worked out from the data, not stored, so their state lives here,
-- keyed by machine, model and setup ("h100-sxm-x1|gemma-4-12b|decode"); anyone reads it, a maintainer writes it
create table if not exists public.outlier_status (
  key text primary key,
  status text not null default 'closed' check (status in ('open', 'closed')),
  updated_at timestamptz not null default now(),
  updated_by uuid default auth.uid() references auth.users (id) on delete set null
);
alter table public.outlier_status enable row level security;
drop policy if exists "outlier status is public" on public.outlier_status;
create policy "outlier status is public" on public.outlier_status for select using (true);
drop policy if exists "maintainers set outlier status" on public.outlier_status;
create policy "maintainers set outlier status" on public.outlier_status for all to authenticated
  using (public.is_maintainer()) with check (public.is_maintainer());
