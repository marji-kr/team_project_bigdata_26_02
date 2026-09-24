"""성공 기준 평가 (문제정의서 4절).

- make_eval_sample : 월별 층화 무작위 추출로 평가용 100건과 수작업 라벨 양식, 소요 시간 기록 양식을 만든다.
- evaluate         : 수작업 라벨(정답) 대비 키워드·LLM 분류의 정확도/Macro-F1/Cohen's κ,
                     수작업 대비 AI 방식의 총 소요 시간 단축률을 계산한다.

공정한 비교를 위해 AI 방식 시간 = 자동 실행 시간(data/runs/timings.csv) + 사람이 결과를 검토·수정한 시간
(data/eval/manual_timing.csv 의 approach=ai_review) 으로 계산한다.
"""
from __future__ import annotations

import pandas as pd
from sklearn.metrics import accuracy_score, cohen_kappa_score, f1_score

import config
from .taxonomy import METHOD_IDS, TOPIC_IDS

SAMPLE = config.EVAL_DIR / "eval_sample.csv"
MANUAL_TIMING = config.EVAL_DIR / "manual_timing.csv"


def make_eval_sample(df: pd.DataFrame, n: int = config.EVAL_SAMPLE_SIZE, overwrite: bool = False) -> pd.DataFrame:
    config.EVAL_DIR.mkdir(parents=True, exist_ok=True)
    if SAMPLE.exists() and not overwrite:
        print(f"[eval] 이미 있음 (수작업 라벨 보호): {SAMPLE}  → 새로 만들려면 --overwrite")
        return pd.read_csv(SAMPLE, encoding="utf-8-sig", dtype=str, keep_default_na=False)
    frac = min(1.0, n / len(df))
    s = df.groupby("month").sample(frac=frac, random_state=config.RANDOM_SEED)
    s = s.sample(frac=1, random_state=config.RANDOM_SEED).head(n)  # 순서 섞기 (월 순서 편향 방지)
    out = s[["arxiv_id", "month", "title", "abstract", "url"]].assign(manual_topic="", manual_method="", annotator="")
    out.to_csv(SAMPLE, index=False, encoding="utf-8-sig")
    if not MANUAL_TIMING.exists():
        pd.DataFrame([
            {"approach": "manual", "step": "search_collect", "annotator": "", "minutes": "", "note": "검색·수집·정리"},
            {"approach": "manual", "step": "read_classify", "annotator": "", "minutes": "", "note": "100건 초록 읽고 라벨링"},
            {"approach": "manual", "step": "write_report", "annotator": "", "minutes": "", "note": "같은 형식의 보고서 작성"},
            {"approach": "ai_review", "step": "review_labels", "annotator": "", "minutes": "", "note": "AI 결과 검토·수정"},
            {"approach": "ai_review", "step": "review_report", "annotator": "", "minutes": "", "note": "AI 보고서 검토·수정"},
        ]).to_csv(MANUAL_TIMING, index=False, encoding="utf-8-sig")
    print(f"[eval] 평가용 {len(out)}건 → {SAMPLE}")
    print(f"       manual_topic / manual_method 칸을 채우세요. 가능한 값: topic={TOPIC_IDS}, method={METHOD_IDS}")
    return out


def _scores(y_true: pd.Series, y_pred: pd.Series, labels: list[str]) -> dict:
    return {
        "n": len(y_true),
        "accuracy": accuracy_score(y_true, y_pred),
        "macro_f1": f1_score(y_true, y_pred, labels=labels, average="macro", zero_division=0),
        "cohen_kappa": cohen_kappa_score(y_true, y_pred),
    }


def accuracy_report(kw: pd.DataFrame, llm: pd.DataFrame | None) -> tuple[pd.DataFrame, dict[str, pd.DataFrame]]:
    gold = pd.read_csv(SAMPLE, encoding="utf-8-sig", dtype=str, keep_default_na=False)
    rows, confusions = [], {}
    for col, labels in [("topic", TOPIC_IDS), ("method", METHOD_IDS)]:
        g = gold[gold[f"manual_{col}"].isin(labels)][["arxiv_id", f"manual_{col}"]]
        if g.empty:
            continue
        for name, pred in [("keyword", kw), ("llm", llm)]:
            if pred is None or col not in pred:
                continue
            m = g.merge(pred[["arxiv_id", col]], on="arxiv_id")
            m = m[m[col] != ""]
            if m.empty:
                continue
            rows.append({"target": col, "approach": name, **_scores(m[f"manual_{col}"], m[col], labels)})
            if col == "topic":
                confusions[name] = pd.crosstab(m["manual_topic"], m["topic"], rownames=["manual"], colnames=[name])
    return pd.DataFrame(rows), confusions


def time_report() -> dict | None:
    if not MANUAL_TIMING.exists():
        return None
    t = pd.read_csv(MANUAL_TIMING, encoding="utf-8-sig")
    t["minutes"] = pd.to_numeric(t["minutes"], errors="coerce")
    manual = t.loc[t["approach"] == "manual", "minutes"].sum()
    review = t.loc[t["approach"] == "ai_review", "minutes"].sum()
    auto_path = config.RUNS_DIR / "timings.csv"
    auto = 0.0
    if auto_path.exists():
        a = pd.read_csv(auto_path)
        # 단계별 가장 최근 실행 1회씩만 합산 (재실행 중복 방지)
        a = a[a["approach"].isin(["auto", "llm"])].groupby("stage").tail(1)
        auto = a["seconds"].sum() / 60
    if manual <= 0:
        return {"manual_min": None, "ai_auto_min": auto, "ai_review_min": review, "ai_total_min": auto + review,
                "reduction": None, "target": config.TARGET_TIME_REDUCTION, "passed": None}
    total = auto + review
    red = 1 - total / manual
    return {"manual_min": manual, "ai_auto_min": auto, "ai_review_min": review, "ai_total_min": total,
            "reduction": red, "target": config.TARGET_TIME_REDUCTION, "passed": red >= config.TARGET_TIME_REDUCTION}
