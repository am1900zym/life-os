-- Life OS 评论功能 SQL（已按无 Auth 的单用户模式放宽）
-- 执行后，前端即可在详情弹窗中新增/读取评论

create table if not exists public.comments (
  id uuid default gen_random_uuid() primary key,
  moment_id uuid references public.moments(id) on delete cascade not null,
  user_id text not null,
  nickname text not null default 'Amanda',
  content text not null,
  created_at timestamptz default now()
);

alter table public.comments enable row level security;

-- 允许 anon key 读取评论
create policy "Public read comments" on public.comments for select using (true);
-- 允许 anon key 插入评论
create policy "Public insert comments" on public.comments for insert with check (true);

create index if not exists idx_comments_moment on public.comments(moment_id, created_at asc);
