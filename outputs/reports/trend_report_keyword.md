# 금융 머신러닝 (Financial Machine Learning) 연구 동향 보고서

- 생성: 2026-10-12 05:33 · 분류 방식: **keyword**
- 데이터: arXiv API, 2026-03 ~ 2026-10 (8개월), 논문 544건
- 월별 비중은 LLM 이 아니라 코드로 계산 (해당 월 논문 수 대비 비율)

## 1. 월별 논문 수

![monthly counts](../figures/monthly_counts.png)

## 2. 주제별 월별 비중

![topic share](../figures/topic_share.png)

| 주제 | 논문 수 | 전체 비중 | 26-03 | 26-04 | 26-05 | 26-06 | 26-07 | 26-08 | 26-09 | 26-10 | 전반→후반 (%p) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 포트폴리오·자산배분 | 117 | 21.5% | 20% | 23% | 18% | 20% | 24% | 25% | 20% | 20% | +3.8 |
| 수익률·가격 예측 | 93 | 17.1% | 20% | 15% | 26% | 16% | 8% | 15% | 20% | 10% | -7.4 |
| 금융 텍스트·감성·대체데이터 | 89 | 16.4% | 11% | 17% | 16% | 15% | 22% | 17% | 20% | 20% | +4.8 |
| 트레이딩·시장 미시구조 | 48 | 8.8% | 8% | 3% | 7% | 11% | 12% | 10% | 10% | 20% | +3.4 |
| 신용·사기탐지·은행 | 41 | 7.5% | 12% | 5% | 8% | 9% | 3% | 9% | 10% | 0% | -2.5 |
| 기타 | 39 | 7.2% | 10% | 8% | 6% | 6% | 9% | 6% | 10% | 0% | -0.3 |
| 리스크·변동성 | 33 | 6.1% | 4% | 11% | 7% | 6% | 8% | 3% | 0% | 10% | -1.7 |
| 파생상품 가격결정·헤징 | 32 | 5.9% | 6% | 6% | 4% | 6% | 9% | 5% | 0% | 10% | +0.9 |
| 암호화폐·DeFi | 28 | 5.1% | 5% | 8% | 2% | 5% | 3% | 9% | 0% | 10% | +1.3 |
| 자산가격결정·팩터 | 18 | 3.3% | 4% | 6% | 3% | 4% | 1% | 2% | 10% | 0% | -2.1 |
| 거시경제·정책 | 6 | 1.1% | 1% | 0% | 3% | 0% | 1% | 1% | 0% | 0% | -0.2 |

> ⚠️ 논문이 30건 미만인 달은 비중이 크게 흔들리므로 해석에 주의: 2026-09 (10건), 2026-10 (10건)

## 3. 증가·감소 주제

**증가**: 금융 텍스트·감성·대체데이터 (+4.8%p, 기울기 +1.10%p/월), 포트폴리오·자산배분 (+3.8%p, 기울기 +0.10%p/월), 트레이딩·시장 미시구조 (+3.4%p, 기울기 +1.49%p/월)

**감소**: 수익률·가격 예측 (-7.4%p, 기울기 -1.05%p/월), 신용·사기탐지·은행 (-2.5%p, 기울기 -0.72%p/월), 자산가격결정·팩터 (-2.1%p, 기울기 -0.14%p/월)

## 4. 주제별 요약과 근거 논문

### 포트폴리오·자산배분 (117건)

