"""월별 주제 비중과 변화량을 '코드로' 계산한다 (LLM 은 쓰지 않음)."""
from __future__ import annotations

import numpy as np
import pandas as pd


def monthly_share(df: pd.DataFrame, labels: pd.DataFrame, col: str = "topic") -> tuple[pd.DataFrame, pd.DataFrame]:
    """(월×라벨 논문 수, 월×라벨 비중) 을 돌려준다. 비중 = 해당 월 논문 수 대비."""
    m = df[["arxiv_id", "month"]].merge(labels[["arxiv_id", col]], on="arxiv_id")
    counts = pd.crosstab(m["month"], m[col]).sort_index()
    share = counts.div(counts.sum(axis=1), axis=0)
    return counts, share


def trend_table(counts: pd.DataFrame, share: pd.DataFrame) -> pd.DataFrame:
    """라벨별 전체 비중, 전반기·후반기 비중 차이(%p), 월별 비중의 선형 기울기(%p/월)."""
    half = max(1, len(share) // 2)
    x = np.arange(len(share))
    rows = []
    for label in share.columns:
        y = share[label].values
        rows.append({
            "label": label,
            "papers": int(counts[label].sum()),
            "overall_share": counts[label].sum() / counts.values.sum(),
            "first_half_share": counts[label].iloc[:half].sum() / counts.iloc[:half].values.sum(),
            "second_half_share": counts[label].iloc[half:].sum() / counts.iloc[half:].values.sum(),
            "slope_pp_per_month": float(np.polyfit(x, y, 1)[0] * 100) if len(x) > 1 else 0.0,
        })
    t = pd.DataFrame(rows)
    t["change_pp"] = (t["second_half_share"] - t["first_half_share"]) * 100
    return t.sort_values("papers", ascending=False).reset_index(drop=True)
