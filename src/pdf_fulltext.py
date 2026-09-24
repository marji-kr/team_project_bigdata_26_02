"""논문 PDF 다운로드 + 본문 텍스트 추출.

- PDF  → data/pdfs/<id>.pdf
- 본문 → data/fulltext/<id>.txt
- 섹션(Introduction / Method / Data / Results / Conclusion 등) 분리
"""
from __future__ import annotations

import re
import time
from pathlib import Path

import pymupdf as fitz
import requests

HEADERS = {"User-Agent": "Mozilla/5.0 (academic research; team_project_bigdata)"}

SECTION_PATTERNS = {
    "abstract": r"abstract",
    "introduction": r"introduction",
    "related_work": r"related work|literature review|background",
    "method": r"method(ology)?|model|framework|approach|proposed",
    "data": r"data(set)?s?|empirical setup|experimental setup",
    "results": r"results?|experiments?|empirical (results|analysis)|evaluation|backtest",
    "conclusion": r"conclusions?|concluding remarks|discussion",
    "references": r"references|bibliography",
}
# "3 Method", "3. Method", "III. METHOD", "Method" 같이 한 줄 전체가 제목인 경우만 섹션 헤더로 본다
HEADER_RE = re.compile(r"^\s*(?:\d{1,2}(?:\.\d)?\.?|[IVX]{1,4}\.)?\s*([A-Z][A-Za-z &\-]{2,40})\s*$")


def _safe_name(paper_id: str) -> str:
    return re.sub(r"[^\w.\-]", "_", paper_id)


def download_pdf(url: str, dest: Path) -> bool:
    if dest.exists() and dest.stat().st_size > 0:
        return True
    try:
        resp = requests.get(url, headers=HEADERS, timeout=60)
        resp.raise_for_status()
    except requests.RequestException as exc:
        print(f"[pdf] 다운로드 실패 {url}: {exc}")
        return False
    if not resp.content.startswith(b"%PDF"):  # 유료 논문 로그인 페이지 등
        print(f"[pdf] PDF 가 아님 (접근 제한 가능성): {url}")
        return False
    dest.write_bytes(resp.content)
    return True


def extract_text(pdf_path: Path) -> tuple[str, int]:
    with fitz.open(pdf_path) as doc:
        text = "\n".join(page.get_text() for page in doc)
        n_pages = doc.page_count
    text = re.sub(r"-\n(?=[a-z])", "", text)  # 줄바꿈 하이픈 복원
    return text, n_pages


def split_sections(text: str) -> dict[str, str]:
    """본문을 표준 섹션 이름별로 나눈다. 찾지 못한 섹션은 빠진다."""
    lines = text.splitlines()
    marks = []
    for i, line in enumerate(lines):
        m = HEADER_RE.match(line)
        if not m:
            continue
        title = m.group(1).strip().lower()
        for name, pat in SECTION_PATTERNS.items():
            if re.fullmatch(rf"(?:{pat})(?:\s.*)?", title) and not any(n == name for _, n in marks):
                marks.append((i, name))
                break
    sections = {}
    for k, (start, name) in enumerate(marks):
        end = marks[k + 1][0] if k + 1 < len(marks) else len(lines)
        sections[name] = re.sub(r"\s+", " ", " ".join(lines[start + 1:end])).strip()
    return sections


def body_text(text: str) -> str:
    """참고문헌 이후를 잘라 분석용 본문만 남긴다."""
    m = re.search(r"\n\s*(references|bibliography)\s*\n", text, re.I)
    return re.sub(r"\s+", " ", text[: m.start()] if m else text).strip()


def fetch_fulltext(papers: list[dict], data_dir: Path) -> list[dict]:
    pdf_dir, txt_dir = data_dir / "pdfs", data_dir / "fulltext"
    pdf_dir.mkdir(parents=True, exist_ok=True)
    txt_dir.mkdir(parents=True, exist_ok=True)
    for p in papers:
        p.update(pdf_path=None, fulltext_path=None, n_pages=None)
        if not p.get("pdf_url"):
            print(f"[pdf] PDF 링크 없음: {p['title'][:60]}")
            continue
        name = _safe_name(p["id"] or p["title"][:40])
        pdf_path = pdf_dir / f"{name}.pdf"
        if not download_pdf(p["pdf_url"], pdf_path):
            continue
        text, n_pages = extract_text(pdf_path)
        txt_path = txt_dir / f"{name}.txt"
        txt_path.write_text(text, encoding="utf-8")
        p.update(pdf_path=str(pdf_path.relative_to(data_dir.parent)).replace("\\", "/"),
                 fulltext_path=str(txt_path.relative_to(data_dir.parent)).replace("\\", "/"),
                 n_pages=n_pages)
        print(f"[pdf] {pdf_path.name}: {n_pages}쪽, {len(text):,}자")
        time.sleep(3)  # arXiv 이용 정책: 요청 간 3초 간격
    return papers