근거 논문:
- (2026-09) [Propose, Don't Judge: An Anytime-Valid Referee for LLM Agents That Mine Investment Factors](http://arxiv.org/abs/2609.27051v1)
- (2026-10) [PreFER: Interactive Robo-Advisor with Scoring Mechanism](http://arxiv.org/abs/2610.03406v1)
- (2026-10) [MLP-Initialized Reinforcement Learning for Exit Timing in SPX Short-Straddle Portfolios](http://arxiv.org/abs/2610.13126v1)

### 수익률·가격 예측 (93건)

근거 논문:
- (2026-09) [The Informational Content in Lepto-Variance and Its Relation to Higher Moments](http://arxiv.org/abs/2609.25144v1)
- (2026-09) [EXAONE Demand 1.0: A Time Series Foundation Model for Demand Forecasting](http://arxiv.org/abs/2609.30880v1)
- (2026-10) [Large-Scale Benchmarking of Quantum Neural Network Configurations for Financial Time Series Forecasting](http://arxiv.org/abs/2610.12148v1)

### 금융 텍스트·감성·대체데이터 (89건)

근거 논문:
- (2026-09) [Same Text, Different Numbers: The Divergence of LLM-Based Measures](http://arxiv.org/abs/2609.31013v1)
- (2026-10) [Trading Strategy Optimization via Textual Gradient](http://arxiv.org/abs/2610.03128v1)
- (2026-10) [MintEval: Do LLMs Implement the Trading Strategy You Asked For? A Behavioural-Equivalence Benchmark for Natural-Language-to-Strategy Code](http://arxiv.org/abs/2610.03080v1)

### 트레이딩·시장 미시구조 (48건)

근거 논문:
- (2026-09) [Algorithmic trading and stochastic integration](http://arxiv.org/abs/2609.31578v1)
- (2026-10) [When a Correct Reward Is Not Enough: Diagnosing and Guiding PPO in an Analytically Solved Broker-Trader Game](http://arxiv.org/abs/2610.03598v1)
- (2026-10) [Market Impact Estimation via Causal Foundation Models](http://arxiv.org/abs/2610.12537v1)

### 신용·사기탐지·은행 (41건)

근거 논문:
- (2026-08) [A Temporal Multiplex Graph Neural Network for Systemic Risk Transmission in Global Banking](http://arxiv.org/abs/2608.27295v1)
- (2026-08) [Oculi: A Conversational Agentic Platform for Automated Credit Risk Analysis](http://arxiv.org/abs/2608.28944v1)
- (2026-09) [Financial Fragility in Societies of LLM Agents: Coordination Failures and Stabilizing Mechanisms](http://arxiv.org/abs/2609.30940v1)

### 기타 (39건)

근거 논문:
- (2026-08) [Spatially explicit feature importance for building height estimation using research-access high-resolution SAR and optical sensors](http://arxiv.org/abs/2608.17822v1)
- (2026-08) [PGFS++: Molecular Property Improvement under Synthesis and Diversity Constraints](http://arxiv.org/abs/2608.19121v1)
- (2026-09) [Bridging LLM Serving and CXL-SSDs with Chunk-Aware KV Cache Management](http://arxiv.org/abs/2609.26828v1)

### 리스크·변동성 (33건)

근거 논문:
- (2026-08) [Beyond Forecasting: Recasting Volatility Control as a Routing Problem](http://arxiv.org/abs/2608.10375v1)
- (2026-08) [Asymptotically-informed neural networks for Black-Scholes implied volatility computation](http://arxiv.org/abs/2609.05491v1)
- (2026-10) [A Distributional Framework for Behavioral Characterization and Risk Management of Large Language Models](http://arxiv.org/abs/2610.12718v1)

### 파생상품 가격결정·헤징 (32건)

근거 논문:
- (2026-08) [Deep Hedging Under Realistic Market Frictions: A Regime-Conditional Empirical Study of Dynamic Option Hedging on Bitcoin Options](http://arxiv.org/abs/2608.29025v1)
- (2026-08) [Neural Calibration of a Complete Market Model](http://arxiv.org/abs/2608.30867v1)
- (2026-10) [Shapley-based Structural Analysis of Neural Calibration for Stochastic Volatility Models](http://arxiv.org/abs/2610.03076v1)

### 암호화폐·DeFi (28건)

근거 논문:
- (2026-08) [Quality over Quantity: Semi-Supervised Detection of Illicit Bitcoin Flows via Feature Engineering](http://arxiv.org/abs/2609.27936v1)
- (2026-08) [An Open-Source, Event-Driven Pipeline for Cryptocurrency Market Data: Ingestion, Forecasting, and On-Chain Fraud Detection](http://arxiv.org/abs/2608.29973v1)
- (2026-10) [OnTrack: Real-Time Monitoring and Intervention in LLM Agent Trajectories via Streaming Structure-Aware Optimal Transport](http://arxiv.org/abs/2610.12375v1)

### 자산가격결정·팩터 (18건)

근거 논문:
- (2026-08) [Cross-Sectional Heterogeneity in LSTM Networks for Financial Time Series](http://arxiv.org/abs/2608.05755v2)
- (2026-08) [AlphaSeek: Trajectory-Level Self-Iterative Factor Mining Framework for Multi-Source Financial Data](http://arxiv.org/abs/2608.13913v1)
- (2026-09) [AlphaDiverse: Post-Training Local Quantitative Research Agents for Diverse Exploration in Alpha Factor Mining](http://arxiv.org/abs/2609.29014v1)

### 거시경제·정책 (6건)

근거 논문:
- (2026-05) [Deep Least Squares Monte Carlo methods for the valuation of variable annuities with guarantees](http://arxiv.org/abs/2605.27182v1)
- (2026-07) [Augmenting Fundamental Analysis with Large Language Models: A RAG-Based System for Generating Investor Briefs](http://arxiv.org/abs/2607.09121v1)
- (2026-08) [Can LLMs Take the Pulse of the Economy? A Real-Time Evaluation of LLM Nowcasts on Macroeconomic Indicators](http://arxiv.org/abs/2608.30110v1)

## 5. 방법론 비중 (보조)

![method share](../figures/method_share.png)

| 방법론 | 26-03 | 26-04 | 26-05 | 26-06 | 26-07 | 26-08 | 26-09 | 26-10 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 전통 ML(트리·선형·SVM) | 5% | 5% | 4% | 3% | 8% | 9% | 0% | 0% |
| 딥러닝 시계열(Transformer·RNN 등) | 30% | 29% | 26% | 19% | 30% | 17% | 10% | 30% |
| 생성모델(Diffusion·GAN·VAE) | 5% | 5% | 5% | 6% | 0% | 3% | 10% | 0% |
| 그래프 신경망 | 2% | 0% | 0% | 0% | 3% | 1% | 0% | 0% |
| LLM·생성형 에이전트 | 37% | 48% | 51% | 54% | 41% | 53% | 70% | 50% |
| 기타/통계·이론 | 14% | 6% | 8% | 6% | 7% | 10% | 10% | 0% |
| 강화학습 | 7% | 8% | 6% | 11% | 12% | 8% | 0% | 20% |
