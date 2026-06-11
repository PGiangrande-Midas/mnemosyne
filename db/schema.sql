-- Enable pgvector (run once in Supabase SQL editor)
create extension if not exists vector;

create table if not exists contacts (
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

create table if not exists interactions (
  id uuid primary key default gen_random_uuid(),
  contact_id uuid references contacts(id),
  date date,
  topic text,
  summary text,
  next_steps text,
  sentiment text
);

create table if not exists memories (
  id uuid primary key default gen_random_uuid(),
  contact_id uuid references contacts(id),
  content text,
  embedding vector(1536),
  created_at timestamp default now()
);

create index if not exists memories_embedding_idx
on memories using ivfflat (embedding vector_cosine_ops)
with (lists = 100);

-- Disable RLS for private dev (anon key needs full access)
alter table contacts disable row level security;
alter table interactions disable row level security;
alter table memories disable row level security;

-- Required for cosine similarity search via Supabase RPC
grant usage on schema public to anon;
grant select on memories to anon;

create or replace function match_memories(
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
  from memories
  order by embedding <=> query_embedding
  limit match_count;
$$;

grant execute on function match_memories to anon;
