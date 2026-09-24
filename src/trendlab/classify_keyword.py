"""베이스라인: 키워드(정규식) 기반 분류. 제목 매칭은 가중치 3, 초록 매칭은 1 로 점수를 매겨 최고점 라벨을 고른다."""
from __future__ import annotations

import re

import pandas as pd

from .taxonomy import METHODS, TOPICS


def _best(title: str, abstract: str, table: dict) -> str:
    scores = {}
    for key, spec in table.items():
        pat = re.compile(spec["keywords"], re.I)
        scores[key] = 3 * len(pat.findall(title)) + len(pat.findall(abstract))
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "other"


def classify_keyword(df: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({
        "arxiv_id": df["arxiv_id"],
        "topic": [_best(t, a, TOPICS) for t, a in zip(df["title"], df["abstract"])],
        "method": [_best(t, a, METHODS) for t, a in zip(df["title"], df["abstract"])],
    })
