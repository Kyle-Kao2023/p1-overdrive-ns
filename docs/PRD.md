# P1-system Overdrive-NS（100x、No-Stop、精準度優先）— PRD

## 1. 產品宗旨

在 100x 槓桿與不預掛止損（No-Stop）前提下，只在高勝率 A+ 段落出手：
四道 Gate（Vol / Consensus / Liq-Buffer / Event&Latency）＋ Decision Agent 鏈式推理＋ MPC & Hazard 動態退出。
與你的日常工作流對齊：TradingView 指標＋YOLO 圖像形態＋Orderflow＋OI/Gas。

## 2. 功能與服務

### 2.1 Decision Service（FastAPI）

- **`/decide/enter`**：輸入 Features + PGM 指標 → 回傳 Allow/Deny、side、alloc、exec、reason_chain。
- **`/decide/exit`**：輸入持倉與即時更新 → 回傳 reduce%/close/trail。
- **`/health`, `/version`**：運維。

### 2.2 FeatureHub（FastAPI）

接收 TradingView Pine webhook、截圖→YOLO tokens、WS/OI/Gas，輸出標準化快照。
本版為 stub，可先用假資料打通流程。

### 2.3 Vision（FastAPI）

圖像→tokens（stub），生成 C_vision 與 bbox overlays。

### 2.4 Adapters

- **Freqtrade ExternalDecisionStrategy**：策略內呼叫 Decision API。
- **Vedanta adapters**：把其回測/線上殼改外部決策模式。

## 3. 決策流程（Mermaid）

```mermaid
flowchart TD
  IN[Features: TV/Pine, YOLO tokens, HTF/LTF, OF, OI/Gas, σ&skew, Market] --> F[CTFG/xLSTM→P(hit),Q(MAE),Q(Slip),T_hit]
  F --> G1[Vol Gate]
  F --> G2[Consensus Gate]
  F --> G3[Liq-Buffer Gate]
  IN --> G4[Event & Latency Gate]
  G1 & G2 & G3 & G4 --> DA[Decision Agent<br/>證據鏈/反事實/行動]
  DA --> EN[Enter Response]
  EN --> EX[Exec(Freqtrade/Vedanta)]
  EX --> SAF[持倉 → Hazard h(t) & MPC Exit]
  SAF --> XR[Exit Response]
```

## 4. Gate 規格

### 4.1 Vol Sweet-Spot Gate

- **Bullish**：σ_1m ∈ [0.0012,0.0022] 且 skew>+0.5
- **Bearish**：σ_1m ∈ [0.0015,0.0028] 且 skew<−0.5
- **|skew|<0.3** → 拒單。
- **σ_1m** = std(logret_1m, win=5)；**skew_1m** = skew(logret_1m, win=20)。

### 4.2 Consensus Gate

- **C_align ≥ 0.85**（Z_4H/Z_1H/Z_15m 一致）
- **C_of ≥ 0.80**（OBI/ΔCVD/補單率 統合）
- **C_vision ≥ 0.75**（YOLO/DETR tokens → 方向分）
- **Pine_match = true**（TradingView 指標同向）

### 4.3 Liq-Buffer Gate

**LiqBuffer** = |Mark−LiqPrice| / Mark

**放行**：Q0.999(MAE) + Q0.95(Slip) + ε ≤ LiqBuffer（ε=0.0005）

### 4.4 Event & Latency Gate

- 黑名單事件窗禁止新倉；端到端決策→保護 p95 ≤ 70ms。

## 5. Decision Agent（鏈式推理）

1. **先驗拒單**（Event/Latency/Vol）。
2. **多假說**：H_long / H_short / H_wait。
3. **證據鏈**：TV、YOLO、HTF/LTF、OF、OI/Gas 支持/反證。
4. **融合**：CTFG → P(hit)；xLSTM → Q(MAE)/Q(Slip)/T_hit；Conformal 校準。
5. **邊界**：Liq-Buffer 檢核。
6. **脆弱性**：拔最強因子/擾動 σ/深度/OF，不可翻盤。
7. **行動**：允許/拒絕、side、alloc、exec；輸出 reason_chain。

## 6. 資料契約（Pydantic 結構）

### 6.1 EnterRequest

```json
{
  "symbol":"ETHUSDT","side_hint":"short","ts":"2025-09-14T10:25:00Z","tf":"15m",
  "features":{
    "sigma_1m":0.0018,"skew_1m":-0.72,
    "Z_4H":-0.9,"Z_1H":-0.7,"Z_15m":-0.6,
    "C_align":0.88,"C_of":0.83,"C_vision":0.79,"pine_match":true,
    "OF":{"obi":0.31,"dCVD":-1.2,"replenish":0.67},
    "vision_tokens":{"bear_engulfing":0.82,"long_upper_wick":0.74},
    "onchain":{"oi_roc":0.08,"gas_z":1.1},
    "market":{"mark":2415.3,"liq_price":2458.8,"spread_bp":3,"depth_px":1200000}
  },
  "pgm":{"p_hit":0.79,"mae_q999":0.0058,"slip_q95":0.0004,"t_hit_q50_bars":6,
          "factors":[["Z4H//Z15m",0.21],["OF_triad",0.18],["OI_ROC//GasZ",0.12],["Event_H",-0.05]]}
}
```

### 6.2 EnterResponse

```json
{
  "allow":true,"side":"short","alloc_equity_pct":0.8,
  "exec":{"type":"post_only_limit_or_mpo","reduce_only_fallback":true},
  "risk":{"liq_buffer_pct":0.0180,"lhs_pct":0.0065},
  "reason_chain":[ "C_align=0.88","C_of=0.83","C_vision=0.79","p_hit=0.79/T50=6",
                   "MAE+Slip+ε ≤ LiqBuffer","Fragility OK" ],
  "runtime_ms":55
}
```

