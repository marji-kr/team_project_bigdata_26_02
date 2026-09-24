# 금융 머신러닝 최신 논문 자동 수집·분석

빅데이터분석및이론 팀 프로젝트. 금융 ML 분야 최신 논문을 자동으로 수집해 `data/`에 저장하고,
키워드·방법론·금융 과제·유사도를 자동 분석해 리포트를 생성한다.

## 구조

```
team/
├── run_pipeline.py        # 수집 → 저장 → 분석 한 번에 실행
├── src/
│   ├── fetch_papers.py    # SerpAPI Google Scholar (1순위) / arXiv (대체) 메타데이터 수집
│   ├── pdf_fulltext.py    # PDF 다운로드, 본문 텍스트 추출, 섹션 분리
│   └── analyze_papers.py  # 본문 기반 키워드·태깅·데이터셋/지표 추출·요약·유사도, 그림, 리포트
├── data/
│   ├── pdfs/              # 논문 원문 PDF
│   ├── fulltext/          # PDF 에서 추출한 본문 텍스트
│   └── papers_raw.json, papers.csv, papers_analysis.csv, similarity_matrix.csv
├── figures/               # top_keywords.png, tag_distribution.png, similarity_heatmap.png
└── reports/analysis_report.md
```

## 실행

```bash
pip install -r requirements.txt
python run_pipeline.py                          # 최신 5편
python run_pipeline.py -n 10 -q "LLM stock prediction" --year-from 2026
python run_pipeline.py --no-pdf                 # PDF 없이 제목·초록만 분석
python run_pipeline.py --skip-fetch             # 저장된 데이터로 분석만
```

## SerpAPI 키 설정

[SerpAPI](https://serpapi.com/google-scholar-api)에서 발급받은 키를 `.env` 파일에 넣으면 Google Scholar에서 수집한다
(`.env`는 `.gitignore`에 포함되어 커밋되지 않음).

```
SERPAPI_KEY=여기에_키
```

키가 없거나 호출이 실패하면 arXiv 금융(q-fin) 카테고리 최신 논문 중 ML 관련 논문을 자동으로 가져온다.
Google Scholar 결과는 초록 대신 짧은 snippet만 주고, PDF 링크가 없거나 유료 논문이면 본문을 받지 못한다.
이 경우 해당 논문은 제목·snippet 으로만 분석된다.

## 분석 내용

| 항목 | 방법 |
|---|---|
| 분석 대상 텍스트 | PDF 본문(참고문헌 제외) + 제목·초록. PDF 가 없으면 제목·초록만 |
| 핵심 키워드 | TF-IDF (1–2gram), 논문별 상위 10개 + 전체 상위 15개 |
| 방법론/과제/데이터 태깅 | 정규식 사전 기반 (`TAXONOMY` 수정으로 확장 가능) |
| 데이터셋·평가지표 | 본문에서 S&P 500, CSI 300, CRSP… / Sharpe, IC, RMSE… 언급 횟수 집계 |
| 논문 구조 | 섹션 구성, 쪽수, 단어 수, 그림·표 개수 |
| 자동 요약 | 초록·결론 섹션에서 TF-IDF 점수 상위 문장 추출 |
| 논문 간 유사도 | TF-IDF 코사인 유사도 히트맵 |
