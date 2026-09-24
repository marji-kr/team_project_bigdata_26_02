"""수집한 논문을 자동 분석한다.

1. TF-IDF 핵심 키워드 추출 (논문별 / 전체)
2. 사전 기반 태깅: ML 방법론 · 금융 과제 · 데이터 유형
3. 추출 요약 (TF-IDF 점수가 높은 문장 2개)
4. 논문 간 코사인 유사도
5. 그림(figures/) + 마크다운 리포트(reports/analysis_report.md) + CSV(data/)
"""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

EXTRA_STOP = {"paper", "propose", "proposed", "approach", "method", "methods", "results", "using",
              "based", "study", "show", "model", "models", "data", "new", "use", "used", "also"}
STOP_WORDS = list(ENGLISH_STOP_WORDS | EXTRA_STOP)

TAXONOMY = {
    "ml_method": {
        "LLM / Foundation Model": r"\b(llm|large language model|gpt|language model|foundation model|agent)",
        "Transformer / Attention": r"\b(transformer|attention)",
        "Reinforcement Learning": r"\b(reinforcement learning|q-learning|policy gradient|\brl\b|actor-critic)",
        "Graph Neural Network": r"\b(graph neural|gnn|graph convolution)",
        "RNN / LSTM": r"\b(lstm|gru|recurrent)",
        "Generative (Diffusion/GAN/VAE)": r"\b(diffusion|gan\b|generative adversarial|vae\b|variational autoencoder|generative)",
        "Tree Ensemble": r"\b(xgboost|lightgbm|random forest|gradient boost)",
        "Deep Learning (general)": r"\b(deep learning|neural network|cnn|convolutional|mixture-of-experts)",
        "Multi-task / Transfer": r"\b(multi-task|transfer learning|meta-learning)",
        "Bayesian / Probabilistic": r"\b(bayesian|gaussian process|probabilistic)",
        "Machine Learning (general)": r"\b(machine learning|supervised|classifier|regression tree)",
    },
    "finance_task": {
        "Return / Price Prediction": r"\b(return prediction|forecast|price prediction|predict(ing)? (stock|return|price))",
        "Portfolio Optimization": r"\b(portfolio|asset allocation)",
        "Trading / Execution": r"\b(trading|execution|market making|order book|high-frequency)",
        "Risk / Volatility": r"\b(volatility|risk|value-at-risk|var\b|tail)",
        "Derivatives / Option Pricing": r"\b(option pricing|derivative|hedging|implied volatility)",
        "Credit / Default": r"\b(credit|default|loan|bankruptcy)",
        "Fraud / AML": r"\b(fraud|anti-money|aml\b|anomaly)",
        "Factor / Asset Pricing": r"\b(factor|asset pricing|cross-section|anomal)",
        "Crypto": r"\b(crypto|bitcoin|blockchain|defi)",
    },
    "data_type": {
        "Time Series": r"\b(time series|time-series|temporal)",
        "Text / News / Sentiment": r"\b(news|sentiment|text|textual|earnings call|social media)",
        "Limit Order Book": r"\b(limit order book|\blob\b|order flow)",
        "Synthetic / Simulation": r"\b(synthetic|simulat)",
        "Fundamental / Accounting": r"\b(fundamental|accounting|financial statement)",
    },
}


def _doc(row: pd.Series) -> str:
    return f"{row['title']}. {row.get('abstract') or ''}"


def tag_papers(df: pd.DataFrame) -> pd.DataFrame:
    tags = {}
    for group, rules in TAXONOMY.items():
        tags[group] = [
            "; ".join(name for name, pat in rules.items() if re.search(pat, _doc(r).lower())) or "-"
            for _, r in df.iterrows()
        ]
    return df.assign(**tags)


def extract_keywords(df: pd.DataFrame, top_k: int = 8):
    vec = TfidfVectorizer(stop_words=STOP_WORDS, ngram_range=(1, 2), min_df=1,
                          token_pattern=r"(?u)\b[a-zA-Z][a-zA-Z\-]{2,}\b", sublinear_tf=True)
    X = vec.fit_transform(df.apply(_doc, axis=1))
    vocab = np.array(vec.get_feature_names_out())
    per_paper = [", ".join(vocab[np.argsort(row)[::-1][:top_k]]) for row in X.toarray()]
    overall = pd.Series(np.asarray(X.sum(axis=0)).ravel(), index=vocab).sort_values(ascending=False)
    return X, per_paper, overall


def summarize(text: str, n_sent: int = 2) -> str:
    """문장 단위 TF-IDF 점수로 핵심 문장을 원래 순서대로 뽑는 추출 요약."""
    sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text or "") if len(s.split()) > 5]
    if len(sents) <= n_sent:
        return " ".join(sents) or (text or "")
    X = TfidfVectorizer(stop_words=STOP_WORDS).fit_transform(sents)
    scores = np.asarray(X.sum(axis=1)).ravel() / np.sqrt(np.array([len(s.split()) for s in sents]))
    keep = sorted(np.argsort(scores)[::-1][:n_sent])
    return " ".join(sents[i] for i in keep)


