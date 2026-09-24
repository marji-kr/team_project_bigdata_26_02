"""논문 수집 → 저장 → 자동 분석을 한 번에 실행한다.

사용법:
    python run_pipeline.py                 # 최신 논문 5편
    python run_pipeline.py -n 10 -q "LLM stock prediction"
    python run_pipeline.py --skip-fetch    # 저장된 data/papers.csv 로 분석만
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from analyze_papers import analyze  # noqa: E402
from fetch_papers import DEFAULT_QUERY, fetch_papers, save_papers  # noqa: E402

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="금융 ML 최신 논문 수집·분석 파이프라인")
    p.add_argument("-n", "--num", type=int, default=5, help="수집할 논문 수")
    p.add_argument("-q", "--query", default=DEFAULT_QUERY, help="Google Scholar 검색어 (SerpAPI 사용 시)")
    p.add_argument("--year-from", type=int, default=None, help="이 연도 이후 논문만 (기본: 작년)")
    p.add_argument("--skip-fetch", action="store_true", help="수집 없이 분석만 실행")
    args = p.parse_args()

    if not args.skip_fetch:
        save_papers(fetch_papers(args.num, args.query, args.year_from), ROOT / "data")
    analyze(ROOT)
