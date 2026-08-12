#!/usr/bin/env bash
# 口腔视界 DentaScope — 每日论文追踪 cron 脚本
# 每日 08:00 自动从 PubMed 抓取最新 7 天论文 -> 写入 Supabase
# 环境变量 (在 CF Pages 或本地 .env 配置):
#   SUPABASE_URL=https://cionlupntwxohrzjgcff.supabase.co
#   SUPABASE_SERVICE_KEY=eyJ... (service_role)
set -e
cd /e/Projects/LifeOS || exit 1
python scripts/dental_tracker.py --days 7 2>&1
