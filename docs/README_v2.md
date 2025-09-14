# P1-System v2 – Overdrive-NS + LLM 共學版

## 概述
升級自 v1（p1-overdrive-ns）。v2 引入 LLM Reasoner、xLSTM、CTFG、Conformal、Learner/Trainer、FinGPT/FinRL，打造能模擬人類交易心理、又有精確數學風控的 100x 系統。

## 主要更新
- LLM Reasoner：僅在邊界單介入，輸出人類式 rationale 與 meta-tag。
- xLSTM：長序列記憶，低延遲，融合 TV/OF/Vision/On-chain。
- CTFG：12 節點因子圖，Loopy BP 統合多腦輸出。
- Conformal/Hazard：風險包線 + 變點退出。
- Learner/Trainer：IL + RL + RLHF；持續進化。
- FinGPT/FinRL：新聞情緒與離線 RL 訓練。

## 風險注意
- 100x No-Stop 僅在 Hazard/Conformal/Liq-Buffer 三重安全殼下運行。
- LLM 成本可用本地 FinGPT/LLaMA 降低；延遲受控（僅邊界單）。
- 蒐集 ≥100 筆人工標註交易以避免過擬合。

## TODO
- 串接 TradingView/YOLO → FeatureHub
- 建立 Likert-7 direction 標註與連續 dir_score
- 上線 Decision Pipeline + Gates
- 加入 FinGPT sentiment token
- FinRL 離線 RL 訓練 Exit/Position Sizing
