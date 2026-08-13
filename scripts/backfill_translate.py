#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DentaScope — 中文标题回填翻译脚本
===================================
从 Supabase dental_papers 拉取 title_zh 为空的记录，
用 DeepL API (优先) 或 MyMemory 免费 API (兜底) 批量翻译标题，
再写回 Supabase。

用法:
    # DeepL (推荐, 每月 50 万字符免费):
    #   1. 去 https://www.deepl.com/pro-api 注册拿 API key
    #   2. export DEEPL_API_KEY=你的key
    #   3. python scripts/backfill_translate.py

    # 无 key 时自动降级 MyMemory 免费 API (无需注册, 每天限额 5000 字符)
    python scripts/backfill_translate.py

    # 只翻译不写库
    python scripts/backfill_translate.py --dry-run

    # 指定翻译条数上限 (默认全部, 建议先跑 --limit 20 测试)
    python scripts/backfill_translate.py --limit 20

环境变量:
    SUPABASE_URL          必填
    SUPABASE_SERVICE_KEY  必填
    DEEPL_API_KEY         可选 (设置则用 DeepL, 否则 MyMemory 兜底)
"""

import argparse
import json
import os
import sys
import time

import requests

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")
DEEPL_API_KEY = os.environ.get("DEEPL_API_KEY")

DEEPL_URL = "https://api-free.deepl.com/v2/translate"
MYMEMORY_URL = "https://api.mymemory.translated.net/get"
MYMEMORY_DAILY_LIMIT = 5000  # MyMemory 免费档每日限额 (字符)

# 翻译缓存: 相同标题只翻一次
_cache: dict = {}


def translate_deepl(text: str) -> str:
    """DeepL 翻译 (免费版 api-free 端点)"""
    r = requests.post(DEEPL_URL, data={
        "auth_key": DEEPL_API_KEY,
        "text": text[:5000],
        "target_lang": "ZH",
        "source_lang": "EN",
    }, timeout=20)
    r.raise_for_status()
    return r.json()["translations"][0]["text"]


def translate_mymemory(text: str) -> str:
    """MyMemory 免费翻译 (无需 key, 单次请求文本 ≤500 字符)"""
    r = requests.get(MYMEMORY_URL, params={
        "q": text[:500],
        "langpair": "en|zh-CN",
    }, timeout=20)
    r.raise_for_status()
    data = r.json()
    status = data.get("responseStatus")
    if status != 200:
        raise RuntimeError(f"MyMemory status {status}: {data.get('responseDetails')}")
    return data.get("responseData", {}).get("translatedText", "")


def translate(text: str) -> str:
    """翻译: DeepL 优先, 失败/无 key 则 MyMemory 兜底"""
    if not text:
        return ""
    if text in _cache:
        return _cache[text]
    result = ""
    if DEEPL_API_KEY:
        try:
            result = translate_deepl(text)
        except Exception as e:
            print(f"    ⚠️ DeepL 失败 ({e}), 降级 MyMemory")
            time.sleep(1)
    if not result:
        try:
            result = translate_mymemory(text)
        except Exception as e:
            print(f"    ⚠️ MyMemory 也失败: {e}")
            result = ""
    _cache[text] = result
    time.sleep(0.3)  # 限速
    return result


def fetch_empty(supabase_url, key, limit=None):
    """拉取 title_zh 为空的记录"""
    url = f"{supabase_url}/rest/v1/dental_papers"
    params = {"select": "pmid,title", "title_zh": "is.null", "order": "published_on.desc"}
    if limit:
        params["limit"] = limit
    r = requests.get(url, headers={
        "apikey": key,
        "Authorization": f"Bearer {key}",
    }, params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def fetch_all(supabase_url, key):
    """拉取全部记录 (title_zh 空或与原文相同则需重翻)"""
    url = f"{supabase_url}/rest/v1/dental_papers"
    r = requests.get(url, headers={
        "apikey": key,
        "Authorization": f"Bearer {key}",
    }, params={"select": "pmid,title,title_zh", "order": "published_on.desc"}, timeout=60)
    r.raise_for_status()
    return r.json()


def update_title_zh(supabase_url, key, pmid, title_zh):
    """写回单个记录的中文标题"""
    url = f"{supabase_url}/rest/v1/dental_papers"
    r = requests.patch(url, headers={
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }, params={"pmid": f"eq.{pmid}"}, json={"title_zh": title_zh}, timeout=30)
    r.raise_for_status()
    return True


def main():
    parser = argparse.ArgumentParser(description="DentaScope 中文标题回填翻译")
    parser.add_argument("--dry-run", action="store_true", help="只翻译不写库")
    parser.add_argument("--limit", type=int, default=None, help="最多处理 N 条 (默认全部)")
    parser.add_argument("--skip", type=int, default=0, help="跳过前 N 条 (用于续跑)")
    parser.add_argument("--oa-only", action="store_true", help="只翻译 is_oa=true 的文章")
    parser.add_argument("--char-limit", type=int, default=4400, help="MyMemory 每日字符上限 (默认 4400, 安全留档)")
    args = parser.parse_args()

    if not SUPABASE_URL or not SERVICE_KEY:
        print("ERROR: 需要环境变量 SUPABASE_URL 和 SUPABASE_SERVICE_KEY")
        sys.exit(1)

    print(f"翻译后端: {'DeepL' if DEEPL_API_KEY else 'MyMemory (免费, 未设置 DEEPL_API_KEY)'}")
    print("拉取待翻译记录...")
    rows = fetch_empty(SUPABASE_URL, SERVICE_KEY, args.limit, args.skip, args.oa_only)
    if not rows:
        print("✅ 没有 title_zh 为空的记录 (可能已全部翻译)")
        return

    print(f"待翻译: {len(rows)} 条 | 字符上限: {args.char_limit}")
    ok, fail, skipped = 0, 0, 0
    chars_used = 0
    for i, row in enumerate(rows, 1):
        title = row.get("title", "")
        char_cost = len(title[:500])
        if chars_used + char_cost > args.char_limit:
            skipped += 1
            continue
        chars_used += char_cost
        print(f"  [{i}/{len(rows)}] PMID {row.get('pmid')}: {title[:60]}...")
        zh = translate(title)
        if not zh:
            fail += 1
            print(f"    ❌ 翻译失败, 跳过")
            continue
        print(f"    ✅ {zh[:60]}")
        if not args.dry_run:
            try:
                update_title_zh(SUPABASE_URL, SERVICE_KEY, row["pmid"], zh)
                ok += 1
            except Exception as e:
                fail += 1
                print(f"    ❌ 写库失败: {e}")
        else:
            ok += 1

    print(f"\n完成: 成功 {ok}, 失败 {fail}, 跳过(字符超限) {skipped} | 字符耗用 {chars_used}/{args.char_limit}")


def fetch_empty(supabase_url, service_key, limit=None, skip=0, oa_only=False):
    """拉取 title_zh 为空的记录"""
    if not service_key:
        raise RuntimeError("Missing SUPABASE_SERVICE_KEY")
    url = f"{supabase_url}/rest/v1/dental_papers"
    params = {
        "select": "pmid,title",
        # tracker 写入时 title_zh 是空字符串 "" (不是 NULL), 所以用 eq. 而非 is.null
        "title_zh": "eq.",
        "order": "published_on.desc",
    }
    if skip:
        params["offset"] = str(skip)
    if limit:
        params["limit"] = str(limit)
    # is_oa filter 放在 params 字典 (requests 會正確 encoding)
    if oa_only:
        params["is_oa"] = "eq.true"
    r = requests.get(url, headers={
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}",
    }, params=params, timeout=30)
    if r.status_code == 206:
        return r.json()
    if r.status_code == 401:
        raise RuntimeError("Supabase 認證失敗: 請確認 SUPABASE_SERVICE_KEY")
    r.raise_for_status()
    return r.json()


if __name__ == "__main__":
    main()
