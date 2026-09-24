"""수집한 논문을 자동 분석한다. PDF 본문(data/fulltext/)이 있으면 본문 기준으로 분석한다.

1. TF-IDF 핵심 키워드 추출 (논문별 / 전체)
2. 사전 기반 태깅: ML 방법론 · 금융 과제 · 데이터 유형 (본문 언급 횟수 기준)
3. 본문 정보 추출: 사용 데이터셋/시장, 평가지표, 섹션 구성, 그림·표 수
4. 추출 요약: 초록 요약 + 결론 섹션 요약
5. 논문 간 코사인 유사도
6. 그림(figures/) + 마크다운 리포트(reports/analysis_report.md) + CSV(data/)
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

from pdf_fulltext import body_text, split_sections

EXTRA_STOP = {"paper", "propose", "proposed", "approach", "method", "methods", "results", "using",
              "based", "study", "show", "model", "models", "data", "new", "use", "used", "also",
              "et", "al", "fig", "figure", "table", "section", "eq", "arxiv", "https", "http", "www",
              "doi", "org", "let", "given", "denote", "denotes", "respectively", "thus", "does", "non"}
STOP_WORDS = list(ENGLISH_STOP_WORDS | EXTRA_STOP)

# 본문에서 이 횟수 이상 언급되어야 태그를 붙인다 (제목·초록에 나오면 1회로 충분)
MIN_BODY_MENTIONS = 3

TAXONOMY = {
    "ml_method": {
        "LLM / Foundation Model": r"\b(llms?|large language models?|gpt|foundation models?)\b",
        "Transformer / Attention": r"\b(transformers?|self-attention|attention mechanism)\b",
        "Reinforcement Learning": r"\b(reinforcement learning|q-learning|policy gradient|actor-critic|bandits?)\b",
        "Graph Neural Network": r"\b(graph neural|gnns?|graph convolution)",
        "RNN / LSTM": r"\b(lstm|gru|recurrent neural)",
        "Generative (Diffusion/GAN/VAE)": r"\b(diffusion models?|gans?|generative adversarial|vaes?|variational autoencoder)\b",
        "Tree Ensemble": r"\b(xgboost|lightgbm|random forests?|gradient boost)",
        "Deep Learning (general)": r"\b(deep learning|neural networks?|cnns?|convolutional|mixture-of-experts|mlp)\b",
        "Multi-task / Transfer": r"\b(multi-task|transfer learning|meta-learning)",
        "Bayesian / Probabilistic": r"\b(bayesian|gaussian process)",
        "Machine Learning (general)": r"\b(machine learning|supervised learning|classifiers?)\b",
    },
    "finance_task": {
        "Return / Price Prediction": r"\b(return prediction|return forecasting|price prediction|stock forecasting|predict(ing)? (stock|returns?|prices?))",
        "Portfolio Optimization": r"\b(portfolio optimi[sz]ation|asset allocation|portfolio construction)",
        "Trading / Execution": r"\b(trading strateg(y|ies)|algorithmic trading|execution|market making|order book|high-frequency)",
        "Risk / Volatility": r"\b(volatility|risk measures?|value-at-risk|expected shortfall|tail risk)",
        "Derivatives / Option Pricing": r"\b(option pricing|derivatives pricing|hedging|implied volatility)",
        "Credit / Default": r"\b(credit risk|default|loans?|bankruptcy)\b",
        "Fraud / AML": r"\b(fraud|anti-money laundering|aml)\b",
        "Factor / Asset Pricing": r"\b(factor (mining|model|investing|zoo)|asset pricing|cross-section(al)? (of )?returns?|alpha factors?)",
        "Crypto": r"\b(crypto(currenc(y|ies))?|bitcoin|blockchain|defi)\b",
    },
    "data_type": {
        "Time Series": r"\b(time series|time-series)",
        "Text / News / Sentiment": r"\b(news|sentiment|earnings calls?|social media|textual)",
        "Limit Order Book": r"\b(limit order book|order flow)",
        "Synthetic / Simulation": r"\b(synthetic data|simulation study|monte carlo|simulated)",
        "Fundamental / Accounting": r"\b(fundamentals?|accounting|financial statements?)\b",
    },
}

# 본문에서 찾는 데이터셋·시장 이름
DATASETS = {
    "S&P 500": r"s&p\s?500", "CSI 300": r"csi\s?300", "CSI 500": r"csi\s?500", "NASDAQ": r"nasdaq",
    "Dow Jones / DJIA": r"dow jones|djia", "NYSE": r"\bnyse\b", "Russell": r"russell\s?\d{4}",
    "CRSP": r"\bcrsp\b", "Compustat": r"compustat", "WRDS": r"\bwrds\b", "TAQ": r"\btaq\b",
    "LOBSTER": r"\blobster\b", "Bloomberg": r"bloomberg", "Reuters": r"reuters", "Yahoo Finance": r"yahoo finance",
    "FNSPID": r"fnspid", "Bitcoin": r"bitcoin|\bbtc\b", "KOSPI": r"kospi", "Nikkei": r"nikkei",
    "Fama-French": r"fama[- ]french", "FRED": r"\bfred\b", "EDGAR / SEC filings": r"edgar|10-k|sec filings",
}
METRICS = {
    "Sharpe ratio": r"sharpe", "Sortino": r"sortino", "Max drawdown": r"max(imum)? drawdown|\bmdd\b",
    "Annualized return": r"annuali[sz]ed returns?|\barr\b", "IC / Rank IC": r"\brank ?ic\b|\bic\b|information coefficient",
    "RMSE / MSE": r"\brmse\b|\bmse\b|mean squared error", "MAE": r"\bmae\b|mean absolute error",
    "Accuracy": r"\baccuracy\b", "F1": r"\bf1\b", "AUC": r"\bauc\b|roc curve", "R²": r"\br\^?2\b|r-squared|\br²",
    "VaR / ES": r"value-at-risk|\bvar\b|expected shortfall|\bcvar\b", "Turnover": r"turnover",
}


def _load_fulltext(df: pd.DataFrame, root: Path) -> pd.DataFrame:
    texts = []
    for _, r in df.iterrows():
        path = r.get("fulltext_path")
        texts.append((root / path).read_text(encoding="utf-8") if isinstance(path, str) and (root / path).exists() else "")
    return df.assign(fulltext=texts)


def _head(row: pd.Series) -> str:
    return f"{row['title']}. {row.get('abstract') or ''}"


def _doc(row: pd.Series) -> str:
    """분석용 문서: 본문이 있으면 참고문헌 전까지의 본문, 없으면 제목+초록."""
    return f"{_head(row)} {body_text(row['fulltext'])}" if row["fulltext"] else _head(row)


def tag_papers(df: pd.DataFrame) -> pd.DataFrame:
    tags = {group: [] for group in TAXONOMY}
    for _, r in df.iterrows():
        head, body = _head(r).lower(), body_text(r["fulltext"]).lower()
        for group, rules in TAXONOMY.items():
            hits = [name for name, pat in rules.items()
                    if re.search(pat, head) or len(re.findall(pat, body)) >= MIN_BODY_MENTIONS]
            tags[group].append("; ".join(hits) or "-")
    return df.assign(**tags)


def find_mentions(df: pd.DataFrame, vocab: dict[str, str], min_count: int = 2) -> list[str]:
    out = []
    for _, r in df.iterrows():
        text = _doc(r).lower()
        counts = {name: len(re.findall(pat, text)) for name, pat in vocab.items()}
        hits = sorted((n for n, c in counts.items() if c >= min_count), key=lambda n: -counts[n])
        out.append("; ".join(f"{n}({counts[n]})" for n in hits) or "-")
    return out


def extract_keywords(df: pd.DataFrame, top_k: int = 10):
    vec = TfidfVectorizer(stop_words=STOP_WORDS, ngram_range=(1, 2), min_df=1, max_df=0.8 if len(df) > 2 else 1.0,
                          token_pattern=r"(?u)\b[a-zA-Z][a-zA-Z\-]{2,}\b", sublinear_tf=True)
    X = vec.fit_transform(df.apply(_doc, axis=1))
    vocab = np.array(vec.get_feature_names_out())
    per_paper = [", ".join(vocab[np.argsort(row)[::-1][:top_k]]) for row in X.toarray()]
    overall = pd.Series(np.asarray(X.sum(axis=0)).ravel(), index=vocab).sort_values(ascending=False)
    return X, per_paper, overall


def summarize(text: str, n_sent: int = 2) -> str:
    """문장 단위 TF-IDF 점수로 핵심 문장을 원래 순서대로 뽑는 추출 요약."""
    sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text or "") if 6 < len(s.split()) < 60]
    if len(sents) <= n_sent:
        return " ".join(sents) or (text or "")[:400]
    X = TfidfVectorizer(stop_words=STOP_WORDS).fit_transform(sents)
    scores = np.asarray(X.sum(axis=1)).ravel() / np.sqrt(np.array([len(s.split()) for s in sents]))
    keep = sorted(np.argsort(scores)[::-1][:n_sent])
    return " ".join(sents[i] for i in keep)


def structure_stats(text: str) -> dict:
    if not text:
        return {"sections": "-", "n_figures": None, "n_tables": None, "n_words": None, "conclusion_summary": "-"}
    sections = split_sections(text)
    body = body_text(text)
    return {
        "sections": ", ".join(k for k in sections if k != "references") or "-",
        "n_figures": len(set(re.findall(r"\bFig(?:ure|\.)\s?(\d+)", body))),
        "n_tables": len(set(re.findall(r"\bTable\s?(\d+)", body))),
        "n_words": len(body.split()),
        "conclusion_summary": summarize(sections.get("conclusion", ""), 3) if "conclusion" in sections else "-",
    }


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


def _fmt(v) -> str:
    return "-" if v is None or (isinstance(v, float) and np.isnan(v)) else f"{int(v):,}"


def write_report(df: pd.DataFrame, overall: pd.Series, sim: np.ndarray, path: Path) -> None:
    labels = [f"P{i + 1}" for i in range(len(df))]
    iu = np.triu_indices(len(df), k=1)
    best = int(np.argmax(sim[iu])) if len(iu[0]) else None
    n_full = int((df["fulltext"] != "").sum())

    lines = [
        "# 금융 머신러닝 최신 논문 자동 분석 리포트",
        "",
        f"- 생성 시각: {datetime.now():%Y-%m-%d %H:%M}",
        f"- 논문 수: {len(df)}편 (출처: {', '.join(df['source'].unique())}) · PDF 본문 분석 {n_full}편",
        f"- 전체 상위 키워드: {', '.join(overall.head(10).index)}",
        "",
        "## 1. 논문 목록",
        "",
        "| # | 제목 | 게재일 | 쪽수 | ML 방법론 | 금융 과제 |",
        "|---|---|---|---|---|---|",
    ]
    for lab, (_, r) in zip(labels, df.iterrows()):
        pdf = f" · [PDF]({r['pdf_url']})" if isinstance(r.get("pdf_url"), str) else ""
        lines.append(f"| {lab} | [{r['title']}]({r['url']}){pdf} | {r['published']} | {_fmt(r.get('n_pages'))} "
                     f"| {r['ml_method']} | {r['finance_task']} |")

    lines += ["", "## 2. 논문별 분석", ""]
    for lab, (_, r) in zip(labels, df.iterrows()):
        cited = f" · 인용 {int(r['cited_by'])}회" if pd.notna(r.get("cited_by")) else ""
        lines += [
            f"### {lab}. {r['title']}",
            "",
            f"- **저자**: {r['authors']}",
            f"- **게재**: {r['venue']} ({r['published']}){cited}",
            f"- **분량**: {_fmt(r.get('n_pages'))}쪽 · 본문 {_fmt(r['n_words'])}단어 · 그림 {_fmt(r['n_figures'])}개 · 표 {_fmt(r['n_tables'])}개",
            f"- **섹션 구성**: {r['sections']}",
            f"- **ML 방법론**: {r['ml_method']}",
            f"- **금융 과제**: {r['finance_task']}",
            f"- **데이터 유형**: {r['data_type']}",
            f"- **사용 데이터셋·시장 (언급 횟수)**: {r['datasets']}",
            f"- **평가지표 (언급 횟수)**: {r['metrics']}",
            f"- **핵심 키워드**: {r['keywords']}",
            f"- **초록 요약**: {r['summary']}",
            f"- **결론 요약**: {r['conclusion_summary']}",
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
    df = _load_fulltext(df, root)
    df = tag_papers(df)
    X, df["keywords"], overall = extract_keywords(df)
    df["summary"] = df["abstract"].fillna("").map(summarize)
    df["datasets"] = find_mentions(df, DATASETS)
    df["metrics"] = find_mentions(df, METRICS)
    df = pd.concat([df, pd.DataFrame([structure_stats(t) for t in df["fulltext"]], index=df.index)], axis=1)
    sim = cosine_similarity(X)

    labels = [f"P{i + 1}" for i in range(len(df))]
    plot_keywords(overall, fig_dir / "top_keywords.png")
    plot_similarity(sim, labels, fig_dir / "similarity_heatmap.png")
    plot_tags(df, fig_dir / "tag_distribution.png")

    df.drop(columns="fulltext").to_csv(data_dir / "papers_analysis.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(sim, index=labels, columns=labels).round(4).to_csv(data_dir / "similarity_matrix.csv")
    write_report(df, overall, sim, rep_dir / "analysis_report.md")
    print(f"[analyze] 리포트: {rep_dir / 'analysis_report.md'}")
    return df


if __name__ == "__main__":
    analyze(Path(__file__).resolve().parents[1])
