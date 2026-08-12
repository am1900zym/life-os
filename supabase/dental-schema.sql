-- ============================================================
-- 口腔视界 DentaScope — Supabase Schema v1.0
-- 口腔医学 & 口腔护理内容库（论文/病例/护理/视频/书/影像）
-- 参考 alohomora.live 内容结构
-- ============================================================

-- 1. dental_papers（论文库）
create table if not exists public.dental_papers (
  id uuid default gen_random_uuid() primary key,
  pmid text,                        -- PubMed PMID (去重)
  title text not null,
  authors text,
  journal text not null,
  journal_zh text,                  -- 期刊中文名
  published_on date not null,
  doi text,                         -- DOI
  url text,
  abstract text,
  paper_type text default '研究',  -- 研究/综述/临床/实验室/政策
  tags text[] default '{}',
  is_new boolean default true,
  created_at timestamptz default now(),
  unique (pmid)
);

-- 2. dental_nursing（口腔护理要点）
create table if not exists public.dental_nursing (
  id uuid default gen_random_uuid() primary key,
  title text not null,
  category text not null,  -- 预防/治疗/紧急/儿科/老年
  summary text,
  url text,
  published_on date default current_date,
  created_at timestamptz default now()
);

-- 3. dental_cases（临床病例）
create table if not exists public.dental_cases (
  id uuid default gen_random_uuid() primary key,
  title text not null,
  patient text,            -- '58M' 等
  diagnosis text,
  specialty text not null, -- 口腔颌面外科/种植修复/儿童牙科/牙体牙髓
  summary text,
  image_url text,
  url text,
  published_on date default current_date,
  created_at timestamptz default now()
);

-- 4. dental_videos（视频/讲座）
create table if not exists public.dental_videos (
  id uuid default gen_random_uuid() primary key,
  title text not null,
  channel text,
  category text default '讲座',  -- 手术/讲座/教学/研讨
  duration text,
  url text,
  published_on date default current_date,
  created_at timestamptz default now()
);

-- 5. dental_books（书库）
create table if not exists public.dental_books (
  id uuid default gen_random_uuid() primary key,
  title text not null,
  author text,
  category text default '教科书', -- 教科书/临床/考试/研究
  publish_year integer,
  description text,
  url text,
  created_at timestamptz default now()
);

-- 6. dental_scans（影像档案）
create table if not exists public.dental_scans (
  id uuid default gen_random_uuid() primary key,
  title text not null,
  modality text not null,  -- 全景片/CBCT/根尖片
  finding text,
  image_url text,
  published_on date default current_date,
  created_at timestamptz default now()
);

-- ============================================================
-- Row Level Security — 默认仅登录用户可写，公开可读
-- ============================================================
alter table public.dental_papers enable row level security;
alter table public.dental_nursing enable row level security;
alter table public.dental_cases enable row level security;
alter table public.dental_videos enable row level security;
alter table public.dental_books enable row level security;
alter table public.dental_scans enable row level security;

create policy "dental_papers public read" on public.dental_papers for select using (true);
create policy "dental_papers insert" on public.dental_papers for insert with check (auth.role() = 'authenticated');
create policy "dental_nursing public read" on public.dental_nursing for select using (true);
create policy "dental_nursing insert" on public.dental_nursing for insert with check (auth.role() = 'authenticated');
create policy "dental_cases public read" on public.dental_cases for select using (true);
create policy "dental_cases insert" on public.dental_cases for insert with check (auth.role() = 'authenticated');
create policy "dental_videos public read" on public.dental_videos for select using (true);
create policy "dental_videos insert" on public.dental_videos for insert with check (auth.role() = 'authenticated');
create policy "dental_books public read" on public.dental_books for select using (true);
create policy "dental_books insert" on public.dental_books for insert with check (auth.role() = 'authenticated');
create policy "dental_scans public read" on public.dental_scans for select using (true);
create policy "dental_scans insert" on public.dental_scans for insert with check (auth.role() = 'authenticated');

-- 索引
create index if not exists idx_dental_papers_date on public.dental_papers(published_on desc);
create index if not exists idx_dental_papers_journal on public.dental_papers(journal);
create index if not exists idx_dental_nursing_cat on public.dental_nursing(category);
create index if not exists idx_dental_cases_specialty on public.dental_cases(specialty);

-- 7. dental_saved — 用户收藏/保存的论文与内容 (参考 Alohomora /red/ "我的收藏")
create table if not exists public.dental_saved (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references public.profiles(id) on delete cascade,
  ref_type text not null default 'paper',  -- paper/book/case/video/nursing/scan
  ref_id text not null,                    -- 对应 dental_papers.id / dental_books.id 等
  pmid text,                               -- PubMed PMID (论文专用, 用于去重)
  is_starred boolean default true,         -- 精选 (Alohomora 中的 ★)
  note text,                               -- 用户备注
  created_at timestamptz default now(),
  unique(user_id, ref_type, ref_id)
);
alter table public.dental_saved enable row level security;
create policy "saved read" on public.dental_saved for select using (auth.uid() = user_id or user_id is null);
create policy "saved write" on public.dental_saved for all using (auth.uid() = user_id or user_id is null);
create index if not exists idx_dental_saved_user on public.dental_saved(user_id, is_starred, created_at desc);
create index if not exists idx_dental_saved_pmid on public.dental_saved(pmid);
