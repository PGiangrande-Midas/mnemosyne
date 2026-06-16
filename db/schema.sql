-- Mnemosyne working tables. These live in the shared Pantheon Supabase
-- project alongside the Metis `runs` table (one project, many tables).
--
-- Security posture: RLS stays ON and anon gets NO access. Mnemosyne reads and
-- writes with the service_role key, which bypasses RLS, so its operations work
-- while contact and interaction data stays private, mirroring how `runs` is
-- protected. Run once in the Supabase SQL editor. Idempotent: safe to re-run.

create extension if not exists vector;

create table if not exists public.contacts (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  company text,
  role text,
  email text,
  last_contact date,
  status text default 'active',
  created_at timestamp default now(),
  updated_at timestamp default now()
);

create table if not exists public.interactions (
  id uuid primary key default gen_random_uuid(),
  contact_id uuid references public.contacts(id),
  date date,
  topic text,
  summary text,
  next_steps text,
  sentiment text
);

create table if not exists public.memories (
  id uuid primary key default gen_random_uuid(),
  contact_id uuid references public.contacts(id),
  content text,
  embedding vector(1536),
  created_at timestamp default now()
);

create index if not exists memories_embedding_idx
  on public.memories using ivfflat (embedding vector_cosine_ops)
  with (lists = 100);

-- RLS ON, no policies, no anon access. Only service_role (which bypasses RLS)
-- can read or write. Do NOT disable RLS or grant anon here: that would expose
-- contact data in the shared project.
alter table public.contacts     enable row level security;
alter table public.interactions enable row level security;
alter table public.memories     enable row level security;

revoke all on public.contacts     from anon, authenticated;
revoke all on public.interactions from anon, authenticated;
revoke all on public.memories     from anon, authenticated;

-- Cosine-similarity helper. Callable only by the service role, not anon.
create or replace function public.match_memories(
  query_embedding vector(1536),
  match_count int default 5
)
returns table (
  id uuid,
  contact_id uuid,
  content text,
  similarity float
)
language sql stable
as $$
  select id, contact_id, content,
    1 - (embedding <=> query_embedding) as similarity
  from public.memories
  order by embedding <=> query_embedding
  limit match_count;
$$;

revoke all on function public.match_memories(vector, int) from public;
grant execute on function public.match_memories(vector, int) to service_role;
