"""금융 머신러닝 최신 논문 수집기.

1순위: SerpAPI Google Scholar API (환경변수 SERPAPI_KEY 필요)
2순위: arXiv API (키 불필요, SERPAPI_KEY 가 없거나 호출 실패 시 자동 사용)

결과는 data/papers_raw.json, data/papers.csv 로 저장된다.
"""
from __future__ import annotations

import json
import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests

SERPAPI_URL = "https://serpapi.com/search.json"
ARXIV_URL = "https://export.arxiv.org/api/query"
ATOM = "{http://www.w3.org/2005/Atom}"

DEFAULT_QUERY = '"machine learning" OR "deep learning" finance stock portfolio'
# arXiv 검색식은 괄호 섞인 AND/OR 를 제대로 처리하지 못하므로
# 금융(q-fin) 최신 논문을 넉넉히 받은 뒤 ML 키워드로 직접 거른다.
ARXIV_QUERY = "cat:q-fin.CP OR cat:q-fin.PM OR cat:q-fin.ST OR cat:q-fin.TR OR cat:q-fin.RM OR cat:q-fin.MF"
ML_PATTERN = re.compile(
    r"machine learning|deep learning|neural network|reinforcement learning|language model|\bllms?\b"
    r"|transformer|lstm|graph neural|gradient boost|xgboost|random forest|diffusion model|multi-task learning",
    re.I,
)


def _load_dotenv(path: Path) -> None:
    """.env 파일의 KEY=VALUE 를 환경변수로 읽는다 (python-dotenv 없이)."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def fetch_serpapi(query: str, n: int, api_key: str, year_from: int) -> list[dict]:
    """SerpAPI Google Scholar 엔진으로 최신순(scisbd=1) 논문을 가져온다."""
    params = {
        "engine": "google_scholar",
        "q": query,
        "api_key": api_key,
        "as_ylo": year_from,
        "scisbd": 1,  # 날짜순 정렬 (최근 추가된 논문)
        "num": min(max(n * 2, 10), 20),
        "hl": "en",
    }
    resp = requests.get(SERPAPI_URL, params=params, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    if "error" in data:
        raise RuntimeError(data["error"])

    papers = []
    for r in data.get("organic_results", []):
        pub = r.get("publication_info", {}).get("summary", "")
        year = re.search(r"(19|20)\d{2}", pub)
        pdf = next((x.get("link") for x in r.get("resources", []) if x.get("file_format") == "PDF"), None)
        papers.append({
            "id": r.get("result_id"),
            "title": r.get("title", "").strip(),
            "authors": ", ".join(a.get("name", "") for a in r.get("publication_info", {}).get("authors", [])) or pub.split(" - ")[0],
            "published": year.group(0) if year else "",
            "venue": pub,
            "abstract": r.get("snippet", ""),
            "categories": "",
            "cited_by": r.get("inline_links", {}).get("cited_by", {}).get("total", 0),
            "url": r.get("link", ""),
            "pdf_url": pdf,
            "source": "serpapi_google_scholar",
        })
        if len(papers) >= n:
            break
    return papers


def fetch_arxiv(n: int) -> list[dict]:
    """arXiv 금융(q-fin) 카테고리에서 ML 관련 최신 논문을 가져온다."""
    params = {
        "search_query": ARXIV_QUERY,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
        "max_results": 200,
    }
    resp = requests.get(ARXIV_URL, params=params, timeout=60)
    resp.raise_for_status()
    root = ET.fromstring(resp.content)

    papers = []
    for e in root.findall(f"{ATOM}entry"):
        text = lambda tag: re.sub(r"\s+", " ", (e.findtext(f"{ATOM}{tag}") or "")).strip()
        pdf = next((l.get("href") for l in e.findall(f"{ATOM}link") if l.get("title") == "pdf"), None)
        papers.append({
            "id": text("id").rsplit("/", 1)[-1],
            "title": text("title"),
            "authors": ", ".join(a.findtext(f"{ATOM}name") for a in e.findall(f"{ATOM}author")),
            "published": text("published")[:10],
            "venue": "arXiv",
            "abstract": text("summary"),
            "categories": ", ".join(c.get("term") for c in e.findall(f"{ATOM}category")),
            "cited_by": None,
            "url": text("id"),
            "pdf_url": pdf,
            "source": "arxiv",
        })
    papers = [p for p in papers if ML_PATTERN.search(f"{p['title']} {p['abstract']}")]
    return papers[:n]


def fetch_papers(n: int = 5, query: str = DEFAULT_QUERY, year_from: int | None = None) -> list[dict]:
    _load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    year_from = year_from or datetime.now().year - 1
    api_key = os.getenv("SERPAPI_KEY")
    if api_key:
        try:
            papers = fetch_serpapi(query, n, api_key, year_from)
            if papers:
                print(f"[fetch] SerpAPI Google Scholar 에서 {len(papers)}편 수집")
                return papers
        except Exception as exc:  # 키 오류·쿼터 초과 등
            print(f"[fetch] SerpAPI 실패 → arXiv 로 대체: {exc}")
    else:
        print("[fetch] SERPAPI_KEY 없음 → arXiv API 로 수집")
    papers = fetch_arxiv(n)
    print(f"[fetch] arXiv 에서 {len(papers)}편 수집")
    return papers


def save_papers(papers: list[dict], data_dir: Path) -> pd.DataFrame:
    data_dir.mkdir(parents=True, exist_ok=True)
    payload = {"collected_at": datetime.now().isoformat(timespec="seconds"), "papers": papers}
    (data_dir / "papers_raw.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    df = pd.DataFrame(papers)
    df.to_csv(data_dir / "papers.csv", index=False, encoding="utf-8-sig")
    print(f"[fetch] 저장: {data_dir / 'papers_raw.json'}, {data_dir / 'papers.csv'}")
    return df


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    save_papers(fetch_papers(), root / "data")
