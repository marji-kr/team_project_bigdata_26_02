"""논문 트렌드 자동 분석 파이프라인 (팀 JKLS · 빅데이터분석및이론).

연구 질문: 최근 논문을 LLM 으로 주제별 분류·요약하고 월별 주제 비중 변화를 제시하면,
          사람이 직접 읽고 정리하는 방식보다 동향 파악 시간을 줄일 수 있는가?

사용법 (자세한 설명은 README.md):
    python run.py all                 # 수집 → 정제 → 분류(키워드+LLM) → 요약 → 보고서
    python run.py all --no-llm        # API 키 없이 키워드 분류만
    python run.py collect             # 1. arXiv 수집
    python run.py clean               # 2. 중복 제거·누락 확인·월 집계
    python run.py classify keyword    # 3a. 키워드 베이스라인
    python run.py classify llm        # 3b. LLM 분류 (--eval-only: 평가용 100건만)
    python run.py summarize           # 4. 주제별 LLM 요약
    python run.py report              # 5. 동향 보고서
    python run.py eval-sample         # 6. 평가용 100건 + 수작업 라벨·시간 기록 양식
    python run.py evaluate            # 7. 정확도·시간 단축률 평가 보고서
    python run.py weekly              # 주간 업데이트: 새 논문 5편 추가 → 분류 → 보고서 갱신
"""
from __future__ import annotations

import argparse
import glob
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT), str(ROOT / "src")]

import pandas as pd  # noqa: E402

import config  # noqa: E402
from trendlab import classify_keyword as kw_mod  # noqa: E402
from trendlab import clean as clean_mod  # noqa: E402
from trendlab import collect as collect_mod  # noqa: E402
from trendlab import evaluate as eval_mod  # noqa: E402
from trendlab import report as report_mod  # noqa: E402
from trendlab import trends  # noqa: E402
from trendlab.taxonomy import METHODS, TOPICS  # noqa: E402
from trendlab.timing import timed  # noqa: E402

P = config.PROCESSED_DIR


def _labels_path(approach: str) -> Path:
    return P / f"labels_{approach}.csv"


def _read(path: Path) -> pd.DataFrame | None:
    return pd.read_csv(path, encoding="utf-8-sig", dtype=str, keep_default_na=False) if path.exists() else None


def _reference_date(arg: str | None) -> date:
    s = arg or config.REFERENCE_DATE
    return date.fromisoformat(s) if s else date.today()


def cmd_collect(args) -> None:
    with timed("collect", "auto"):
        rows = collect_mod.collect(_reference_date(args.reference_date))
    print(f"[collect] 원본 {len(rows)}건 → {config.RAW_DIR}")


def cmd_clean(args) -> None:
    meta = json.loads((config.RAW_DIR / "collection_meta.json").read_text(encoding="utf-8"))
    ref = date.fromisoformat(meta["reference_date"])
    files = [config.RAW_DIR / f"arxiv_{m}.json" for m, _, _ in collect_mod.month_windows(ref, meta["window_months"])]
    files += sorted(config.RAW_DIR.glob("weekly_*.json"))  # 주간 업데이트로 추가된 논문도 유지
    rows = [r for f in files for r in json.loads(f.read_text(encoding="utf-8"))]
    with timed("clean", "auto", len(rows)):
        df, log = clean_mod.clean(rows)
        clean_mod.save(df, log)


def cmd_classify(args) -> None:
    df = clean_mod.load_papers()
    if args.approach == "keyword":
        with timed("classify", "keyword", len(df)):
            labels = kw_mod.classify_keyword(df)
    else:
        from trendlab import classify_llm as llm_mod
        if not llm_mod.has_credentials():
            sys.exit("ANTHROPIC_API_KEY 가 없습니다. .env 파일에 ANTHROPIC_API_KEY=... 를 넣으세요 (README 참고).")
        if args.eval_only:
            sample = _read(eval_mod.SAMPLE)
            if sample is None:
                sys.exit("먼저 python run.py eval-sample 을 실행하세요.")
            df = df[df["arxiv_id"].isin(sample["arxiv_id"])]
        with timed("classify", "llm", len(df), note="eval_only" if args.eval_only else ""):
            labels = llm_mod.classify_llm(df, model=args.model)
        if args.eval_only:  # 평가용만 분류했으면 전체 라벨 파일을 덮어쓰지 않는다
            labels.to_csv(P / "labels_llm_eval.csv", index=False, encoding="utf-8-sig")
            print(f"[classify] 평가용 LLM 라벨 {len(labels)}건 → labels_llm_eval.csv")
            return
    labels.to_csv(_labels_path(args.approach), index=False, encoding="utf-8-sig")
    print(f"[classify] {args.approach}: {len(labels)}건 → {_labels_path(args.approach).name}")
    print(labels["topic"].value_counts().to_string())


