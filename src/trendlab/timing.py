"""자동화 단계의 소요 시간을 data/runs/timings.csv 에 누적 기록한다 (성공 기준: 시간 비교)."""
from __future__ import annotations

import csv
import time
from contextlib import contextmanager
from datetime import datetime

import config

FIELDS = ["timestamp", "stage", "approach", "seconds", "n_papers", "note"]


def log_time(stage: str, approach: str, seconds: float, n_papers: int | None = None, note: str = "") -> None:
    config.RUNS_DIR.mkdir(parents=True, exist_ok=True)
    path = config.RUNS_DIR / "timings.csv"
    new = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new:
            w.writeheader()
        w.writerow({"timestamp": datetime.now().isoformat(timespec="seconds"), "stage": stage,
                    "approach": approach, "seconds": round(seconds, 2), "n_papers": n_papers, "note": note})


@contextmanager
def timed(stage: str, approach: str, n_papers: int | None = None, note: str = ""):
    start = time.perf_counter()
    yield
    elapsed = time.perf_counter() - start
    log_time(stage, approach, elapsed, n_papers, note)
    print(f"[time] {stage} ({approach}): {elapsed:.1f}s")
