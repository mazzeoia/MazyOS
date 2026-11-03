create table if not exists public.clients (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null,
  name text not null,
  source text not null default 'manual',
  meta_ad_account_id text,
  google_ads_customer_id text,
  meta_page_id text,
  meta_instagram_account_id text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table public.clients add column if not exists owner_id uuid;
alter table public.clients add column if not exists source text not null default 'manual';
alter table public.clients add column if not exists meta_ad_account_id text;
alter table public.clients add column if not exists google_ads_customer_id text;
alter table public.clients add column if not exists meta_page_id text;
alter table public.clients add column if not exists meta_instagram_account_id text;
alter table public.clients add column if not exists monthly_budget numeric not null default 0;
alter table public.clients add column if not exists target_cpl numeric not null default 0;
alter table public.clients add column if not exists account_manager text not null default '';
alter table public.clients add column if not exists business_goal text not null default '';
alter table public.clients add column if not exists qualified_lead_definition text not null default '';
alter table public.clients add column if not exists whatsapp_number text not null default '';
alter table public.clients add column if not exists whatsapp_connected boolean not null default false;
alter table public.clients add column if not exists whatsapp_connection_mode text not null default 'manual';
alter table public.clients add column if not exists whatsapp_phone_number_id text not null default '';
alter table public.clients add column if not exists whatsapp_business_account_id text not null default '';
alter table public.clients add column if not exists whatsapp_real_numbers integer not null default 0;
alter table public.clients add column if not exists whatsapp_notes text not null default '';
alter table public.clients add column if not exists created_at timestamptz not null default now();
alter table public.clients add column if not exists updated_at timestamptz not null default now();

create table if not exists public.meta_connections (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null,
  meta_user_id text not null,
  meta_user_name text,
  access_token text not null,
  scopes text[] not null default '{}',
  expires_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (owner_id, meta_user_id)
);

create table if not exists public.meta_businesses (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null,
  meta_business_id text not null,
  name text not null,
  verification_status text,
  raw jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (owner_id, meta_business_id)
);

create table if not exists public.meta_ad_accounts (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null,
  meta_ad_account_id text not null,
  account_id text,
  name text not null,
  account_status int,
  currency text,
  timezone_name text,
  business_id text,
  raw jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (owner_id, meta_ad_account_id)
);

create table if not exists public.meta_pages (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null,
  meta_page_id text not null,
  name text not null,
  category text,
  meta_instagram_account_id text,
  instagram_username text,
  raw jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (owner_id, meta_page_id)
);

create table if not exists public.google_ads_connections (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null,
  google_user_id text not null default '',
  google_user_email text not null default '',
  access_token text not null,
  refresh_token text not null default '',
  scopes text[] not null default '{}',
  expires_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (owner_id, google_user_id)
);

create table if not exists public.google_ads_customer_accounts (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null,
  customer_id text not null,
  descriptive_name text not null default '',
  currency_code text,
  time_zone text,
  manager boolean not null default false,
  raw jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (owner_id, customer_id)
);

create table if not exists public.whatsapp_business_accounts (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null,
  waba_id text not null,
  business_id text,
  name text not null default '',
  ownership_type text not null default '',
  timezone_id text,
  currency text,
  message_template_namespace text,
  raw jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (owner_id, waba_id)
);

create table if not exists public.whatsapp_phone_numbers (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null,
  waba_id text not null,
  phone_number_id text not null,
  display_phone_number text not null default '',
  verified_name text not null default '',
  quality_rating text,
  platform_type text,
  code_verification_status text,
  raw jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (owner_id, phone_number_id)
);

alter table public.clients enable row level security;
alter table public.meta_connections enable row level security;
alter table public.meta_businesses enable row level security;
alter table public.meta_ad_accounts enable row level security;
alter table public.meta_pages enable row level security;
alter table public.google_ads_connections enable row level security;
alter table public.google_ads_customer_accounts enable row level security;
alter table public.whatsapp_business_accounts enable row level security;
alter table public.whatsapp_phone_numbers enable row level security;

drop policy if exists "clients_owner_select" on public.clients;
create policy "clients_owner_select" on public.clients
  for select using (auth.uid() = owner_id);

drop policy if exists "clients_owner_insert" on public.clients;
create policy "clients_owner_insert" on public.clients
  for insert with check (auth.uid() = owner_id);

drop policy if exists "clients_owner_update" on public.clients;
create policy "clients_owner_update" on public.clients
  for update using (auth.uid() = owner_id) with check (auth.uid() = owner_id);

drop policy if exists "meta_businesses_owner_select" on public.meta_businesses;
create policy "meta_businesses_owner_select" on public.meta_businesses
  for select using (auth.uid() = owner_id);

drop policy if exists "meta_ad_accounts_owner_select" on public.meta_ad_accounts;
create policy "meta_ad_accounts_owner_select" on public.meta_ad_accounts
  for select using (auth.uid() = owner_id);

drop policy if exists "meta_pages_owner_select" on public.meta_pages;
create policy "meta_pages_owner_select" on public.meta_pages
  for select using (auth.uid() = owner_id);

drop policy if exists "google_ads_customer_accounts_owner_select" on public.google_ads_customer_accounts;
create policy "google_ads_customer_accounts_owner_select" on public.google_ads_customer_accounts
  for select using (auth.uid() = owner_id);

drop policy if exists "whatsapp_business_accounts_owner_select" on public.whatsapp_business_accounts;
create policy "whatsapp_business_accounts_owner_select" on public.whatsapp_business_accounts
  for select using (auth.uid() = owner_id);

drop policy if exists "whatsapp_phone_numbers_owner_select" on public.whatsapp_phone_numbers;
create policy "whatsapp_phone_numbers_owner_select" on public.whatsapp_phone_numbers
  for select using (auth.uid() = owner_id);

-- Tokens ficam acessiveis apenas via service role no backend.
drop policy if exists "meta_connections_no_client_access" on public.meta_connections;
create policy "meta_connections_no_client_access" on public.meta_connections
  for select using (false);

drop policy if exists "google_ads_connections_no_client_access" on public.google_ads_connections;
create policy "google_ads_connections_no_client_access" on public.google_ads_connections
  for select using (false);

alter table public.campaigns add column if not exists owner_id uuid;
alter table public.campaigns add column if not exists client_id uuid;
alter table public.campaigns add column if not exists organization_id uuid;
alter table public.campaigns add column if not exists meta_campaign_id text;
alter table public.campaigns add column if not exists external_id text;
alter table public.campaigns add column if not exists platform text not null default 'meta_ads';
alter table public.campaigns add column if not exists ad_account_id text;
alter table public.campaigns add column if not exists name text;
alter table public.campaigns add column if not exists status text;
alter table public.campaigns add column if not exists effective_status text;
alter table public.campaigns add column if not exists objective text;
alter table public.campaigns add column if not exists daily_budget numeric;
alter table public.campaigns add column if not exists lifetime_budget numeric;
alter table public.campaigns add column if not exists metadata jsonb not null default '{}'::jsonb;
alter table public.campaigns add column if not exists raw jsonb not null default '{}'::jsonb;
alter table public.campaigns add column if not exists created_at timestamptz not null default now();
alter table public.campaigns add column if not exists updated_at timestamptz not null default now();
alter table public.campaigns alter column platform set default 'meta_ads';

alter table public.campaign_daily_metrics add column if not exists owner_id uuid;
alter table public.campaign_daily_metrics add column if not exists client_id uuid;
alter table public.campaign_daily_metrics add column if not exists campaign_id uuid;
alter table public.campaign_daily_metrics add column if not exists meta_campaign_id text;
alter table public.campaign_daily_metrics add column if not exists metric_date date;
alter table public.campaign_daily_metrics add column if not exists platform text not null default 'meta_ads';
alter table public.campaign_daily_metrics add column if not exists source_file text default 'meta_api_last_30d';
alter table public.campaign_daily_metrics add column if not exists date text;
alter table public.campaign_daily_metrics add column if not exists campaign text;
alter table public.campaign_daily_metrics add column if not exists campaign_name text;
alter table public.campaign_daily_metrics add column if not exists campaign_external_id text;
alter table public.campaign_daily_metrics add column if not exists ad_group text default '';
alter table public.campaign_daily_metrics add column if not exists ad_name text default '';
alter table public.campaign_daily_metrics add column if not exists spend numeric not null default 0;
alter table public.campaign_daily_metrics add column if not exists impressions integer not null default 0;
alter table public.campaign_daily_metrics add column if not exists reach integer not null default 0;
alter table public.campaign_daily_metrics add column if not exists clicks integer not null default 0;
alter table public.campaign_daily_metrics add column if not exists inline_link_clicks integer not null default 0;
alter table public.campaign_daily_metrics add column if not exists leads integer not null default 0;
alter table public.campaign_daily_metrics add column if not exists ctr numeric not null default 0;
alter table public.campaign_daily_metrics add column if not exists cpc numeric not null default 0;
alter table public.campaign_daily_metrics add column if not exists cpm numeric not null default 0;
alter table public.campaign_daily_metrics add column if not exists frequency numeric not null default 0;
alter table public.campaign_daily_metrics add column if not exists cpl numeric not null default 0;
alter table public.campaign_daily_metrics add column if not exists raw_json jsonb not null default '{}'::jsonb;
alter table public.campaign_daily_metrics add column if not exists raw jsonb not null default '{}'::jsonb;
alter table public.campaign_daily_metrics add column if not exists created_at timestamptz not null default now();
alter table public.campaign_daily_metrics add column if not exists updated_at timestamptz not null default now();

create table if not exists public.sync_runs (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null,
  client_id uuid not null,
  source text not null,
  status text not null,
  started_at timestamptz not null default now(),
  finished_at timestamptz,
  campaigns_synced integer not null default 0,
  metrics_synced integer not null default 0,
  error text,
  raw jsonb not null default '{}'::jsonb
);

create unique index if not exists campaigns_client_meta_campaign_uidx
  on public.campaigns (client_id, meta_campaign_id)
  where meta_campaign_id is not null;

create unique index if not exists campaign_daily_metrics_client_campaign_date_uidx
  on public.campaign_daily_metrics (client_id, meta_campaign_id, metric_date)
  where meta_campaign_id is not null and metric_date is not null;

alter table public.campaigns enable row level security;
alter table public.campaign_daily_metrics enable row level security;
alter table public.sync_runs enable row level security;

drop policy if exists "campaigns_owner_select" on public.campaigns;
create policy "campaigns_owner_select" on public.campaigns
  for select using (auth.uid() = owner_id);

drop policy if exists "campaign_daily_metrics_owner_select" on public.campaign_daily_metrics;
create policy "campaign_daily_metrics_owner_select" on public.campaign_daily_metrics
  for select using (auth.uid() = owner_id);

drop policy if exists "sync_runs_owner_select" on public.sync_runs;
create policy "sync_runs_owner_select" on public.sync_runs
  for select using (auth.uid() = owner_id);

-- Otimizacao IA: plano de acao consultivo gerado a partir do diagnostico deterministico.
create table if not exists public.recommendations (
  id uuid primary key default gen_random_uuid()
);

alter table public.recommendations add column if not exists owner_id uuid;
alter table public.recommendations add column if not exists client_id uuid;
alter table public.recommendations add column if not exists period text;
alter table public.recommendations add column if not exists snapshot jsonb not null default '{}'::jsonb;
alter table public.recommendations add column if not exists content text;
alter table public.recommendations add column if not exists model text default '';
alter table public.recommendations add column if not exists created_at timestamptz not null default now();

create index if not exists recommendations_client_period_idx
  on public.recommendations (client_id, period, created_at desc);

alter table public.recommendations enable row level security;

drop policy if exists "recommendations_owner_select" on public.recommendations;
create policy "recommendations_owner_select" on public.recommendations
  for select using (auth.uid() = owner_id);

-- Central de acoes: decisoes operacionais aprovadas, rejeitadas ou concluidas.
create table if not exists public.action_items (
  id uuid primary key default gen_random_uuid()
);

alter table public.action_items add column if not exists owner_id uuid;
alter table public.action_items add column if not exists client_id uuid;
alter table public.action_items add column if not exists period text;
alter table public.action_items add column if not exists campaign_external_id text not null default '';
alter table public.action_items add column if not exists campaign_name text;
alter table public.action_items add column if not exists title text;
alter table public.action_items add column if not exists action text;
alter table public.action_items add column if not exists impact text;
alter table public.action_items add column if not exists severity integer not null default 1;
alter table public.action_items add column if not exists tone text not null default 'blue';
alter table public.action_items add column if not exists status text not null default 'open';
alter table public.action_items add column if not exists approved_at timestamptz;
alter table public.action_items add column if not exists rejected_at timestamptz;
alter table public.action_items add column if not exists completed_at timestamptz;
alter table public.action_items add column if not exists created_at timestamptz not null default now();
alter table public.action_items add column if not exists updated_at timestamptz not null default now();

create unique index if not exists action_items_unique_decision_idx
  on public.action_items (owner_id, client_id, period, campaign_external_id, title);

alter table public.action_items enable row level security;

drop policy if exists "action_items_owner_select" on public.action_items;
create policy "action_items_owner_select" on public.action_items
  for select using (auth.uid() = owner_id);
