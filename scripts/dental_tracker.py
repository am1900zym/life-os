#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
口腔视界 DentaScope — 期刊自动追踪器 v1.2
==========================================
通过 PubMed E-utilities (NCBI) 自动追踪口腔医学 + 口腔护理期刊的最新论文，
解析元数据（含 OA 全文链接、中英双语标签、中文标题翻译）后写入 Supabase dental_papers 表。

用法:
    python scripts/dental_tracker.py              # 默认追踪最近 7 天 (写库)
    python scripts/dental_tracker.py --days 30    # 追踪最近 30 天
    python scripts/dental_tracker.py --dry-run    # 只打印不写库
    python scripts/dental_tracker.py --days 30 --json --out data/dental-papers-fresh.json  # 导出 JSON
    python scripts/dental_tracker.py --no-translate  # 跳过标题翻译 (更快)

环境变量:
    SUPABASE_URL          必填, e.g. https://xxxx.supabase.co
    SUPABASE_SERVICE_KEY  必填, service_role key (写入用, 勿入前端)
    PUBMED_EMAIL          可选, NCBI 联系方式 (默认 dentascope@example.com)

原理:
    esearch 按期刊 NLM 缩写 + 日期过滤拿 PMID → efetch 批量取元数据 →
    解析 (标签双语/期刊双语) → Europe PMC 查 OA 全文 → 批量 upsert (on pmid)
