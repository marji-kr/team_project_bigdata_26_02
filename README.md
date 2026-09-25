# LLM 기반 금융 ML 논문 트렌드 자동 분석 (팀 JKLS)

빅데이터분석및이론(AMA8039) 팀 프로젝트. 문제정의서(3주차)를 그대로 구현한 코드다.

> **연구 질문** — 관심 분야의 최근 논문을 LLM 으로 주제별 분류·요약하고 월별 주제 비중 변화를 제시하면,
> 사람이 직접 논문을 읽고 정리하는 방식보다 주요 연구 동향을 파악하는 시간을 줄일 수 있는가?

| 문제정의서 | 이 코드에서 |
|---|---|
| 관심 분야 1개 | 금융 머신러닝 (`config.py` 의 `FIELD_NAME`, `ARXIV_QUERIES`) |
| 기준일 직전 6개월, 500~1000건, 제목·초록·발표일·DOI/URL | arXiv API 월별 수집 → 현재 **524건** (2026-03 ~ 2026-08) |
| Scholar 는 일괄 수집 불가 → 대체 후보 arXiv API | `src/trendlab/collect.py` |
| DOI/제목 기준 중복 제거 → 초록·날짜 누락 확인 → 월별 집계 | `src/trendlab/clean.py` → `data/processed/cleaning_log.json` |
| LLM 으로 유사 주제 묶기·요약 | `src/trendlab/classify_llm.py` (Claude API) |
| 논문 수·월별 비중은 코드로 계산 | `src/trendlab/trends.py` |
| 키워드 기반 분류와 비교 | `src/trendlab/classify_keyword.py` (베이스라인) |
| 평가용 약 100건, 수작업 vs AI, 시간 30% 이상 단축 | `src/trendlab/evaluate.py` → `outputs/reports/evaluation_report.md` |
| 근거 논문 링크가 포함된 트렌드 | `outputs/reports/trend_report_*.md` |

## 전체 흐름

```
collect ─▶ clean ─▶ classify keyword ─┐
                   └▶ classify llm ───┼▶ report (월별 비중·증감·주제별 요약+근거 링크)
                        └▶ summarize ─┘
eval-sample ─▶ (사람이 100건 라벨링 + 시간 기록) ─▶ evaluate (정확도 + 시간 단축률)
```

## 폴더 구조

```
team/
├── .github/workflows/weekly.yml  # 매주 자동 업데이트 (GitHub Actions)
├── run.py                  # 실행 진입점 (명령어 목록은 python run.py -h)
├── config.py               # 분야·검색식·기간·상한·모델·성공 기준 등 설정
├── src/trendlab/
│   ├── collect.py          # arXiv API 월별 수집
│   ├── clean.py            # 누락 확인·중복 제거·관련성 필터·월 컬럼
│   ├── taxonomy.py         # 주제 11개·방법론 7개 정의 (모든 분류 방식이 공유)
│   ├── classify_keyword.py # 베이스라인: 정규식 키워드 분류
│   ├── classify_llm.py     # Claude API 분류(+관련성 판정, 한 줄 요약)·주제별 동향 요약
│   ├── trends.py           # 월별 논문 수·비중·전반→후반 변화·기울기
│   ├── evaluate.py         # 평가 샘플 생성, 정확도·κ·시간 단축률
│   ├── report.py           # 그림 + 마크다운 보고서
│   └── timing.py           # 자동 단계 소요 시간 기록
├── data/
│   ├── raw/                # arXiv 원본 (월별 JSON)
│   ├── processed/          # papers.csv, labels_*.csv, monthly_*.csv, trend_table_*.csv
│   ├── eval/               # eval_sample.csv (수작업 라벨), manual_timing.csv (수작업 시간)
│   └── runs/               # timings.csv (자동 단계 시간), llm_usage.csv (토큰), weekly_log.csv (주간 추가 기록)
└── outputs/
    ├── figures/            # monthly_counts.png, topic_share.png, method_share.png
    └── reports/            # trend_report_keyword.md, trend_report_llm.md, evaluation_report.md
```

## 설치

```bash
pip install -r requirements.txt
```

## LLM(Claude API) 키 설정

