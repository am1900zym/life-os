-- ============================================================
-- Life OS · 修复 moments 表 RLS 策略（缺失导致「删除/编辑」无效）
-- 应用场景：前端使用匿名 anon key + 写死 user_id，不依赖真实登录
-- 因此策略按固定 user_id 常量放行，可重复执行（幂等）
-- ============================================================

-- 先清理可能已存在的同名策略，避免重复创建报错
drop policy if exists "Users insert own moments" on public.moments;
drop policy if exists "Users update own moments" on public.moments;
drop policy if exists "Users delete own moments" on public.moments;

-- 插入：允许应用写入属于该用户的记录
create policy "Users insert own moments" on public.moments
  for insert with check (user_id = 'ec4e72df-c496-4d45-830e-71787bb281a5');

-- 更新：允许应用修改属于该用户的记录
create policy "Users update own moments" on public.moments
  for update using (user_id = 'ec4e72df-c496-4d45-830e-71787bb281a5')
  with check (user_id = 'ec4e72df-c496-4d45-830e-71787bb281a5');

-- 删除：允许应用删除属于该用户的记录（当前缺失，正是「删不掉」的根因）
create policy "Users delete own moments" on public.moments
  for delete using (user_id = 'ec4e72df-c496-4d45-830e-71787bb281a5');

-- 注意：select 策略保持原样（auth.uid() = user_id or visibility = 'public'）即可
