-- ============================================================
-- 口腔视界 DentaScope — dental_papers 表升级 v1.2
-- 新增: 中文标题 / 中文标签 / OA 全文信息
-- 幂等, 可重复执行
-- ============================================================

ALTER TABLE dental_papers
  ADD COLUMN IF NOT EXISTS title_zh text,
  ADD COLUMN IF NOT EXISTS tags_zh text[] DEFAULT '{}',
  ADD COLUMN IF NOT EXISTS pmc_id text,
  ADD COLUMN IF NOT EXISTS is_oa boolean DEFAULT false,
  ADD COLUMN IF NOT EXISTS full_text_url text;

-- OA 过滤加速索引
CREATE INDEX IF NOT EXISTS idx_dental_papers_is_oa ON dental_papers (is_oa);
CREATE INDEX IF NOT EXISTS idx_dental_papers_pmc_id ON dental_papers (pmc_id);

-- 中文标签数组索引用 GIN (如需按标签检索)
CREATE INDEX IF NOT EXISTS idx_dental_papers_tags_zh ON dental_papers USING GIN (tags_zh);

-- 回填: 已有的 tags_zh 空数组 (无历史数据可回填, 仅保证默认值)
UPDATE dental_papers SET tags_zh = '{}' WHERE tags_zh IS NULL;
UPDATE dental_papers SET is_oa = false WHERE is_oa IS NULL;
