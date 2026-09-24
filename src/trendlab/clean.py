"""정제: 금융×ML 관련성 필터 → DOI/arXiv ID/제목 기준 중복 제거 → 초록·날짜 누락 확인 → 월 컬럼 → 상한 적용."""
from __future__ import annotations

import json
import re

import pandas as pd

import config

ML_RE = re.compile(
    r"machine learning|deep learning|neural net|language model|\bllms?\b|transformer|reinforcement learning"
    r"|lstm|graph neural|\bgnn|gradient boost|xgboost|random forest|diffusion model|generative adversarial"
    r"|autoencoder|foundation model|deep hedging|learning-based|supervised|representation learning", re.I)
FIN_RE = re.compile(
    r"financ|stock|equit(?:y|ies)|portfolio|asset pricing|trading|market making|order book|volatility"
    r"|option pricing|derivative pricing|hedg|credit|loan|default risk|fraud|anti-money|bank|crypto|bitcoin"
    r"|defi\b|investor|investment|hedge fund|bond|interest rate|exchange rate|forex|insurance|earnings", re.I)


def _norm_title(t: str) -> str:
    return re.sub(r"[^a-z0-9]", "", t.lower())


def clean(rows: list[dict]) -> tuple[pd.DataFrame, dict]:
    df = pd.DataFrame(rows)
    log = {"raw_rows": len(df)}

    # 1) 누락 확인
    for col in ["title", "abstract", "published", "url"]:
        log[f"missing_{col}"] = int((df[col].fillna("").str.strip() == "").sum())
    df = df[(df["title"].str.strip() != "") & (df["abstract"].str.strip() != "") & (df["published"].str.strip() != "")]

    # 2) 중복 제거: arXiv ID → DOI → 정규화 제목 (여러 검색식에 걸린 논문은 query 를 합쳐서 보관)
    df = df.assign(query=df.groupby("arxiv_id")["query"].transform(lambda s: "; ".join(sorted(set(s)))))
    before = len(df)
    df = df.drop_duplicates("arxiv_id")
    df = df[~(df["doi"].ne("") & df.duplicated("doi"))]
    df = df.loc[~df["title"].map(_norm_title).duplicated()]
    log["duplicates_removed"] = before - len(df)

    # 3) 관련성: 제목+초록에 ML 용어가 있고, 금융 용어가 있거나 q-fin 카테고리
    text = df["title"] + " " + df["abstract"]
    is_ml = text.str.contains(ML_RE)
    is_fin = text.str.contains(FIN_RE) | df["categories"].str.contains("q-fin")
    log["dropped_not_ml"] = int((~is_ml).sum())
    log["dropped_not_finance"] = int((is_ml & ~is_fin).sum())
    df = df[is_ml & is_fin].copy()

    # 4) 월 컬럼 (최초 제출일 기준)
    df["month"] = df["published"].str[:7]
    log["after_filter"] = len(df)

    # 5) 상한: 월별 비율을 유지하도록 월마다 같은 비율로 무작위 추출
    if len(df) > config.MAX_PAPERS:
        frac = config.MAX_PAPERS / len(df)
        df = df.groupby("month").sample(frac=frac, random_state=config.RANDOM_SEED)
        log["sampled_to"] = len(df)

    df = df.sort_values(["published", "arxiv_id"]).reset_index(drop=True)
    log["final_rows"] = len(df)
    log["per_month"] = df["month"].value_counts().sort_index().to_dict()
    return df, log


def save(df: pd.DataFrame, log: dict) -> None:
    config.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    cols = ["arxiv_id", "month", "published", "title", "abstract", "authors", "primary_category",
            "categories", "doi", "url", "query"]
    df[cols].to_csv(config.PROCESSED_DIR / "papers.csv", index=False, encoding="utf-8-sig")
    (config.PROCESSED_DIR / "cleaning_log.json").write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[clean] {log['raw_rows']} → {log['final_rows']}건, 월별 {log['per_month']}")


def load_papers() -> pd.DataFrame:
    return pd.read_csv(config.PROCESSED_DIR / "papers.csv", encoding="utf-8-sig", dtype=str, keep_default_na=False)
