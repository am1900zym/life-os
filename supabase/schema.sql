-- Life OS Supabase Schema v1.0

-- 1. Profiles（用户主表）
create table public.profiles (
  id uuid references auth.users on delete cascade primary key,
  name text not null,
  handle text unique,
  avatar_url text,
  theme text default 'deep-blue',
  created_at timestamptz default now()
);

-- 2. Moments（人生瞬间）
create table public.moments (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references public.profiles(id) on delete cascade not null,
  type text not null default '💡 想法',
  title text not null,
  body text,
  media_urls text[] default '{}',
  occurred_at timestamptz default now(),
  visibility text default 'private',
  created_at timestamptz default now()
);

-- 3. Friends（好友关系，双向确认）
create table public.friends (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references public.profiles(id) on delete cascade not null,
  friend_id uuid references public.profiles(id) on delete cascade not null,
  status text default 'pending',
  shared_categories text[] default '{}',
  created_at timestamptz default now(),
  unique(user_id, friend_id)
);

-- 4. Shared Moments（共同瞬间）
create table public.shared_moments (
  id uuid default gen_random_uuid() primary key,
  moment_id uuid references public.moments(id) on delete cascade not null,
  participants uuid[] not null,
  ai_summary text,
  created_at timestamptz default now()
);

-- Row Level Security
alter table public.profiles enable row level security;
alter table public.moments enable row level security;
alter table public.friends enable row level security;
alter table public.shared_moments enable row level security;

-- 策略
create policy "Users read own profile" on public.profiles for select using (auth.uid() = id);
create policy "Users update own profile" on public.profiles for update using (auth.uid() = id);
create policy "Users insert own moments" on public.moments for insert with check (user_id = 'ec4e72df-c496-4d45-830e-71787bb281a5');
create policy "Users read own moments" on public.moments for select using (auth.uid() = user_id or visibility = 'public');
create policy "Users update own moments" on public.moments for update using (user_id = 'ec4e72df-c496-4d45-830e-71787bb281a5') with check (user_id = 'ec4e72df-c496-4d45-830e-71787bb281a5');
create policy "Users delete own moments" on public.moments for delete using (user_id = 'ec4e72df-c496-4d45-830e-71787bb281a5');
create policy "Users manage own friends" on public.friends for all using (auth.uid() = user_id or auth.uid() = friend_id);
create policy "Read shared moments" on public.shared_moments for select using (auth.uid() = any(participants));

-- 索引
create index idx_moments_user on public.moments(user_id, occurred_at desc);
create index idx_friends_user on public.friends(user_id, friend_id);