def plot_keywords(overall: pd.Series, path: Path, top: int = 15) -> None:
    s = overall.head(top)[::-1]
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.barh(s.index, s.values, color="#3b6ea5")
    ax.set_title("Top TF-IDF keywords (all papers)")
    ax.set_xlabel("Summed TF-IDF weight")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_similarity(sim: np.ndarray, labels: list[str], path: Path) -> None:
    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(sim, cmap="Blues", vmin=0, vmax=1)
    ax.set_xticks(range(len(labels)), labels)
    ax.set_yticks(range(len(labels)), labels)
    for i in range(len(labels)):
        for j in range(len(labels)):
            ax.text(j, i, f"{sim[i, j]:.2f}", ha="center", va="center",
                    color="white" if sim[i, j] > 0.6 else "black", fontsize=9)
    ax.set_title("Paper-to-paper cosine similarity (TF-IDF)")
    fig.colorbar(im, ax=ax, fraction=0.046)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_tags(df: pd.DataFrame, path: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    for ax, col, title in zip(axes, ["ml_method", "finance_task"], ["ML method", "Finance task"]):
        counts = df[col].str.split("; ").explode().loc[lambda s: s != "-"].value_counts()[::-1]
        ax.barh(counts.index, counts.values, color="#5a9e6f")
        ax.set_title(title)
        ax.xaxis.get_major_locator().set_params(integer=True)
        ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def write_report(df: pd.DataFrame, overall: pd.Series, sim: np.ndarray, path: Path) -> None:
    labels = [f"P{i + 1}" for i in range(len(df))]
    iu = np.triu_indices(len(df), k=1)
    best = int(np.argmax(sim[iu])) if len(iu[0]) else None

    lines = [
        "# 금융 머신러닝 최신 논문 자동 분석 리포트",
        "",
        f"- 생성 시각: {datetime.now():%Y-%m-%d %H:%M}",
        f"- 논문 수: {len(df)}편 (출처: {', '.join(df['source'].unique())})",
        f"- 전체 상위 키워드: {', '.join(overall.head(10).index)}",
        "",
        "## 1. 논문 목록",
        "",
        "| # | 제목 | 게재일 | ML 방법론 | 금융 과제 |",
        "|---|---|---|---|---|",
    ]
    for lab, (_, r) in zip(labels, df.iterrows()):
        lines.append(f"| {lab} | [{r['title']}]({r['url']}) | {r['published']} | {r['ml_method']} | {r['finance_task']} |")

    lines += ["", "## 2. 논문별 분석", ""]
    for lab, (_, r) in zip(labels, df.iterrows()):
        lines += [
            f"### {lab}. {r['title']}",
            "",
            f"- **저자**: {r['authors']}",
            f"- **게재**: {r['venue']} ({r['published']})" + (f" · 인용 {int(r['cited_by'])}회" if pd.notna(r.get('cited_by')) else ""),
            f"- **ML 방법론**: {r['ml_method']}",
            f"- **금융 과제**: {r['finance_task']}",
            f"- **데이터 유형**: {r['data_type']}",
            f"- **핵심 키워드**: {r['keywords']}",
            f"- **자동 요약**: {r['summary']}",
            "",
        ]

    lines += [
        "## 3. 교차 분석",
        "",
        "![tags](../figures/tag_distribution.png)",
        "",
        "![keywords](../figures/top_keywords.png)",
        "",
        "![similarity](../figures/similarity_heatmap.png)",
        "",
    ]
    if best is not None:
        i, j = iu[0][best], iu[1][best]
        lines.append(f"- 가장 유사한 논문 쌍: **{labels[i]} ↔ {labels[j]}** (코사인 유사도 {sim[i, j]:.2f})")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def analyze(root: Path) -> pd.DataFrame:
    data_dir, fig_dir, rep_dir = root / "data", root / "figures", root / "reports"
    fig_dir.mkdir(exist_ok=True)
    rep_dir.mkdir(exist_ok=True)

    df = pd.read_csv(data_dir / "papers.csv", encoding="utf-8-sig")
    df = tag_papers(df)
    X, df["keywords"], overall = extract_keywords(df)
    df["summary"] = df["abstract"].fillna("").map(summarize)
    sim = cosine_similarity(X)

    labels = [f"P{i + 1}" for i in range(len(df))]
    plot_keywords(overall, fig_dir / "top_keywords.png")
    plot_similarity(sim, labels, fig_dir / "similarity_heatmap.png")
    plot_tags(df, fig_dir / "tag_distribution.png")

    df.to_csv(data_dir / "papers_analysis.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(sim, index=labels, columns=labels).round(4).to_csv(data_dir / "similarity_matrix.csv")
    write_report(df, overall, sim, rep_dir / "analysis_report.md")
    print(f"[analyze] 리포트: {rep_dir / 'analysis_report.md'}")
    return df


if __name__ == "__main__":
    analyze(Path(__file__).resolve().parents[1])
