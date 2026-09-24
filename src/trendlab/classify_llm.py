"""LLM(Claude API) 기반 분류·요약.

1. classify_llm : 논문 N편씩 묶어 topic/method 라벨 + 한국어 한 줄 요약을 JSON 으로 받는다.
   결과는 data/processed/llm_cache.jsonl 에 캐시되어 재실행 시 API 를 다시 부르지 않는다.
2. summarize_topics : 주제별로 논문 요약들을 모아 '동향 요약 + 근거 논문 ID' 를 받는다.
   근거 ID 는 코드가 실제 논문 링크로 바꾼다 (LLM 이 만든 링크를 그대로 쓰지 않음).

논문 수·월별 비중 계산은 LLM 이 아니라 trends.py 의 코드가 한다 (문제정의서 2절).
인증: ANTHROPIC_API_KEY 환경변수 또는 .env 파일.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import anthropic
import pandas as pd

import config
from .taxonomy import METHOD_IDS, METHODS, TAXONOMY_VERSION, TOPIC_IDS, TOPICS

CACHE = config.PROCESSED_DIR / "llm_cache.jsonl"
USAGE_LOG = config.RUNS_DIR / "llm_usage.csv"
FALLBACK_BETA = "server-side-fallback-2026-07-01"


def load_env() -> None:
    env = config.ROOT / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def has_credentials() -> bool:
    load_env()
    return bool(os.getenv("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_AUTH_TOKEN"))


def _taxonomy_text() -> str:
    t = "\n".join(f"- {k}: {v['desc']}" for k, v in TOPICS.items())
    m = "\n".join(f"- {k}: {v['desc']}" for k, v in METHODS.items())
    return f"TOPICS (the financial problem the paper addresses):\n{t}\n\nMETHODS (main ML technique):\n{m}"


CLASSIFY_SYSTEM = f"""You label recent arXiv papers for a research-trend study of financial machine learning.
For each paper pick exactly one topic and one method from the lists below, based on the paper's main contribution.
When several topics apply, choose the one the paper's evaluation or application is about.
Use "other" only when no listed label fits.

{_taxonomy_text()}

