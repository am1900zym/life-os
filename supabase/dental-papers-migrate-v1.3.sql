-- ============================================================
-- 口腔视界 DentaScope — dental_papers 约束修复 v1.3
-- 问题: v1.1 用的是部分唯一索引 (WHERE pmid is not null),
--       PostgREST 的 on_conflict 不识别 partial index → upsert 409。
-- 修复: 换成普通 UNIQUE 约束 (NULL 不参与唯一性, 语义相同)。
-- 幂等, 可重复执行
-- ============================================================

-- 1. 删除旧的部分唯一索引
drop index if exists dental_papers_pmid_key;

-- 2. 加普通唯一约束 (PostgREST on_conflict 可识别)
alter table public.dental_papers
  add constraint dental_papers_pmid_key unique (pmid);