"""

import argparse
import json
import os
import re
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import List, Dict, Optional

import requests

# NCBI E-utilities 需要直连 (本机 Clash 代理会中断连接)
os.environ["NO_PROXY"] = "eutils.ncbi.nlm.nih.gov,www.ncbi.nlm.nih.gov,api.ncbi.nlm.nih.gov,www.ebi.ac.uk,ebi.ac.uk"
os.environ["no_proxy"] = os.environ["NO_PROXY"]

# ---------------------------------------------------------------
# 追踪的期刊清单 (20 本: 10 核心口腔 + 10 口腔护理/卫生)
# ta = NLM 缩写 (PubMed [ta] 检索), title = 期刊全名, zh = 中文明
# ---------------------------------------------------------------
JOURNALS = [
    # ── 核心口腔医学 (10) ──
    {"title": "Journal of Dental Research", "ta": "J Dent Res", "zh": "牙科研究杂志"},
    {"title": "Journal of Clinical Periodontology", "ta": "J Clin Periodontol", "zh": "临床牙周病学杂志"},
    {"title": "Journal of Endodontics", "ta": "J Endod", "zh": "牙髓病学杂志"},
    {"title": "Journal of Periodontology", "ta": "J Periodontol", "zh": "牙周病学杂志"},
    {"title": "Journal of Prosthetic Dentistry", "ta": "J Prosthet Dent", "zh": "修复牙科杂志"},
    {"title": "International Journal of Paediatric Dentistry", "ta": "Int J Paediatr Dent", "zh": "国际儿童牙科杂志"},
    {"title": "Community Dentistry and Oral Epidemiology", "ta": "Community Dent Oral Epidemiol", "zh": "社区口腔与流行病学"},
    {"title": "Journal of Oral Rehabilitation", "ta": "J Oral Rehabil", "zh": "口腔康复杂志"},
    {"title": "Journal of Dental Sciences", "ta": "J Dent Sci", "zh": "牙科科学杂志"},
    {"title": "BMC Oral Health", "ta": "BMC Oral Health", "zh": "BMC 口腔健康"},
    # ── 口腔护理/卫生 (10) ──
    {"title": "International Journal of Dental Hygiene", "ta": "Int J Dent Hyg", "zh": "国际牙科卫生杂志"},
    {"title": "Journal of Dental Hygiene", "ta": "J Dent Hyg", "zh": "牙科卫生学杂志"},
    {"title": "Special Care in Dentistry", "ta": "Spec Care Dentist", "zh": "特需牙科学"},
    {"title": "Gerodontology", "ta": "Gerodontology", "zh": "老年牙科学"},
    {"title": "Community Dental Health", "ta": "Community Dent Health", "zh": "社区牙科健康"},
    {"title": "Journal of Clinical Nursing", "ta": "J Clin Nurs", "zh": "临床护理杂志"},
    {"title": "Journal of Advanced Nursing", "ta": "J Adv Nurs", "zh": "高级护理杂志"},
    {"title": "Nursing Open", "ta": "Nurs Open", "zh": "护理开放"},
    {"title": "BMC Nursing", "ta": "BMC Nurs", "zh": "BMC 护理"},
    {"title": "Journal of Public Health Dentistry", "ta": "J Public Health Dent", "zh": "公共卫生牙科杂志"},
]

# PublicationType → (英文标签, 中文标签)
PUBTYPE_TAGS = {
    "Journal Article": ("Article", "期刊文章"),
    "Review": ("Review", "综述"),
    "Systematic Review": ("Systematic Review", "系统评价"),
    "Meta-Analysis": ("Meta-Analysis", "荟萃分析"),
    "Randomized Controlled Trial": ("RCT", "随机对照"),
    "Clinical Trial": ("Clinical Trial", "临床试验"),
    "Multicenter Study": ("Multicenter", "多中心"),
    "Comparative Study": ("Comparative", "对比研究"),
    "Observational Study": ("Observational", "观察性研究"),
    "Case Reports": ("Case Report", "病例报告"),
    "Guideline": ("Guideline", "指南"),
    "Practice Guideline": ("Practice Guideline", "实践指南"),
    "Validation Study": ("Validation", "效度研究"),
    "Evaluation Study": ("Evaluation", "评价研究"),
    "Letter": ("Letter", "来信"),
    "Editorial": ("Editorial", "社论"),
    "Comment": ("Comment", "评论"),
    "Retraction of Publication": ("Retraction", "撤稿"),
    "Erratum": ("Erratum", "勘误"),
    "In Vitro": ("In Vitro", "体外研究"),
    "Prospective Studies": ("Prospective", "前瞻性研究"),
    "Retrospective Studies": ("Retrospective", "回顾性研究"),
    "Cross-Sectional Studies": ("Cross-Sectional", "横断面研究"),
    "Cohort Studies": ("Cohort", "队列研究"),
    "Follow-Up Studies": ("Follow-Up", "随访研究"),
    "Longitudinal Studies": ("Longitudinal", "纵向研究"),
    "Sensitivity and Specificity": ("Sensitivity", "敏感性"),
    "Reproducibility of Results": ("Reproducibility", "可重复性"),
    "Dental Care": ("Dental Care", "口腔护理"),
    "Oral Health": ("Oral Health", "口腔健康"),
    "Dental Hygiene": ("Dental Hygiene", "牙科卫生"),
    "Nursing": ("Nursing", "护理"),
    "Geriatric Dentistry": ("Geriatric", "老年口腔"),
    "Patient Education as Topic": ("Patient Edu", "患者教育"),
    "Health Education, Dental": ("Health Edu", "健康教育"),
    "Quality of Life": ("QoL", "生活质量"),
    "Pain Management": ("Pain", "疼痛管理"),
    "Infection Control, Dental": ("Infection Ctrl", "感染控制"),
    "Saliva": ("Saliva", "唾液"),
    "Xerostomia": ("Xerostomia", "口干症"),
    "Periodontal Diseases": ("Periodontal", "牙周病"),
    "Dental Caries": ("Caries", "龋病"),
    "Tooth Loss": ("Tooth Loss", "失牙"),
    "Dental Anxiety": ("Anxiety", "牙科焦虑"),
    "Oral Hygiene": ("Oral Hygiene", "口腔卫生"),
    "Health Behavior": ("Health Behavior", "健康行为"),
    "Self Care": ("Self Care", "自我护理"),
    "Caregivers": ("Caregivers", "照护者"),
    "Long-Term Care": ("Long-Term Care", "长期照护"),
    "Dementia": ("Dementia", "痴呆"),
    "Down Syndrome": ("Down Syndrome", "唐氏综合征"),
    "Cerebral Palsy": ("Cerebral Palsy", "脑瘫"),
    "Autism Spectrum Disorder": ("Autism", "自闭症"),
    "Disabled Persons": ("Disability", "残障人群"),
    "Learning Disabilities": ("Learning Disability", "学习障碍"),
    "Oral Health Services": ("Services", "口腔卫生服务"),
    "Health Services Accessibility": ("Access", "服务可及性"),
    "Vulnerable Populations": ("Vulnerable", "弱势群体"),
    "Aged": ("Aged", "老年"),
    "Child": ("Child", "儿童"),
    "Adolescent": ("Adolescent", "青少年"),
    "Pregnancy": ("Pregnancy", "妊娠"),
}

NCBI_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
EUROPE_PMC_BASE = "https://www.ebi.ac.uk/europepmc/webservices/rest"
TOOL = "DentaScopeTracker"
EMAIL = os.environ.get("PUBMED_EMAIL", "dentascope@example.com")

# 翻译缓存 (避免重复调用)
TRANSLATE_CACHE: Dict[str, str] = {}


def ncbi_params(**kw):
    p = {"tool": TOOL, "email": EMAIL}
    p.update(kw)
    return p


def search_pmids(journal_ta, start_date, end_date, retmax=50):
    """esearch: 按期刊 NLM 缩写 + 出版日期区间拿 PMID 列表（按入库时间排序取最新）"""
    term = f'"{journal_ta}"[ta] AND {start_date}[dp] : {end_date}[dp]'
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


def translate_title_zh(title: str) -> str:
    """调用 Google Translate 免费端点翻译标题为中文 (失败返回空串, 不阻塞流程)"""
    if not title or len(title) < 10:
        return ""
    if title in TRANSLATE_CACHE:
        return TRANSLATE_CACHE[title]
    try:
        r = requests.get(
            "https://translate.googleapis.com/translate_a/single",
            params={"client": "gtx", "sl": "en", "tl": "zh-CN", "dt": "t", "q": title[:1800]},
            timeout=20,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        if r.status_code == 200:
            parts = r.json()
            if parts and parts[0]:
                translated = "".join(seg[0] for seg in parts[0] if seg and seg[0])
                TRANSLATE_CACHE[title] = translated
                time.sleep(0.15)  # 限速
                return translated
    except Exception:
        pass
    TRANSLATE_CACHE[title] = ""
    return ""


def europe_pmc_oa_lookup(doi: str) -> Dict:
    """Europe PMC 查 OA 全文信息: pmc_id, is_oa, full_text_url"""
    if not doi:
        return {"pmc_id": None, "is_oa": False, "full_text_url": None}
    try:
        r = requests.get(
            f"{EUROPE_PMC_BASE}/search",
            params={"query": f'DOI:"{doi}"', "format": "json", "pageSize": 1},
            timeout=15,
        )
        if r.status_code != 200:
            return {"pmc_id": None, "is_oa": False, "full_text_url": None}
        data = r.json()
        hits = data.get("resultList", {}).get("result", [])
        if not hits:
            return {"pmc_id": None, "is_oa": False, "full_text_url": None}
        hit = hits[0]
        pmc_id = hit.get("pmcid") or ""
        is_oa = hit.get("isOpenAccess") == "Y"
        full_text_url = None
        # 优先 PDF 直链
        ft_urls = hit.get("fullTextUrlList", {}).get("fullTextUrl", [])
        for u in ft_urls:
            if u.get("documentStyle") == "pdf" and u.get("availability") in ("Open access", "Open Access"):
                full_text_url = u.get("url")
                break
        if not full_text_url and pmc_id:
            full_text_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc_id}/"
        return {"pmc_id": pmc_id, "is_oa": is_oa, "full_text_url": full_text_url}
    except Exception:
        return {"pmc_id": None, "is_oa": False, "full_text_url": None}


def parse_pubmed_xml(xml_text):
    """解析 PubMed XML → 文章字典列表 (含双语标签/期刊/标题)"""
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
        title = re.sub(r"<[^>]+>", "", title)

        # 期刊
        journal_el = article.find("Journal")
        journal = text_of(journal_el.find("Title")) if journal_el is not None else ""
        journal_info = next((j for j in JOURNALS if j["ta"].lower() == (text_of(journal_el.find("ISOAbbreviation")) if journal_el is not None else "").lower()
                             or j["title"].lower() == journal.lower()), None)
        journal_zh = journal_info["zh"] if journal_info else journal

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

        # PMCID (PubMed XML 自带, 免费批量获取 OA 标识)
        pmcid = ""
        for pid in art.findall(".//ArticleId[@IdType='pmc']"):
            pmcid = text_of(pid)
            break

        # 摘要
        abstract_parts = []
        for ab in article.findall(".//AbstractText"):
            label = ab.get("Label")
            txt = text_of(ab)
            abstract_parts.append(f"{label}: {txt}" if label else txt)
        abstract = " ".join(abstract_parts)[:2000]

        # 文献类型 + 双语标签
        ptypes = [text_of(p) for p in article.findall(".//PublicationType")]
        paper_type = "研究"
        if any("Review" in t for t in ptypes):
            paper_type = "综述"
        elif any("Clinical Trial" in t or "Randomized" in t for t in ptypes):
            paper_type = "临床"
        elif any("Comment" in t or "Editorial" in t or "Letter" in t or "Erratum" in t or "Corrigendum" in t for t in ptypes):
            paper_type = "政策"

        tags_en, tags_zh = [], []
        for pt in ptypes:
            mapped = PUBTYPE_TAGS.get(pt)
            if mapped:
                en, zh = mapped
                if en not in tags_en:
                    tags_en.append(en)
                if zh not in tags_zh:
                    tags_zh.append(zh)
        # 补充: 标题关键词标签 (前 3 个 MeSH 或 Keyword)
        keyword_list = art.find(".//KeywordList")
        if keyword_list is not None:
            for k in keyword_list.findall("Keyword")[:3]:
                kw = text_of(k)
                if kw and kw not in tags_en:
                    tags_en.append(kw)
        tags_en = tags_en[:5]
        tags_zh = tags_zh[:5]

        articles.append({
            "pmid": pmid,
            "title": title,
            "title_zh": "",  # 由 main 统一翻译
            "authors": authors_str,
            "journal": journal,
            "journal_zh": journal_zh,
            "date": pub_date,
            "doi": doi,
            "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else doi,
            "abstract": abstract,
            "type": paper_type,
            "tags": tags_en,
            "tags_zh": tags_zh,
            "pmcid": pmcid,  # 有值 = PMC 收录, 可读全文
            "is_new": True,
        })
    return articles


def _sb_request(method, url, key, **kw):
    """Supabase 请求带重试 (对抗本机网络抖动 SSL EOF / HTTP 000)"""
    headers = kw.pop("headers", {})
    headers.setdefault("apikey", key)
    headers.setdefault("Authorization", f"Bearer {key}")
    last_err = None
    for attempt in range(4):
        try:
            return requests.request(method, url, headers=headers, timeout=45, **kw)
        except (requests.exceptions.ConnectionError, requests.exceptions.SSLError,
                requests.exceptions.Timeout) as e:
            last_err = e
            print(f"  ⚠️ 网络抖动 (attempt {attempt+1}/4): {type(e).__name__}")
            time.sleep(3 * (attempt + 1))
    raise last_err


def fetch_existing_pmids(supabase_url, service_key):
    """从 Supabase 读取已入库的 PMID (去重用)"""
    url = f"{supabase_url}/rest/v1/dental_papers?select=pmid"
    r = _sb_request("GET", url, service_key)
    if r.status_code in (401, 404):
        return set()
    r.raise_for_status()
    return {row.get("pmid") for row in r.json() if row.get("pmid")}


def ensure_tables(supabase_url, service_key):
    """自检: dental_papers 表是否存在"""
    url = f"{supabase_url}/rest/v1/dental_papers?select=count"
    r = _sb_request("GET", url, service_key, params={"select": "count"},
                    headers={"Prefer": "count=exact"})
    # PostgREST 对 count 请求返回 206 Partial Content (表存在); 404/405 = 不存在或无权
    return r.status_code in (200, 206)


def upsert_articles(supabase_url, service_key, articles):
    """批量写入 Supabase (upsert on pmid) — v1.2 新增 OA/双语字段
    OA 判断: PubMed XML 自带 pmcid, 有值即 PMC 收录 → 可读全文 (零额外请求)"""
    if not articles:
        return 0
    url = f"{supabase_url}/rest/v1/dental_papers?on_conflict=pmid"
    rows = []
    for a in articles:
        pmcid = a.get("pmcid", "")
        is_oa = bool(pmcid)
        full_text_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/" if pmcid else None
        rows.append({
            "pmid": a.get("pmid"),
            "title": a.get("title"),
            "title_zh": a.get("title_zh", ""),
            "authors": a.get("authors", ""),
            "journal": a.get("journal"),
            "journal_zh": a.get("journal_zh", ""),
            "published_on": a.get("date"),
            "doi": a.get("doi", ""),
            "url": a.get("url"),
            "abstract": a.get("abstract", ""),
            "paper_type": a.get("type", "研究"),
            "tags": a.get("tags", []),
            "tags_zh": a.get("tags_zh", []),
            "is_new": a.get("is_new", True),
            "pmc_id": pmcid,
            "is_oa": is_oa,
            "full_text_url": full_text_url,
        })
    r = _sb_request("POST", url, service_key, json=rows,
                    headers={"Content-Type": "application/json",
                             "Prefer": "resolution=merge-duplicates,return=minimal"})
    r.raise_for_status()
    return len(articles)


def main():
    parser = argparse.ArgumentParser(description="DentaScope 期刊追踪器 v1.2")
    parser.add_argument("--days", type=int, default=7, help="回溯天数 (默认 7)")
    parser.add_argument("--dry-run", action="store_true", help="只打印不写库")
    parser.add_argument("--journal", default=None, help="只追踪指定期刊 (默认全部)")
    parser.add_argument("--json", dest="as_json", action="store_true", help="输出 JSON 到 stdout (配合 --out 使用)")
    parser.add_argument("--out", default=None, help="写入 JSON 文件路径 (默认 stdout)")
    parser.add_argument("--no-translate", action="store_true", help="跳过标题中文翻译 (更快)")
    parser.add_argument("--refresh", action="store_true", help="全量刷新模式: 不去重, 重写已有 PMID (用于回填 title_zh/tags_zh/is_oa)")
    args = parser.parse_args()

    supabase_url = os.environ.get("SUPABASE_URL")
    service_key = os.environ.get("SUPABASE_SERVICE_KEY")
    if not (args.dry_run or args.as_json) and (not supabase_url or not service_key):
        print("ERROR: 需要环境变量 SUPABASE_URL 和 SUPABASE_SERVICE_KEY (dry-run/--json 除外)")
        sys.exit(1)

    end = datetime.now()
    start = end - timedelta(days=args.days)
    start_str = start.strftime("%Y/%m/%d")
    end_str = end.strftime("%Y/%m/%d")

    journals = [j for j in JOURNALS if args.journal is None or j["ta"].lower() == args.journal.lower() or j["title"].lower() == args.journal.lower()]
    if not journals:
        print(f"未找到期刊: {args.journal}")
        sys.exit(1)

    print(f"[{datetime.now():%H:%M:%S}] 追踪区间: {start_str} - {end_str} (共 {len(journals)} 本期刊)")

    # 自检: 表是否存在 (写库前检查)
    if not args.dry_run and not args.as_json:
        if not ensure_tables(supabase_url, service_key):
            print("⚠️  表 dental_papers 不存在! 请先在 Supabase SQL Editor 执行:")
            print("   supabase/dental-schema.sql")
            sys.exit(1)

    # 已入库 PMID (去重; --refresh 模式跳过去重, 全量重写)
    existing = set()
    if not args.dry_run and not args.refresh:
        try:
            existing = fetch_existing_pmids(supabase_url, service_key)
            print(f"已入库 {len(existing)} 条")
        except Exception as e:
            print(f"读取已有记录失败(首次运行可忽略): {e}")

    all_new = []
    seen_pmids = set()
    for j in journals:
        try:
            pmids = search_pmids(j["ta"], start_str, end_str)
            print(f"  {j['zh']} [{j['ta']}]: {len(pmids)} 篇")
        except Exception as e:
            print(f"  {j['zh']}: 查询失败 - {e}")
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

    # 标题翻译 (默认开启, --no-translate 跳过)
    if not args.no_translate:
        print(f"[{datetime.now():%H:%M:%S}] 翻译标题为中文 ({len(all_new)} 篇)...")
        for a in all_new:
            a["title_zh"] = translate_title_zh(a["title"])
            if not a["title_zh"]:
                a["title_zh"] = ""  # 翻译失败留空, 前端隐藏中文行

    print(f"\n新论文: {len(all_new)} 篇")

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
            zh = f" | {a['title_zh'][:30]}" if a.get("title_zh") else ""
            print(f"  [{a['date']}] {a['journal_zh']} | {a['title'][:60]}{zh}")
        return

    if all_new:
        try:
            n = upsert_articles(supabase_url, service_key, all_new)
            print(f"✅ 已写入 Supabase: {n} 条 (含 OA 全文链接)")
        except Exception as e:
            print(f"❌ 写入失败: {e}")
            sys.exit(1)
    else:
        print("无新论文")


if __name__ == "__main__":
    main()
