"""프로젝트 설정. 문제정의서(3주차) 기준값이며, 팀 합의에 따라 여기만 고치면 된다."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
RAW_DIR = DATA / "raw"              # API 원본 응답
PROCESSED_DIR = DATA / "processed"  # 정제·분류·집계 결과
EVAL_DIR = DATA / "eval"            # 평가용 100건 + 수작업 라벨 + 소요 시간 기록
RUNS_DIR = DATA / "runs"            # 자동 단계 소요 시간 로그
FIG_DIR = ROOT / "outputs" / "figures"
REPORT_DIR = ROOT / "outputs" / "reports"

# ── 3. 데이터 ─────────────────────────────────────────────
FIELD_NAME = "금융 머신러닝 (Financial Machine Learning)"
WINDOW_MONTHS = 6          # 수집 기준일 직전 6개월 (완결된 달만 사용)
REFERENCE_DATE = None      # None 이면 오늘. 재현하려면 "2026-09-24" 처럼 고정
MAX_PAPERS = 1000          # 상한. 넘으면 월별 비율을 유지한 채 무작위 추출
RANDOM_SEED = 42

# arXiv 검색식 (괄호로 우선순위를 반드시 묶는다)
QFIN_CATS = "cat:q-fin.CP OR cat:q-fin.PM OR cat:q-fin.ST OR cat:q-fin.TR OR cat:q-fin.RM OR cat:q-fin.MF OR cat:q-fin.GN OR cat:q-fin.PR"
CS_CATS = "cat:cs.LG OR cat:cs.AI OR cat:cs.CL OR cat:stat.ML OR cat:cs.CE"
ML_TERMS = ('abs:"machine learning" OR abs:"deep learning" OR abs:"neural network" OR abs:"language model" '
            'OR abs:"reinforcement learning" OR abs:transformer OR abs:LLM')
FIN_TERMS = ('abs:"stock" OR abs:"portfolio" OR abs:"asset pricing" OR abs:"financial market" '
             'OR abs:"quantitative trading" OR abs:"algorithmic trading" OR abs:"credit risk" '
             'OR abs:"cryptocurrency" OR abs:"option pricing" OR abs:"financial time series"')
ARXIV_QUERIES = {
    "qfin_x_ml": f"({QFIN_CATS}) AND ({ML_TERMS})",   # 금융 분야 논문 중 ML 사용
    "ml_x_fin": f"({CS_CATS}) AND ({FIN_TERMS})",     # ML 분야 논문 중 금융 응용
}

# ── 2. LLM (Claude API) ──────────────────────────────────
LLM_MODEL = "claude-opus-5"
LLM_BATCH_SIZE = 20        # 요청 1회에 분류할 논문 수
LLM_EFFORT = "low"         # 분류 작업은 low 로 충분 (비용·시간 절감)

# ── 4. 성공 기준 ──────────────────────────────────────────
EVAL_SAMPLE_SIZE = 100
TARGET_TIME_REDUCTION = 0.30   # 수작업 대비 30% 이상 시간 단축