def cmd_summarize(args) -> None:
    from trendlab import classify_llm as llm_mod
    df, labels = clean_mod.load_papers(), _read(_labels_path("llm"))
    if labels is None:
        sys.exit("먼저 python run.py classify llm 을 실행하세요.")
    with timed("summarize", "llm", len(df)):
        s = llm_mod.summarize_topics(df, labels, model=args.model)
    s.to_csv(P / "topic_summaries.csv", index=False, encoding="utf-8-sig")


def cmd_report(args) -> None:
    approach = args.approach or ("llm" if _labels_path("llm").exists() else "keyword")
    df, labels = clean_mod.load_papers(), _read(_labels_path(approach))
    if labels is None:
        sys.exit(f"먼저 python run.py classify {approach} 를 실행하세요.")
    if "relevant" in labels:  # LLM 이 금융×ML 과 무관하다고 판정한 논문은 트렌드 계산에서 제외
        excluded = labels["relevant"] == "False"
        print(f"[report] LLM 판정 무관 논문 {excluded.sum()}건 제외")
        labels = labels[~excluded]
        df = df[df["arxiv_id"].isin(labels["arxiv_id"])]
    config.FIG_DIR.mkdir(parents=True, exist_ok=True)
    config.REPORT_DIR.mkdir(parents=True, exist_ok=True)
    with timed("report", "auto" if approach == "llm" else "keyword", len(df)):
        counts, share = trends.monthly_share(df, labels, "topic")
        trend = trends.trend_table(counts, share)
        m_counts, m_share = trends.monthly_share(df, labels, "method")
        for name, obj in [("monthly_topic_counts", counts), ("monthly_topic_share", share.round(4)),
                          ("monthly_method_share", m_share.round(4))]:
            obj.to_csv(P / f"{name}_{approach}.csv", encoding="utf-8-sig")
        trend.round(4).to_csv(P / f"trend_table_{approach}.csv", index=False, encoding="utf-8-sig")

        report_mod.plot_monthly_counts(counts, config.FIG_DIR / "monthly_counts.png")
        report_mod.plot_share_small_multiples(share[trend["label"]], {k: k for k in TOPICS},
                                              config.FIG_DIR / "topic_share.png", f"Topic share by month (%, {approach})")
        report_mod.plot_share_small_multiples(m_share, {k: k for k in METHODS},
                                              config.FIG_DIR / "method_share.png", f"Method share by month (%, {approach})")
        summaries = _read(P / "topic_summaries.csv") if approach == "llm" else None
        out = config.REPORT_DIR / f"trend_report_{approach}.md"
        report_mod.write_trend_report(df, labels, counts, share, trend, m_share, summaries, approach, out)
    print(f"[report] {out}")


def cmd_eval_sample(args) -> None:
    eval_mod.make_eval_sample(clean_mod.load_papers(), args.n, args.overwrite)


def cmd_evaluate(args) -> None:
    kw = _read(_labels_path("keyword"))
    llm = _read(_labels_path("llm"))
    llm_eval = _read(P / "labels_llm_eval.csv")
    if llm is None:
        llm = llm_eval
    elif llm_eval is not None:
        llm = pd.concat([llm, llm_eval]).drop_duplicates("arxiv_id")
    if kw is None:
        sys.exit("먼저 python run.py classify keyword 를 실행하세요.")
    acc, conf = eval_mod.accuracy_report(kw, llm)
    agreement = None
    if llm is not None:
        m = kw.merge(llm, on="arxiv_id", suffixes=("_kw", "_llm"))
        m = m[m["topic_llm"] != ""]
        if len(m):
            agreement = {"n": len(m), "topic": (m["topic_kw"] == m["topic_llm"]).mean(),
                         "method": (m["method_kw"] == m["method_llm"]).mean()}
    config.REPORT_DIR.mkdir(parents=True, exist_ok=True)
    out = config.REPORT_DIR / "evaluation_report.md"
    report_mod.write_eval_report(acc, conf, eval_mod.time_report(), agreement, out)
    if not acc.empty:
        acc.round(4).to_csv(config.EVAL_DIR / "accuracy.csv", index=False, encoding="utf-8-sig")
    print(f"[evaluate] {out}")