### 6.3 ExitRequest / ExitResponse

```json
{
  "position":{"avg_entry":2415.0,"side":"short","qty":120,"upl_pct":0.42},
  "updates":{"p_hit":0.46,"mae_q90":0.0035,"t_hit_q50_bars":12,"h_t":0.37,"dCVD":0.9,"replenish":0.25}
}
```

```json
{"action":"reduce_or_close","reduce_pct":0.5,"reason":["hazard>0.3","of_flip","timeout_risk"],"runtime_ms":39}
```

## 7. KPI（於 σ-band 條件下）

- **Precision@Entry**（MAE ≤0.6%）≥ 95%
- **Hit@1%** ≥ 75%
- **拒單品質** ≥ 60%（拒後 30–60 分內反向 ≥1%）
- **Conformal 覆蓋誤差** ≤ 5%（rolling）
- **p95 決策→保護** ≤ 70ms
- **日內** ≤ 6 筆；只在浮盈中加倉；黑名單窗禁開新倉

## 8. 測試計畫

### 8.1 單元測試

- **Gate 邏輯**：`tests/test_gates.py`
  - Vol Gate: bull/bear 甜蜜點通過/拒絕
  - Consensus Gate: C_align/C_of/C_vision/Pine 閾值測試
  - Liq-Buffer Gate: 風險預算 vs LiqBuffer 邊界測試
  - Event & Latency Gate: 黑名單事件與延遲 SLA 測試

- **Hazard/MPC**：`tests/test_hazard_and_mpc.py`
  - BOCPD regime shift 檢測
  - MPC 退出策略：hold/reduce/close/trail 觸發條件
  - 場景模擬：normal/high_hazard/critical 情境

- **Decision API**：`tests/test_decision_api.py`
  - 入場決策：bull/bear 允許，vol/p_hit 拒絕場景
  - 退出決策：hazard/p_hit/orderflow 觸發測試
  - 性能測試：< 70ms 延遲 SLA
  - 推理鏈品質：包含關鍵指標與完整邏輯

### 8.2 回放測試

以 FeatureHub stub 產生 bull/bear/neutral 三組快照，確認 allow/deny 與理由。

### 8.3 故障注入

spread、depth、延遲、LiqBuffer 接近值 → 應拒單或降級只出場。

## 9. 風險與注意事項

### 9.1 No-Stop 風險

務必嚴守 Liq-Buffer Gate 與 Hazard/MPC；黑名單事件必須生效。

### 9.2 資料正確性

YOLO/TV/Pine 若不一致 → 拒單；審核面板與回寫標註閉環要打通。

### 9.3 授權

本專案 MIT；若接 Vedanta (GPL-3.0)，請以微服務隔離，不混源碼。

### 9.4 API 超時

Decision API 超時 > 70ms → 停新倉、僅出場。

## 10. 後續擴充（占位）

- **CTFG 真實 Loopy-BP**、**xLSTM/TFT 真模型**、**Conformal 真實校準**
- **Binance WS/Bybit** 執行細節（post-only/reduce-only/IOC）
- **TradingView 截圖 headless**、**YOLO/DETR 真檢測**
- **Chroma 記憶**（模仿學習樣本）
- **Gym-CDA 沙盒**接線與延遲/清算/手續費/對抗代理

## 11. 快速開始

```bash
# 開發
pip install -r requirements.txt
./scripts/run_dev.sh

# Docker
docker-compose up --build

# 打開 API
open http://localhost:8000/docs
```

## 12. 系統架構圖

```
                    ┌─────────────────────────────────────────┐
                    │            P1 Overdrive-NS             │
                    │         100x No-Stop System            │
                    └─────────────────────────────────────────┘
                                         │
              ┌──────────────────────────┼──────────────────────────┐
              │                          │                          │
    ┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
    │   FeatureHub    │       │  Decision Core  │       │   Vision YOLO   │
    │   Port: 8010    │       │   Port: 8000    │       │   Port: 8020    │
    │                 │       │                 │       │                 │
    │ • TradingView   │◄──────│ • Vol Gate      │──────►│ • Pattern Detect│
    │ • OrderFlow     │       │ • Consensus Gate│       │ • C_vision Gen  │
    │ • OnChain Data  │       │ • Liq-Buffer    │       │ • Confidence    │
    │ • Market Snapshot│       │ • Event/Latency │       │ • Bbox Overlay  │
    │                 │       │                 │       │                 │
    │ Pine Webhook    │       │ CTFG Engine     │       │ DETR Tokens     │
    │ WS Connectors   │       │ MPC Exit        │       │ Form Recognition│
    │ Screenshot API  │       │ Hazard Detection│       │                 │
    └─────────────────┘       └─────────────────┘       └─────────────────┘
              │                          │                          │
              └──────────────────────────┼──────────────────────────┘
                                         │
                            ┌─────────────────┐
                            │    Adapters     │
                            │                 │
                            │ ┌─────────────┐ │
                            │ │  Freqtrade  │ │
                            │ │  Strategy   │ │
                            │ └─────────────┘ │
                            │ ┌─────────────┐ │
                            │ │   Vedanta   │ │
                            │ │  Backtest   │ │
                            │ └─────────────┘ │
                            │ ┌─────────────┐ │
                            │ │ Custom APIs │ │
                            │ └─────────────┘ │
                            └─────────────────┘
```

---

**P1 Overdrive-NS** - 在極限條件下的精準交易決策系統
