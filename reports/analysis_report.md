# 금융 머신러닝 최신 논문 자동 분석 리포트

- 생성 시각: 2026-09-24 14:54
- 논문 수: 5편 (출처: arxiv)
- 전체 상위 키워드: lepto-variance, sample, learning, language, stopping, framework, financial, portfolio, price, stock

## 1. 논문 목록

| # | 제목 | 게재일 | ML 방법론 | 금융 과제 |
|---|---|---|---|---|
| P1 | [Propose, Don't Judge: An Anytime-Valid Referee for LLM Agents That Mine Investment Factors](http://arxiv.org/abs/2609.27051v1) | 2026-09-22 | LLM / Foundation Model | Portfolio Optimization; Trading / Execution; Factor / Asset Pricing |
| P2 | [Hierarchical Multi-Task Learning with Liquidity-Aware Signals for Stock Forecasting](http://arxiv.org/abs/2609.25617v1) | 2026-09-22 | Deep Learning (general); Multi-task / Transfer | Return / Price Prediction; Portfolio Optimization; Trading / Execution; Risk / Volatility |
| P3 | [The Informational Content in Lepto-Variance and Its Relation to Higher Moments](http://arxiv.org/abs/2609.25144v1) | 2026-09-21 | Machine Learning (general) | Factor / Asset Pricing; Crypto |
| P4 | [Risk Measures under Paired-Ambiguity: A Deep Learning Reflected BSDE Framework](http://arxiv.org/abs/2609.23768v1) | 2026-09-20 | Deep Learning (general) | Risk / Volatility |
| P5 | [Financial Language Models as Applied Artificial Intelligence Systems for News-Based Trading under Market Frictions](http://arxiv.org/abs/2609.23703v1) | 2026-09-20 | LLM / Foundation Model | Return / Price Prediction; Portfolio Optimization; Trading / Execution |

## 2. 논문별 분석

### P1. Propose, Don't Judge: An Anytime-Valid Referee for LLM Agents That Mine Investment Factors

- **저자**: Bo Qu, Mingguang Chen, Licheng Wang
- **게재**: arXiv (2026-09-22)
- **ML 방법론**: LLM / Foundation Model
- **금융 과제**: Portfolio Optimization; Trading / Execution; Factor / Asset Pricing
- **데이터 유형**: Synthetic / Simulation
- **핵심 키워드**: referee, agent, factors, bandit, frozen, judge, time, investment factors
- **자동 요약**: The certificate's price is time: an admitted true factor waits about 500 trading days, and the certified portfolio's Sharpe ratio therefore trails an ungated one. Judging belongs to the procedure; proposing and instrument-making belong to the agent.

### P2. Hierarchical Multi-Task Learning with Liquidity-Aware Signals for Stock Forecasting

- **저자**: Hengyi Yang, Sida Lin, Yiyan Qi, Yankai Chen, Haohan Zhang, Xianhua Peng, Jian Guo
- **게재**: arXiv (2026-09-22)
- **ML 방법론**: Deep Learning (general); Multi-task / Transfer
- **금융 과제**: Return / Price Prediction; Portfolio Optimization; Trading / Execution; Risk / Volatility
- **데이터 유형**: Time Series
- **핵심 키워드**: multi-task, limt, temporal, forecasting, price, forecasts, dependencies, movement
- **자동 요약**: Building on this latent state, we introduce a Liquidity-Driven Learning (LDL) module, a mixture-of-experts architecture that features cross-task gating mechanisms to jointly predict price movement, volatility, and trading volume. In realistic CSI300 backtests, APO improves annualized return from 3.99% to 10.01% and Sharpe ratio from 1.22 to 1.86 over equal weighting, showing that the multi-task forecasts translate into deployable portfolio gains.

### P3. The Informational Content in Lepto-Variance and Its Relation to Higher Moments

- **저자**: Vassilis Polimenis
- **게재**: arXiv (2026-09-21)
- **ML 방법론**: Machine Learning (general)
- **금융 과제**: Factor / Asset Pricing; Crypto
- **데이터 유형**: Synthetic / Simulation
- **핵심 키워드**: sample, lepto-variance, variance, sample variance, lepto-ratio, correlated, normal, orthogonal sample
- **자동 요약**: It is a novel, model-free method potentially revealing information on important sample structure properties. Both lepto-variance and lepto-ratio are orthogonal to sample skew.

### P4. Risk Measures under Paired-Ambiguity: A Deep Learning Reflected BSDE Framework

- **저자**: Nacira Agram, Jan Rems, Emanuela Rosazza Gianin
- **게재**: arXiv (2026-09-20)
- **ML 방법론**: Deep Learning (general)
- **금융 과제**: Risk / Volatility
- **데이터 유형**: -
- **핵심 키워드**: risk, reflected, bsde, stopping, risk measures, quadratic, ambiguity, measures
- **자동 요약**: We introduce a paired ambiguity framework combining Girsanov model uncertainty with cash subadditive risk evaluation and characterize the stopping value by an upper reflected backward stochastic differential equation (BSDE). Numerical experiments for American options illustrate the effects of discount rate and entropic ambiguity on stopping values and exercise decisions.

### P5. Financial Language Models as Applied Artificial Intelligence Systems for News-Based Trading under Market Frictions

- **저자**: Kemal Kirtac
- **게재**: arXiv (2026-09-20)
- **ML 방법론**: LLM / Foundation Model
- **금융 과제**: Return / Price Prediction; Portfolio Optimization; Trading / Execution
- **데이터 유형**: Time Series; Text / News / Sentiment
- **핵심 키워드**: financial, text, language, financial language, news, deployment, calibration, diagnostics
- **자동 요약**: Computer science research has developed strong methods for time-series forecasting, text classification, multimodal stock prediction, graph-based market modeling, and machine-learning operations, yet these streams do not provide a domain-specific protocol that jointly tests financial language-model outputs under event-time observability, probability calibration, execution timing, transaction costs, liquidity constraints, capacity limits, operational diagnostics, and statistical inference. We introduce MFAST, a Market-Friction-Aware Sentiment-to-Trading framework that converts timestamped financial text into auditable, reproducible, and market-feasible trading decisions.

## 3. 교차 분석

![tags](../figures/tag_distribution.png)

![keywords](../figures/top_keywords.png)

![similarity](../figures/similarity_heatmap.png)

- 가장 유사한 논문 쌍: **P2 ↔ P5** (코사인 유사도 0.06)
