# 금융 머신러닝 최신 논문 자동 수집·분석

빅데이터분석및이론 팀 프로젝트. 금융 ML 분야 최신 논문을 자동으로 수집해 `data/`에 저장하고,
키워드·방법론·금융 과제·유사도를 자동 분석해 리포트를 생성한다.

## 구조

```
team/
├── run_pipeline.py        # 수집 → 저장 → 분석 한 번에 실행
├── src/
│   ├── fetch_papers.py    # SerpAPI Google Scholar (1순위) / arXiv (대체) 수집
│   └── analyze_papers.py  # TF-IDF 키워드, 태깅, 추출 요약, 유사도, 그림, 리포트
├── data/                  # papers_raw.json, papers.csv, papers_analysis.csv, similarity_matrix.csv
├── figures/               # top_keywords.png, tag_distribution.png, similarity_heatmap.png
└── reports/analysis_report.md
```

## 실행

```bash
pip install -r requirements.txt
python run_pipeline.py                          # 최신 5편
python run_pipeline.py -n 10 -q "LLM stock prediction" --year-from 2026
python run_pipeline.py --skip-fetch             # 저장된 데이터로 분석만
```

## SerpAPI 키 설정

[SerpAPI](https://serpapi.com/google-scholar-api)에서 발급받은 키를 `.env` 파일에 넣으면 Google Scholar에서 수집한다
(`.env`는 `.gitignore`에 포함되어 커밋되지 않음).

```
SERPAPI_KEY=여기에_키
```

키가 없거나 호출이 실패하면 arXiv 금융(q-fin) 카테고리 최신 논문 중 ML 관련 논문을 자동으로 가져온다.
Google Scholar 결과는 초록 대신 짧은 snippet만 제공하므로 arXiv 쪽이 요약·키워드 분석 품질은 더 좋다.

## 분석 내용

| 항목 | 방법 |
|---|---|
| 핵심 키워드 | TF-IDF (1–2gram), 논문별 상위 8개 + 전체 상위 15개 |
| 방법론/과제/데이터 태깅 | 정규식 사전 기반 (`TAXONOMY` 수정으로 확장 가능) |
| 자동 요약 | 문장별 TF-IDF 점수 상위 2문장 추출 |
| 논문 간 유사도 | TF-IDF 코사인 유사도 히트맵 |