def cmd_all(args) -> None:
    cmd_collect(args)
    cmd_clean(args)
    args.approach = "keyword"
    cmd_classify(args)
    from trendlab import classify_llm as llm_mod
    use_llm = not args.no_llm and llm_mod.has_credentials()
    if use_llm:
        args.approach, args.eval_only = "llm", False
        cmd_classify(args)
        cmd_summarize(args)
    elif not args.no_llm:
        print("[all] ANTHROPIC_API_KEY 없음 → LLM 단계 건너뜀 (키워드 분류로 보고서 생성)")
    args.approach = "llm" if use_llm else "keyword"
    cmd_report(args)
    cmd_eval_sample(argparse.Namespace(n=config.EVAL_SAMPLE_SIZE, overwrite=False))
    cmd_evaluate(args)


def cmd_weekly(args) -> None:
    """기존 데이터에 없는 최신 논문 n편을 추가하고, 분류·보고서를 갱신한다 (매주 GitHub Actions 가 실행)."""
    papers = clean_mod.load_papers()
    with timed("weekly_fetch", "weekly"):
        new = collect_mod.fetch_latest(args.n, set(papers["arxiv_id"]), clean_mod.is_relevant)
    today = date.today().isoformat()
    log_path = config.RUNS_DIR / "weekly_log.csv"
    config.RUNS_DIR.mkdir(parents=True, exist_ok=True)
    if not log_path.exists():
        log_path.write_text("date,added,arxiv_ids\n", encoding="utf-8")
    with log_path.open("a", encoding="utf-8") as f:
        f.write(f"{today},{len(new)},{' '.join(r['arxiv_id'] for r in new)}\n")
    if not new:
        print("[weekly] 새 논문 없음")
        return

    raw = config.RAW_DIR / f"weekly_{today}.json"
    prev = json.loads(raw.read_text(encoding="utf-8")) if raw.exists() else []
    raw.write_text(json.dumps(prev + new, ensure_ascii=False, indent=1), encoding="utf-8")
    add = pd.DataFrame(new).assign(month=lambda d: d["published"].str[:7])[papers.columns]
    pd.concat([papers, add]).to_csv(P / "papers.csv", index=False, encoding="utf-8-sig")
    for r in new:
        print(f"[weekly] + ({r['published']}) {r['title'][:80]}")
    print(f"[weekly] {len(new)}편 추가 → 총 {len(papers) + len(new)}편")

    args.approach, args.eval_only = "keyword", False
    cmd_classify(args)
    from trendlab import classify_llm as llm_mod
    use_llm = llm_mod.has_credentials()
    if use_llm:  # 이미 분류한 논문은 캐시되므로 새 논문만 API 비용이 든다
        args.approach = "llm"
        cmd_classify(args)
        cmd_summarize(args)
    args.approach = "llm" if use_llm else "keyword"
    cmd_report(args)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    model = {"default": config.LLM_MODEL, "help": f"Claude 모델 (기본 {config.LLM_MODEL})"}

    s = sub.add_parser("collect"); s.add_argument("--reference-date", help="YYYY-MM-DD (기본: 오늘)")
    sub.add_parser("clean")
    s = sub.add_parser("classify"); s.add_argument("approach", choices=["keyword", "llm"])
    s.add_argument("--eval-only", action="store_true", help="평가용 100건만 LLM 분류 (비용 절약)")
    s.add_argument("--model", **model)
    s = sub.add_parser("summarize"); s.add_argument("--model", **model)
    s = sub.add_parser("report"); s.add_argument("--approach", choices=["keyword", "llm"])
    s = sub.add_parser("eval-sample"); s.add_argument("--n", type=int, default=config.EVAL_SAMPLE_SIZE)
    s.add_argument("--overwrite", action="store_true", help="기존 평가 샘플(수작업 라벨 포함)을 덮어씀")
    sub.add_parser("evaluate")
    s = sub.add_parser("weekly"); s.add_argument("--n", type=int, default=5, help="추가할 논문 수 (기본 5)")
    s.add_argument("--model", **model)
    s = sub.add_parser("all"); s.add_argument("--reference-date"); s.add_argument("--no-llm", action="store_true")
    s.add_argument("--model", **model)

    args = p.parse_args()
    {"collect": cmd_collect, "clean": cmd_clean, "classify": cmd_classify, "summarize": cmd_summarize,
     "report": cmd_report, "eval-sample": cmd_eval_sample, "evaluate": cmd_evaluate, "weekly": cmd_weekly, "all": cmd_all}[args.cmd](args)


if __name__ == "__main__":
    main()
