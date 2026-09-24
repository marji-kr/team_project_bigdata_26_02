"""arXiv API 로 기준일 직전 N개월 논문(제목·초록·발표일·DOI/URL)을 월 단위로 수집한다.

Google Scholar 는 일괄 수집을 지원하지 않으므로(문제정의서 3절) 대체 후보인 arXiv API 를 쓴다.
arXiv 이용 정책에 따라 요청 사이에 3초를 쉰다.
"""
from __future__ import annotations

import calendar
import json
import re
import time
import xml.etree.ElementTree as ET
from datetime import date

import requests

import config

API = "https://export.arxiv.org/api/query"
ATOM = "{http://www.w3.org/2005/Atom}"
ARXIV_NS = "{http://arxiv.org/schemas/atom}"
OS_NS = "{http://a9.com/-/spec/opensearch/1.1/}"
PAGE = 200


def month_windows(reference: date, n_months: int) -> list[tuple[str, date, date]]:
    """기준일이 속한 달 직전의 완결된 n개월을 (YYYY-MM, 시작일, 말일) 로 돌려준다."""
    y, m = reference.year, reference.month
    out = []
    for _ in range(n_months):
        m -= 1
        if m == 0:
            y, m = y - 1, 12
        out.append((f"{y}-{m:02d}", date(y, m, 1), date(y, m, calendar.monthrange(y, m)[1])))
    return out[::-1]


def _entry(e: ET.Element, query_name: str) -> dict:
    text = lambda tag, ns=ATOM: re.sub(r"\s+", " ", e.findtext(f"{ns}{tag}") or "").strip()
    url = text("id")
    return {
        "arxiv_id": re.sub(r"v\d+$", "", url.rsplit("/abs/", 1)[-1]),
        "title": text("title"),
        "abstract": text("summary"),
        "published": text("published")[:10],
        "updated": text("updated")[:10],
        "authors": "; ".join(a.findtext(f"{ATOM}name") for a in e.findall(f"{ATOM}author")),
        "primary_category": (e.find(f"{ARXIV_NS}primary_category").get("term")
                             if e.find(f"{ARXIV_NS}primary_category") is not None else ""),
        "categories": "; ".join(c.get("term") for c in e.findall(f"{ATOM}category")),
        "doi": text("doi", ARXIV_NS),
        "url": url,
        "query": query_name,
    }


def fetch_month(query_name: str, query: str, start: date, end: date, session: requests.Session) -> list[dict]:
    q = f"({query}) AND submittedDate:[{start:%Y%m%d}0000 TO {end:%Y%m%d}2359]"
    rows, offset, total = [], 0, None
    while total is None or offset < total:
        resp = session.get(API, params={"search_query": q, "start": offset, "max_results": PAGE,
                                        "sortBy": "submittedDate", "sortOrder": "ascending"}, timeout=90)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
        total = int(root.findtext(f"{OS_NS}totalResults") or 0)
        entries = root.findall(f"{ATOM}entry")
        rows += [_entry(e, query_name) for e in entries if e.findtext(f"{ATOM}title") != "Error"]
        offset += PAGE
        time.sleep(3)
        if not entries:  # arXiv 가 가끔 빈 페이지를 주면 중단
            break
    return rows


def collect(reference: date) -> list[dict]:
    config.RAW_DIR.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers["User-Agent"] = "trendlab/1.0 (graduate course project)"
    all_rows = []
    for label, start, end in month_windows(reference, config.WINDOW_MONTHS):
        month_rows = []
        for name, query in config.ARXIV_QUERIES.items():
            rows = fetch_month(name, query, start, end, session)
            print(f"[collect] {label} {name}: {len(rows)}건")
            month_rows += rows
        (config.RAW_DIR / f"arxiv_{label}.json").write_text(
            json.dumps(month_rows, ensure_ascii=False, indent=1), encoding="utf-8")
        all_rows += month_rows
    meta = {"reference_date": reference.isoformat(), "window_months": config.WINDOW_MONTHS,
            "queries": config.ARXIV_QUERIES, "n_raw": len(all_rows)}
    (config.RAW_DIR / "collection_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return all_rows