[Claude Console](https://console.anthropic.com) 에서 API 키를 발급받아 `team` 폴더에 `.env` 파일을 만든다.
`.env` 는 `.gitignore` 에 있어 GitHub 에 올라가지 않는다. **키는 팀원끼리도 채팅에 붙여넣지 말 것.**

```
ANTHROPIC_API_KEY=sk-ant-...
```

- 기본 모델은 `claude-opus-5`, 분류는 effort `low`. 바꾸려면 `config.py` 의 `LLM_MODEL` 또는 `--model`.
- 모델이 요청을 거절하면 서버측 fallback(`fallbacks: "default"`)이 다른 모델로 자동 재시도한다.
- 한 번 분류한 논문은 `data/processed/llm_cache.jsonl` 에 캐시되어 다시 돌려도 비용이 들지 않는다.
- 토큰 사용량은 `data/runs/llm_usage.csv` 에 쌓인다.

## 실행

### 한 번에 전부

```bash
python run.py all            # 키가 있으면 LLM 까지, 없으면 키워드 분류로만 보고서
python run.py all --no-llm   # LLM 없이
```

### 단계별

```bash
python run.py collect --reference-date 2026-09-24   # 1. 기준일 직전 6개월 수집 (약 1분)
python run.py clean                                 # 2. 정제
python run.py classify keyword                      # 3a. 키워드 베이스라인
python run.py classify llm                          # 3b. LLM 분류 (524건 ≈ 27회 요청)
python run.py summarize                             # 4. 주제별 동향 요약 (LLM)
python run.py report                                # 5. 동향 보고서 (llm 라벨이 있으면 llm 기준)
python run.py report --approach keyword             #    키워드 기준 보고서
```

### 주간 업데이트 (매주 새 논문 5편 추가)

```bash
python run.py weekly          # 기존 데이터에 없는 최신 논문 5편 추가 → 분류 → 보고서 갱신
python run.py weekly --n 10   # 개수 변경
```

- 추가된 논문 원본은 `data/raw/weekly_날짜.json`, 기록은 `data/runs/weekly_log.csv` 에 쌓인다.
- `python run.py all` 로 처음부터 다시 수집해도 주간 추가분은 유지된다.
- **자동 실행**: GitHub Actions(`.github/workflows/weekly.yml`)가 매주 월요일 09:00(KST)에 실행하고 결과를 저장소에 커밋한다.
  컴퓨터가 꺼져 있어도 된다. 내 드라이브 폴더에 반영하려면 `git pull`.
  - 수동 실행: GitHub 저장소 → Actions → Weekly paper update → Run workflow
  - LLM 분류까지 자동으로 하려면: Settings → Secrets and variables → Actions → `ANTHROPIC_API_KEY` 등록
    (없으면 키워드 분류로만 갱신)

### 성공 기준 평가 (문제정의서 4절)

```bash
python run.py eval-sample              # 1) 월별 층화 추출 100건 + 기록 양식 생성
python run.py classify llm --eval-only # 2) (비용 절약) 100건만 LLM 분류
python run.py evaluate                 # 4) 평가 보고서
```

3) 사이에 사람이 할 일:

1. `data/eval/eval_sample.csv` 를 엑셀로 열어 **manual_topic, manual_method** 칸을 채운다.
   가능한 값은 `src/trendlab/taxonomy.py` 의 키 (`forecasting`, `portfolio`, … / `llm`, `deep_seq`, …).
   AI 결과를 보지 않은 상태에서 라벨링해야 비교가 공정하다.
2. `data/eval/manual_timing.csv` 의 **minutes** 칸에 걸린 시간(분)을 적는다.
   - `manual`: 사람이 검색·수집 → 100건 읽고 분류 → 같은 형식의 보고서 작성에 걸린 시간
   - `ai_review`: AI 가 만든 라벨·보고서를 사람이 검토·수정한 시간

`evaluate` 는 다음을 계산한다.

| 지표 | 계산 |
|---|---|
| 시간 단축률 (주 지표) | 1 − (AI 자동 실행 시간 + 사람 검토 시간) / 수작업 시간, 목표 ≥ 30% |
| 분류 품질 | 수작업 라벨 대비 정확도, Macro-F1, Cohen's κ (키워드 vs LLM) |
| 참고 | 전체 논문에서 키워드·LLM 분류 일치율 |

AI 쪽 시간에 사람 검토 시간을 포함하는 이유: 자동 실행 시간만 비교하면 AI 에 유리하게 편향되므로.

## 분석 결과 보기

- `outputs/reports/trend_report_llm.md` (또는 `_keyword.md`) — 월별 비중 표, 증가·감소 주제, 주제별 요약과 근거 논문 링크
- `outputs/reports/evaluation_report.md` — 성공 기준 달성 여부
- VS Code 에서 `.md` 파일을 열고 `Ctrl+Shift+V` 로 그림과 함께 볼 수 있다.

## 설정 바꾸기 (`config.py`)

| 항목 | 기본값 | 설명 |
|---|---|---|
| `WINDOW_MONTHS` | 6 | 기준일 직전 몇 개월 (완결된 달만) |
| `REFERENCE_DATE` | None(오늘) | 재현하려면 날짜 고정 |
| `ARXIV_QUERIES` | q-fin×ML, cs×금융 | 분야를 바꾸려면 여기 |
| `MAX_PAPERS` | 1000 | 넘으면 월별 비율 유지 무작위 추출 |
| `LLM_MODEL` / `LLM_BATCH_SIZE` / `LLM_EFFORT` | claude-opus-5 / 20 / low | LLM 설정 |
| `TARGET_TIME_REDUCTION` | 0.30 | 성공 기준 |

주제 정의를 바꾸면 `taxonomy.py` 의 `TAXONOMY_VERSION` 을 올려야 LLM 캐시가 새로 만들어진다.

## 한계 (보고서 작성 시 참고)

- arXiv 는 프리프린트만 포함 → 저널 논문 동향과 다를 수 있다. Scholar 알림 병행은 미정.
- 1차 관련성 필터는 키워드라 무관한 논문이 일부 섞인다. LLM 분류가 `relevant=false` 로 판정한 논문은 LLM 보고서의 비중 계산에서 빠진다.
- 월별 논문 수가 66~105건이라 작은 주제의 월별 비중은 변동이 크다 → 전반·후반 비교와 기울기를 함께 본다.
- 논문 PDF 원문은 저작권 때문에 저장소에 포함하지 않는다.
