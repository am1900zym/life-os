@echo off
REM ============================================================
REM DentaScope 中文标题回填 —— 双语翻译回补脚本
REM 用法: 双击运行, 或在 PowerShell: .\run-translate.bat
REM 只需填入你的 service_role key (從 Supabase Dashboard 複製)
REM ============================================================
set SUPABASE_URL=https://cionltpnftwxohrzgcfh.supabase.co

REM ==== 在下面貼上你的 service_role key (從 Supabase Dashboard → Settings → API → service_role) ====
set SUPABASE_SERVICE_KEY=YOUR_SERVICE_ROLE_KEY_HERE
REM ==== 貼上完畢 ====

cd /d E:\Projects\LifeOS

echo.
echo === [1/3] 翻译 OA 全文标的标题 (优先) ===
python scripts/backfill_translate.py --oa-only --limit 50 --char-limit 4400
echo.

echo === [2/3] 翻译剩余非OA标题 (分批, 每次 45 篇) ===
python scripts/backfill_translate.py --limit 45 --char-limit 4400 --skip 0
echo.

echo === [3/3] 全部完成 ===
pause
