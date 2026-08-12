-- 口腔视界 DentaScope — dental_papers 加列迁移 (v1.0 → v1.1)
-- 在 Supabase SQL Editor 中整段粘贴执行
alter table public.dental_papers
  add column if not exists pmid text,
  add column if not exists journal_zh text,
  add column if not exists doi text;

-- 为 pmid 加唯一约束 (upsert 去重依赖)
create unique index if not exists dental_papers_pmid_key
  on public.dental_papers(pmid)
  where pmid is not null;
