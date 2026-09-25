"""그림과 마크다운 보고서 생성.

- trend_report.md      : 월별 주제 비중 + 증가/감소 주제 + 주제별 요약과 근거 논문 링크 (수작업 보고서와 같은 형식)
- evaluation_report.md : 수작업 대비 정확도·소요 시간 (성공 기준)
"""
from __future__ import annotations

from datetime import datetime

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

import config
from .taxonomy import METHODS, TOPICS

BLUE, INK, MUTED, GRID = "#2a78d6", "#1f1f1e", "#6b6a64", "#e4e3dc"


def _style(ax):
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=8)
    ax.grid(axis="y", color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)


def plot_monthly_counts(counts: pd.DataFrame, path) -> None:
    total = counts.sum(axis=1)
    fig, ax = plt.subplots(figsize=(7, 3))
    ax.bar(total.index, total.values, color=BLUE, width=0.6)
    for x, v in zip(total.index, total.values):
        ax.text(x, v, f"{v}", ha="center", va="bottom", fontsize=8, color=INK)
    ax.set_title("Papers per month", loc="left", fontsize=10, color=INK)
    _style(ax)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_share_small_multiples(share: pd.DataFrame, names: dict, path, title: str) -> None:
    """라벨이 8개를 넘으므로 색으로 구분하지 않고 라벨마다 작은 그래프 하나 (small multiples, 같은 y축)."""
    cols = [c for c in share.columns]
    n = len(cols)
    ncol = 4
    nrow = -(-n // ncol)
    fig, axes = plt.subplots(nrow, ncol, figsize=(12, 2.3 * nrow), sharey=True)
    ymax = share.values.max() * 100 * 1.15
    months = [m[2:] for m in share.index]  # "26-03"
    for ax, col in zip(axes.flat, cols):
        y = share[col].values * 100
        ax.plot(months, y, color=BLUE, linewidth=2, marker="o", markersize=4)
        ax.set_title(names.get(col, col), loc="left", fontsize=9, color=INK)
        ax.annotate(f"{y[-1]:.0f}%", (months[-1], y[-1]), textcoords="offset points", xytext=(4, 4),
                    fontsize=8, color=INK)
        ax.set_ylim(0, ymax)
        _style(ax)
    for ax in list(axes.flat)[n:]:
        ax.axis("off")
    fig.suptitle(title, x=0.01, ha="left", fontsize=11, color=INK)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def _link(row) -> str:
    return f"[{row.title}]({row.url})"


def write_trend_report(df, labels, counts, share, trend, m_share, summaries, approach: str, path) -> None:
    names = {k: v["name"] for k, v in TOPICS.items()}
    merged = df.merge(labels, on="arxiv_id")
    months = list(share.index)
    L = [
        f"# {config.FIELD_NAME} 연구 동향 보고서",
        "",
        f"- 생성: {datetime.now():%Y-%m-%d %H:%M} · 분류 방식: **{approach}**",
        f"- 데이터: arXiv API, {months[0]} ~ {months[-1]} ({len(months)}개월), 논문 {len(df)}건",
        "- 월별 비중은 LLM 이 아니라 코드로 계산 (해당 월 논문 수 대비 비율)",
        "",
        "## 1. 월별 논문 수",
        "",
        "![monthly counts](../figures/monthly_counts.png)",
        "",
        "## 2. 주제별 월별 비중",
        "",
        "![topic share](../figures/topic_share.png)",
        "",
        "| 주제 | 논문 수 | 전체 비중 | " + " | ".join(m[2:] for m in months) + " | 전반→후반 (%p) |",
        "|---|---:|---:|" + "---:|" * len(months) + "---:|",
    ]
    for r in trend.itertuples():
        monthly = " | ".join(f"{share.loc[m, r.label] * 100:.0f}%" for m in months)
        L.append(f"| {names.get(r.label, r.label)} | {r.papers} | {r.overall_share * 100:.1f}% | {monthly} | {r.change_pp:+.1f} |")

    small = [f"{m} ({int(counts.loc[m].sum())}건)" for m in months if counts.loc[m].sum() < 30]
    if small:
        L += ["", f"> ⚠️ 논문이 30건 미만인 달은 비중이 크게 흔들리므로 해석에 주의: {', '.join(small)}"]

    movers = trend[trend["label"] != "other"].sort_values("change_pp")
    L += ["", "## 3. 증가·감소 주제", ""]
    for title, rows in [("증가", movers.tail(3)[::-1]), ("감소", movers.head(3))]:
        L.append(f"**{title}**: " + ", ".join(
            f"{names[r.label]} ({r.change_pp:+.1f}%p, 기울기 {r.slope_pp_per_month:+.2f}%p/월)" for r in rows.itertuples()))
        L.append("")

    L += ["## 4. 주제별 요약과 근거 논문", ""]
    summ = summaries.set_index("topic") if summaries is not None and len(summaries) else None
    for r in trend.itertuples():
        g = merged[merged["topic"] == r.label]
        L += [f"### {names.get(r.label, r.label)} ({r.papers}건)", ""]
        if summ is not None and r.label in summ.index:
            L += [summ.loc[r.label, "summary_ko"], ""]
            ev = [i for i in str(summ.loc[r.label, "evidence_ids"]).split("; ") if i]
            ev_rows = g[g["arxiv_id"].isin(ev)]
        else:
            ev_rows = g.sort_values("published").tail(3)
        L.append("근거 논문:")
        for p in ev_rows.itertuples():
            extra = f" — {p.summary_ko}" if "summary_ko" in g and getattr(p, "summary_ko", "") else ""
            L.append(f"- ({p.month}) {_link(p)}{extra}")
        L.append("")

    if m_share is not None:
        L += ["## 5. 방법론 비중 (보조)", "", "![method share](../figures/method_share.png)", "",
              "| 방법론 | " + " | ".join(m[2:] for m in months) + " |", "|---|" + "---:|" * len(months)]
        for col in m_share.columns:
            L.append(f"| {METHODS[col]['name']} | " + " | ".join(f"{m_share.loc[m, col] * 100:.0f}%" for m in months) + " |")
        L.append("")
    path.write_text("\n".join(L), encoding="utf-8")


def write_eval_report(acc: pd.DataFrame, confusions: dict, timing: dict | None, agreement: dict | None, path) -> None:
    L = ["# 평가 보고서 (문제정의서 4. 성공 기준)", "", f"- 생성: {datetime.now():%Y-%m-%d %H:%M}", ""]
    L += ["## 1. 소요 시간 (주 지표)", ""]
    if timing is None or timing["manual_min"] is None:
        L += ["수작업 소요 시간이 아직 기록되지 않았습니다 → `data/eval/manual_timing.csv` 의 minutes 칸을 채우세요.", ""]
        if timing:
            L += [f"- AI 자동 실행 시간(최근 실행): {timing['ai_auto_min']:.1f}분", ""]
    else:
        verdict = "달성 ✅" if timing["passed"] else "미달 ❌"
        L += [
            "| 방식 | 소요 시간(분) |", "|---|---:|",
            f"| 수작업 | {timing['manual_min']:.1f} |",
            f"| AI (자동 실행 {timing['ai_auto_min']:.1f} + 사람 검토 {timing['ai_review_min']:.1f}) | {timing['ai_total_min']:.1f} |",
            "",
            f"**단축률 {timing['reduction'] * 100:.1f}%** (목표 {timing['target'] * 100:.0f}% 이상) → {verdict}", "",
        ]
    L += ["## 2. 분류 정확도 (수작업 라벨 = 정답)", ""]
    if acc.empty:
        L += ["수작업 라벨이 아직 없습니다 → `data/eval/eval_sample.csv` 의 manual_topic, manual_method 칸을 채우세요.", ""]
    else:
        L += ["| 대상 | 방식 | n | 정확도 | Macro-F1 | Cohen's κ |", "|---|---|---:|---:|---:|---:|"]
        for r in acc.itertuples():
            L.append(f"| {r.target} | {r.approach} | {r.n} | {r.accuracy:.3f} | {r.macro_f1:.3f} | {r.cohen_kappa:.3f} |")
        L.append("")
        for name, cm in confusions.items():
            L += [f"**혼동행렬 (topic, {name})**", "", cm.to_markdown(), ""]
    if agreement:
        L += ["## 3. 전체 논문에서 키워드 vs LLM 분류 일치율 (참고)", "",
              f"- topic 일치율 {agreement['topic'] * 100:.1f}% · method 일치율 {agreement['method'] * 100:.1f}% (n={agreement['n']})", ""]
    path.write_text("\n".join(L), encoding="utf-8")
