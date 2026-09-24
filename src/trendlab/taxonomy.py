"""분류 체계. LLM 분류·키워드 분류·수작업 라벨이 모두 같은 라벨을 쓴다.

- topic : 논문이 다루는 금융 문제 (월별 비중 = 트렌드 분석 대상)
- method: 주로 쓰는 ML 방법론 (보조 분석)
keywords 는 키워드 기반 베이스라인이 쓰는 정규식이다.
"""

TOPICS = {
    "forecasting": {
        "name": "수익률·가격 예측",
        "desc": "Stock/asset return, price, or movement prediction; financial time-series forecasting.",
        "keywords": r"forecast|predict(ion|ing)? (of )?(stock|price|return|movement)|stock (price|return|movement)|price prediction|return prediction|time[- ]series",
    },
    "portfolio": {
        "name": "포트폴리오·자산배분",
        "desc": "Portfolio construction/optimization, asset allocation, robo-advisory, index tracking.",
        "keywords": r"portfolio|asset allocation|mean-variance|robo-advis|index tracking|rebalanc",
    },
    "trading": {
        "name": "트레이딩·시장 미시구조",
        "desc": "Trading strategies and agents, order execution, market making, limit order books, high-frequency data.",
        "keywords": r"trading (strateg|agent|system)|algorithmic trading|quantitative trading|execution|market[- ]making|order book|high[- ]frequency|microstructure",
    },
    "risk": {
        "name": "리스크·변동성",
        "desc": "Volatility modeling/forecasting, VaR/ES, tail and systemic risk, stress testing.",
        "keywords": r"volatility|value[- ]at[- ]risk|expected shortfall|tail risk|systemic risk|stress test|risk measure|risk management",
    },
    "derivatives": {
        "name": "파생상품 가격결정·헤징",
        "desc": "Option/derivative pricing, deep hedging, implied volatility surfaces, calibration, stochastic models (SDE/BSDE).",
        "keywords": r"option pric|derivative|deep hedging|hedg|implied volatility|calibrat|bsde|stochastic volatility",
    },
    "asset_pricing": {
        "name": "자산가격결정·팩터",
        "desc": "Asset pricing models, factor discovery/mining, cross-section of returns, anomalies, alpha.",
        "keywords": r"asset pricing|factor (model|mining|zoo|investing)|alpha factor|cross[- ]section|anomal(y|ies)|risk premi|stochastic discount",
    },
    "credit_fraud": {
        "name": "신용·사기탐지·은행",
        "desc": "Credit scoring, default/bankruptcy prediction, lending, fraud and AML detection, banking operations.",
        "keywords": r"credit|default|bankrupt|loan|lending|fraud|money laundering|\baml\b|bank",
    },
    "crypto": {
        "name": "암호화폐·DeFi",
        "desc": "Cryptocurrencies, blockchain, DeFi, tokens.",
        "keywords": r"crypto|bitcoin|ethereum|blockchain|defi\b|decentralized finance|token",
    },
    "text_altdata": {
        "name": "금융 텍스트·감성·대체데이터",
        "desc": "Financial NLP: news/social-media sentiment, filings and earnings calls, financial QA/benchmarks, alternative data.",
        "keywords": r"sentiment|news|social media|earnings call|10-k|filings|financial (nlp|text|question|report)|textual|alternative data|benchmark",
    },
    "macro_econ": {
        "name": "거시경제·정책",
        "desc": "Macroeconomic forecasting, monetary policy, inflation, economic indicators, nowcasting.",
        "keywords": r"macroeconom|inflation|monetary policy|central bank|gdp|nowcast|interest rate|economic indicator",
    },
    "other": {
        "name": "기타",
        "desc": "Finance-related but none of the above (e.g., insurance, ESG, regulation), or not clearly finance+ML.",
        "keywords": r"$^",
    },
}

METHODS = {
    "llm": {"name": "LLM·생성형 에이전트", "desc": "Large language models, LLM agents, prompting, fine-tuned LMs, RAG.",
            "keywords": r"\bllms?\b|large language model|language model|gpt|agentic|\bagents?\b|retrieval-augmented|\brag\b|prompt"},
    "deep_seq": {"name": "딥러닝 시계열(Transformer·RNN 등)", "desc": "Transformers, LSTM/GRU, TCN, attention, other deep sequence/tabular nets.",
                 "keywords": r"transformer|attention|lstm|gru\b|recurrent|temporal convolution|mamba|deep learning|neural network"},
    "rl": {"name": "강화학습", "desc": "Reinforcement learning, bandits, deep RL agents.",
           "keywords": r"reinforcement learning|q-learning|policy gradient|actor-critic|bandit|\bdrl\b"},
    "graph": {"name": "그래프 신경망", "desc": "Graph neural networks, knowledge graphs, network models.",
              "keywords": r"graph neural|\bgnns?\b|graph convolution|knowledge graph|graph attention"},
    "generative": {"name": "생성모델(Diffusion·GAN·VAE)", "desc": "Diffusion models, GANs, VAEs, normalizing flows, synthetic data generation.",
                   "keywords": r"diffusion model|\bgans?\b|generative adversarial|variational autoencoder|\bvaes?\b|normalizing flow|synthetic data"},
    "classical_ml": {"name": "전통 ML(트리·선형·SVM)", "desc": "Gradient boosting, random forests, SVM, penalized regression, clustering.",
                     "keywords": r"xgboost|lightgbm|catboost|gradient boost|random forest|support vector|\bsvm\b|lasso|ridge|clustering|k-means"},
    "other": {"name": "기타/통계·이론", "desc": "Mainly statistical/econometric/theoretical methods, or other ML.", "keywords": r"$^"},
}

TOPIC_IDS = list(TOPICS)
METHOD_IDS = list(METHODS)
TAXONOMY_VERSION = "v1"   # 라벨 정의를 바꾸면 올릴 것 (LLM 캐시가 무효화됨)