Set relevant=false if the paper does not actually apply machine learning to a finance or economics problem
(e.g., keyword matches such as "portfolio of software" or "trading off accuracy").
Also write summary_ko: one Korean sentence (max 60 characters) stating what the paper does and how."""

CLASSIFY_SCHEMA = {
    "type": "object",
    "properties": {
        "results": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "relevant": {"type": "boolean"},
                    "topic": {"type": "string", "enum": TOPIC_IDS},
                    "method": {"type": "string", "enum": METHOD_IDS},
                    "summary_ko": {"type": "string"},
                },
                "required": ["id", "relevant", "topic", "method", "summary_ko"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["results"],
    "additionalProperties": False,
}

TOPIC_SUMMARY_SCHEMA = {
    "type": "object",
    "properties": {
        "summary_ko": {"type": "string"},
        "evidence_ids": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["summary_ko", "evidence_ids"],
    "additionalProperties": False,
}


class LLMClient:
    def __init__(self, model: str = config.LLM_MODEL, effort: str = config.LLM_EFFORT):
        load_env()
        self.client = anthropic.Anthropic()
        self.model, self.effort = model, effort

    def ask_json(self, system: str, user: str, schema: dict, stage: str, max_tokens: int = 16000) -> dict:
        """구조화 출력(JSON schema)으로 요청한다. 거절 시 서버측 fallback 모델이 이어받는다."""
        resp = self.client.beta.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
            output_config={"effort": self.effort, "format": {"type": "json_schema", "schema": schema}},
            betas=[FALLBACK_BETA],
            fallbacks="default",
        )
        self._log_usage(stage, resp)
        if resp.stop_reason == "refusal":
            raise RuntimeError(f"LLM refused ({stage}): {resp.stop_details}")
        if resp.stop_reason == "max_tokens":
            raise RuntimeError(f"LLM output truncated ({stage}); reduce LLM_BATCH_SIZE")
        text = next(b.text for b in resp.content if b.type == "text")
        return json.loads(text)

    def _log_usage(self, stage: str, resp) -> None:
        config.RUNS_DIR.mkdir(parents=True, exist_ok=True)
        new = not USAGE_LOG.exists()
        with USAGE_LOG.open("a", encoding="utf-8") as f:
            if new:
                f.write("stage,model,input_tokens,output_tokens\n")
            f.write(f"{stage},{resp.model},{resp.usage.input_tokens},{resp.usage.output_tokens}\n")


def _cache_key(arxiv_id: str, model: str) -> str:
    return f"{arxiv_id}|{model}|{TAXONOMY_VERSION}"


def _read_cache() -> dict[str, dict]:
    if not CACHE.exists():
        return {}
    rows = [json.loads(l) for l in CACHE.read_text(encoding="utf-8").splitlines() if l.strip()]
    return {r["key"]: r for r in rows}


def classify_llm(df: pd.DataFrame, model: str = config.LLM_MODEL, batch_size: int = config.LLM_BATCH_SIZE) -> pd.DataFrame:
    cache = _read_cache()
    todo = df[~df["arxiv_id"].map(lambda i: _cache_key(i, model) in cache)]
    print(f"[llm] 캐시 {len(df) - len(todo)}건, 새로 분류 {len(todo)}건 (model={model})")

    if len(todo):
        llm = LLMClient(model)
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        for start in range(0, len(todo), batch_size):
            batch = todo.iloc[start:start + batch_size]
            papers = "\n\n".join(f"<paper id=\"{r.arxiv_id}\">\nTitle: {r.title}\nAbstract: {r.abstract}\n</paper>"
                                 for r in batch.itertuples())
            out = llm.ask_json(CLASSIFY_SYSTEM, f"Label these {len(batch)} papers.\n\n{papers}",
                               CLASSIFY_SCHEMA, stage="classify")
            got = {r["id"]: r for r in out["results"]}
            with CACHE.open("a", encoding="utf-8") as f:
                for pid in batch["arxiv_id"]:
                    if pid in got:  # 빠진 논문은 다음 실행 때 다시 요청된다
                        rec = {**got[pid], "id": pid, "key": _cache_key(pid, model)}
                        cache[rec["key"]] = rec
                        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            print(f"[llm] {min(start + batch_size, len(todo))}/{len(todo)}")

    rows = [cache.get(_cache_key(i, model)) for i in df["arxiv_id"]]
    return pd.DataFrame({
        "arxiv_id": df["arxiv_id"].values,
        "relevant": [str(r["relevant"]) if r else "" for r in rows],
        "topic": [r["topic"] if r else "" for r in rows],
        "method": [r["method"] if r else "" for r in rows],
        "summary_ko": [r["summary_ko"] if r else "" for r in rows],
    })


TOPIC_SYSTEM = """You write concise Korean research-trend briefs for a graduate seminar on financial machine learning.
You are given papers from ONE topic over several months, each with an id, month, title, and a one-line summary.
Write summary_ko: 3-4 Korean sentences describing the main research directions in this topic and how they shift over the months.
Only state things supported by the listed papers. Put the ids of 3-5 papers that best support your statements in evidence_ids."""


def summarize_topics(df: pd.DataFrame, labels: pd.DataFrame, model: str = config.LLM_MODEL,
                     max_papers: int = 80) -> pd.DataFrame:
    llm = LLMClient(model)
    if "relevant" in labels:
        labels = labels[labels["relevant"] != "False"]
    merged = df.merge(labels, on="arxiv_id")
    out = []
    for topic, g in merged.groupby("topic"):
        g = g.sort_values("published").tail(max_papers)
        lines = "\n".join(f"[{r.arxiv_id}] ({r.month}) {r.title} — {r.summary_ko}" for r in g.itertuples())
        res = llm.ask_json(TOPIC_SYSTEM, f"Topic: {TOPICS[topic]['name']} ({topic})\nPapers ({len(g)}):\n{lines}",
                           TOPIC_SUMMARY_SCHEMA, stage="topic_summary")
        valid = [i for i in res["evidence_ids"] if i in set(g["arxiv_id"])]  # 존재하는 논문만 근거로 인정
        out.append({"topic": topic, "summary_ko": res["summary_ko"], "evidence_ids": "; ".join(valid)})
        print(f"[llm] 주제 요약: {topic}")
    return pd.DataFrame(out)
