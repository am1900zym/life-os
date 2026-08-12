#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
口腔视界 DentaScope — 期刊自动追踪器
=====================================
通过 PubMed E-utilities (NCBI) 自动追踪口腔医学期刊的最新论文，
解析元数据后写入 Supabase dental_papers 表。

用法:
    python scripts/dental_tracker.py              # 默认追踪最近 7 天
    python scripts/dental_tracker.py --days 14    # 追踪最近 14 天
    python scripts/dental_tracker.py --dry-run    # 只打印不写库

环境变量:
    SUPABASE_URL          必填, e.g. https://xxxx.supabase.co
    SUPABASE_SERVICE_KEY  必填, service_role key (写入用, 勿入前端)
    可选: SUPABASE_ANON_KEY (仅用于测试查询)

原理:
    esearch 按期刊 + 日期过滤拿 PMID 列表 → efetch 批量取元数据 →
    解析 → 与库中已有 PMID 去重 → 批量 upsert
"""
import argparse
import json
import os
import re
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

import requests

# NCBI E-utilities 需要直连 (本机 Clash 代理会中断连接)
os.environ["NO_PROXY"] = "eutils.ncbi.nlm.nih.gov,www.ncbi.nlm.nih.gov,api.ncbi.nlm.nih.gov"
os.environ["no_proxy"] = os.environ["NO_PROXY"]

# ---------------------------------------------------------------
# 追踪的期刊清单 (PubMed journal title + 中文明)
# ---------------------------------------------------------------
JOURNALS = [
    {"title": "Journal of Dental Research", "zh": "牙科研究杂志", "issn": "0022-0345"},
    {"title": "Journal of Clinical Periodontology", "zh": "临床牙周病学杂志", "issn": "0303-6979"},
    {"title": "Journal of Endodontics", "zh": "牙髓病学杂志", "issn": "0099-2399"},
    {"title": "Journal of Periodontology", "zh": "牙周病学杂志", "issn": "0022-3492"},
    {"title": "Journal of Prosthetic Dentistry", "zh": "修复牙科杂志", "issn": "0022-3913"},
    {"title": "International Journal of Paediatric Dentistry", "zh": "国际儿童牙科杂志", "issn": "0960-7439"},
    {"title": "Community Dentistry and Oral Epidemiology", "zh": "社区口腔与流行病学", "issn": "0301-5661"},
    {"title": "Journal of Oral Rehabilitation", "zh": "口腔康复杂志", "issn": "0305-182X"},
    {"title": "Journal of Dental Sciences", "zh": "牙科科学杂志", "issn": "1991-7902"},
    {"title": "BMC Oral Health", "zh": "BMC 口腔健康", "issn": "1472-6831"},
]

NCBI_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
TOOL = "DentaScopeTracker"
EMAIL = "dentascope@example.com"  # NCBI 要求提供联系方式


def ncbi_params(**kw):
    p = {"tool": TOOL, "email": EMAIL}
    p.update(kw)
    return p


def search_pmids(journal_title, start_date, end_date, retmax=30):
    """esearch: 按期刊 + 出版日期区间拿 PMID 列表（按入库时间排序取最新）"""
    term = f'"{journal_title}"[jour] AND {start_date}[dp] : {end_date}[dp]'
    url = f"{NCBI_BASE}/esearch.fcgi"
    r = requests.get(url, params=ncbi_params(db="pubmed", term=term,
                                             retmax=retmax, retmode="json", sort="pub date"),
                     timeout=30)
    r.raise_for_status()
    data = r.json()
    return data.get("esearchresult", {}).get("idlist", [])


def fetch_articles(pmids):
    """efetch: 批量取文章元数据 XML"""
    if not pmids:
        return []
    url = f"{NCBI_BASE}/efetch.fcgi"
    r = requests.get(url, params=ncbi_params(db="pubmed", id=",".join(pmids), retmode="xml"),
                     timeout=40)
    r.raise_for_status()
    return parse_pubmed_xml(r.text)


def text_of(el):
    return "".join(el.itertext()).strip() if el is not None else ""


def parse_pubmed_xml(xml_text):
    """解析 PubMed XML → 文章字典列表"""
    articles = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return articles

    for art in root.findall(".//PubmedArticle"):
        medline = art.find("MedlineCitation")
        if medline is None:
            continue

        pmid = text_of(medline.find("PMID"))
        article = medline.find("Article")
        if article is None:
            continue

        # 标题
        title = text_of(article.find("ArticleTitle"))
        # 去 HTML 标签
        title = re.sub(r"<[^>]+>", "", title)

        # 期刊
        journal_el = article.find("Journal")
        journal = text_of(journal_el.find("Title")) if journal_el is not None else ""

        # 作者
        authors = []
        alist = article.find("AuthorList")
        if alist is not None:
            for a in alist.findall("Author"):
                last = text_of(a.find("LastName"))
                fore = text_of(a.find("ForeName"))
                collective = text_of(a.find("CollectiveName"))
                if collective:
                    authors.append(collective)
                elif last:
                    authors.append(f"{fore} {last}".strip())
        authors_str = ", ".join(authors[:6])

        # 日期 (ArticleDate 优先, 否则 PubDate)
        pub_date = ""
        adate = article.find("ArticleDate")
        if adate is not None:
            y = text_of(adate.find("Year"))
            m = text_of(adate.find("Month"))
            d = text_of(adate.find("Day"))
            pub_date = f"{y}-{m.zfill(2)}-{d.zfill(2)}" if y else ""
        if not pub_date:
            pdate = article.find("Journal/JournalIssue/PubDate")
            if pdate is not None:
                y = text_of(pdate.find("Year"))
                m = text_of(pdate.find("Month"))
                pub_date = f"{y}-{m or '01'}-01" if y else ""

        # DOI
        doi = ""
        for eid in article.findall(".//ELocationID[@EIdType='doi']"):
            doi = text_of(eid)
            break
        if not doi:
            aid = art.find(".//ArticleId[@IdType='doi']")
            doi = text_of(aid)

        # 摘要
        abstract_parts = []
        for ab in article.findall(".//AbstractText"):
            label = ab.get("Label")
            txt = text_of(ab)
            abstract_parts.append(f"{label}: {txt}" if label else txt)
        abstract = " ".join(abstract_parts)[:2000]

        # 文献类型 (研究/综述/临床/实验室/政策 归类)
        ptypes = [text_of(p) for p in article.findall(".//PublicationType")]
        paper_type = "研究"
        if any("Review" in t for t in ptypes):
            paper_type = "综述"
        elif any("Clinical Trial" in t or "Randomized" in t for t in ptypes):
            paper_type = "临床"
        elif any("Comment" in t or "Editorial" in t or "Letter" in t or "Erratum" in t or "Corrigendum" in t for t in ptypes):
            paper_type = "政策"

        # 标签: 提取摘要关键词
        tags = []
        keyword_list = art.find(".//KeywordList")
        if keyword_list is not None:
            tags = [text_of(k) for k in keyword_list.findall("Keyword")][:5]

        articles.append({
            "pmid": pmid,
            "title": title,
            "authors": authors_str,
            "journal": journal,
            "journal_zh": next((j["zh"] for j in JOURNALS if j["title"].lower() == journal.lower()), journal),
            "date": pub_date,
            "doi": doi,
            "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else doi,
            "abstract": abstract,
            "type": paper_type,
            "tags": tags,
            "is_new": True,
        })
    return articles


def fetch_existing_pmids(supabase_url, service_key):
    """从 Supabase 读取已入库的 PMID (去重用)"""
    url = f"{supabase_url}/rest/v1/dental_papers?select=pmid"
    r = requests.get(url, headers={
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}",
    }, timeout=30)
    if r.status_code == 401 or r.status_code == 404:
        # 表不存在/未授权 (首次运行), 返回空 set
        return set()
    r.raise_for_status()
    return {row.get("pmid") for row in r.json() if row.get("pmid")}


def ensure_tables(supabase_url, service_key):
    """自检: 如果 dental_papers 表不存在, 返回 False 提示需要先建表.
    (Supabase REST API 无法建表, 只读/写数据; 建表须用 SQL Editor 或 Management API.)
    返回 True=表存在/可写, False=需手动建.
    """
    url = f"{supabase_url}/rest/v1/dental_papers?select=count"
    r = requests.get(url, headers={
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}",
        "Prefer": "count=exact",
    }, timeout=30)
    # 200 = 表存在; 404/405 = 不存在或无权 (service_role 应能 200)
    return r.status_code == 200


def upsert_articles(supabase_url, service_key, articles):
    """批量写入 Supabase (upsert on pmid)"""
    if not articles:
        return 0
    url = f"{supabase_url}/rest/v1/dental_papers"
    # 字段映射: tracker JSON 字段 → 表列名
    rows = [{
        "pmid": a.get("pmid"),
        "title": a.get("title"),
        "authors": a.get("authors", ""),
        "journal": a.get("journal"),
        "journal_zh": a.get("journal_zh", ""),
        "published_on": a.get("date"),
        "doi": a.get("doi", ""),
        "url": a.get("url"),
        "abstract": a.get("abstract", ""),
        "paper_type": a.get("type", "研究"),
        "tags": a.get("tags", []),
        "is_new": a.get("is_new", True),
    } for a in articles]
    r = requests.post(url, headers={
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates,return=minimal",
    }, json=rows, timeout=60)
    r.raise_for_status()
    return len(articles)


def main():
    parser = argparse.ArgumentParser(description="DentaScope 期刊追踪器")
    parser.add_argument("--days", type=int, default=7, help="回溯天数 (默认 7)")
    parser.add_argument("--dry-run", action="store_true", help="只打印不写库")
    parser.add_argument("--journal", default=None, help="只追踪指定期刊 (默认全部)")
    parser.add_argument("--json", dest="as_json", action="store_true", help="输出 JSON 到 stdout (配合 --out 使用)")
    parser.add_argument("--out", default=None, help="写入 JSON 文件路径 (默认 stdout)")
    args = parser.parse_args()

    supabase_url = os.environ.get("SUPABASE_URL")
    service_key = os.environ.get("SUPABASE_SERVICE_KEY")
    if not (args.dry_run or args.as_json) and (not supabase_url or not service_key):
        print(f"ERROR: 需要环境变量 SUPABASE_URL 和 SUPABASE_SERVICE_KEY (dry-run/--json 除外)")
        sys.exit(1)

    end = datetime.now()
    start = end - timedelta(days=args.days)
    start_str = start.strftime("%Y/%m/%d")
    end_str = end.strftime("%Y/%m/%d")

    journals = [j for j in JOURNALS if args.journal is None or j["title"].lower() == args.journal.lower()]
    if not journals:
        print(f"未找到期刊: {args.journal}")
        sys.exit(1)

    print(f"[{datetime.now():%H:%M:%S}] 追踪区间: {start_str} - {end_str}")

    # 自检: 表是否存在 (写库前检查)
    if not args.dry_run and not args.as_json:
        if not ensure_tables(supabase_url, service_key):
            print(f"⚠️  表 dental_papers 不存在! 请先在 Supabase SQL Editor 执行:")
            print(f"   supabase/dental-schema.sql")
            print(f"   或访问: {supabase_url} → SQL Editor → 贴入 schema → 运行")
            sys.exit(1)

    # 已入库 PMID (去重)
    existing = set()
    if not args.dry_run:
        try:
            existing = fetch_existing_pmids(supabase_url, service_key)
            print(f"已入库 {len(existing)} 条")
        except Exception as e:
            print(f"读取已有记录失败(首次运行可忽略): {e}")

    all_new = []
    seen_pmids = set()
    for j in journals:
        try:
            pmids = search_pmids(j["title"], start_str, end_str)
            print(f"  {j['title']}: {len(pmids)} 篇")
        except Exception as e:
            print(f"  {j['title']}: 查询失败 - {e}")
            continue
        if not pmids:
            continue

        # 分批 efetch (每次最多 50)
        for i in range(0, len(pmids), 50):
            batch = pmids[i:i + 50]
            try:
                arts = fetch_articles(batch)
            except Exception as e:
                print(f"    批次 {i//50}: 获取失败 - {e}")
                time.sleep(1)
                continue
            for a in arts:
                if a["pmid"] in existing or a["pmid"] in seen_pmids:
                    continue
                seen_pmids.add(a["pmid"])
                all_new.append(a)
            time.sleep(0.4)  # NCBI 限速: 无 API key 3 req/s

    print(f"\\n新论文: {len(all_new)} 篇")

    if args.as_json:
        out = json.dumps(all_new, ensure_ascii=False, indent=2, default=str)
        if args.out:
            with open(args.out, "w", encoding="utf-8") as f:
                f.write(out)
            print(f"✅ JSON 写入: {args.out}")
        else:
            print(out)
        return

    if args.dry_run:
        for a in all_new[:20]:
            print(f"  [{a['date']}] {a['journal']} | {a['title'][:70]}")
        return

    if all_new:
        try:
            n = upsert_articles(supabase_url, service_key, all_new)
            print(f"✅ 已写入 Supabase: {n} 条")
        except Exception as e:
            print(f"❌ 写入失败: {e}")
            sys.exit(1)
    else:
        print("无新论文")


if __name__ == "__main__":
    main()
