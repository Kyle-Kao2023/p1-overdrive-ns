# P1 Overdrive-NS Trading Builder

> **決策系統** - 高勝率A+段落交易的智能決策引擎
> # **NEW: v2 (Overdrive-NS + LLM 共學版)** - AI增強決策，人機協同學習

## 🆕 What's New in v2

**v2 引入人工智能增強功能：**

- 1. **LLM Reasoner** - 邊界情況下的人類式推理與元標籤生成
- 2. **xLSTM Architecture** - 長序列記憶，低延遲多模態融合 (YOLO V8看"空間排列" / xLSTM看"時間序列")
- 3. **Likert-7 Direction Encoding** - 連續方向評分 + 離散Likert標籤
- 4. **Learner/Trainer Pipeline** - 模仿學習 + RLHF + 離線強化學習
- 5. **FinGPT Integration** - 新聞情緒分析與事件風險評估
- 6. **FinRL Training** - 專業金融強化學習環境
- 7. **Conformal Prediction** - 統計嚴格的不確定性量化
- 8. **BOCPD Hazard Detection** - 變點檢測與智能退出

### v1 vs v2 比較

| 功能 | v1 (Pure Overdrive-NS) | v2 (+ LLM 共學版) |
|------|------------------------|------------------|
| **決策引擎** | CTFG 因子圖 | CTFG + xLSTM + LLM Reasoner |
| **方向編碼** | 簡單三元組 | Likert-7 + 連續dir_score |
| **學習能力** | 靜態規則 | IL + RLHF + 離線RL |
| **新聞處理** | 無 | FinGPT情緒分析 |
| **不確定性** | 保形預測 | 保形預測 + LLM置信度 |
| **邊界處理** | 拒絕 | LLM人類式推理 |
| **訓練環境** | 無 | FinRL專業環境 |
| **推理透明度** | 數字輸出 | 自然語言解釋 |

> 💡 **選擇指南**: v1適合純數量化策略；v2適合需要AI增強和持續學習的高級策略

[![CI/CD](https://github.com/user/p1-overdrive-ns/workflows/CI%2FCD%20Pipeline/badge.svg)](https://github.com/user/p1-overdrive-ns/actions)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.2-009688.svg)](https://fastapi.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🎯 项目概述

P1 Overdrive-NS 是一个加密貨幣智能合約交易设计的交易决策系统。**v2版本**通过AI增強架構，結合人類交易心理與數學嚴謹性，在高風險環境中實現精準的A+段落交易。

### 🔄 啟用v2功能

```yaml
# configs/v2.yaml
version: "2.0"
features:
  enable_llm_reasoner: true      # 啟用LLM推理器
  enable_xlstm: true             # 啟用xLSTM序列建模
  enable_learner_trainer: true   # 啟用學習訓練管道
  enable_fingpt: true            # 啟用FinGPT新聞分析
  enable_finrl: true             # 啟用FinRL訓練環境

llm_reasoner:
  model: "fingpt-7b"             # 本地FinGPT模型
  timeout_ms: 150                # LLM超時限制
  borderline_range: [0.72, 0.78] # 觸發LLM的邊界範圍

learner:
  experience_buffer_size: 10000   # 經驗回放緩存
  il_learning_rate: 0.001        # 模仿學習率
  rlhf_preference_weight: 0.3    # 人類反饋權重
```

### 核心特性

**v1 核心功能：**
- 🔒 **4-Gate安全系统** - Vol/Consensus/LiqBuffer/Event四层防护
- 🧠 **CTFG Loopy-BP引擎** - 12节点连续时间因子图推理
- ⚡ **<70ms决策延迟** - 满足高频交易SLA要求
- 📊 **实时风险评估** - 动态流动性缓冲验证
- 🎯 **保形预测校准** - 统计有效的置信区间
- 📈 **MPC动态退出** - Hazard感知的智能退出策略

**v2 AI增強功能：**
- 🤖 **LLM邊界推理** - 僅在邊界情況啟用，提供人類式rationale
- 🧩 **xLSTM長序列建模** - 處理複雜時間依賴，支援多模態融合
- 📏 **Likert-7方向編碼** - 精細化方向評分 + 連續置信度
- 🎓 **持續學習管道** - 模仿學習 + 人類反饋 + 離線強化學習
- 📰 **FinGPT新聞分析** - 實時情緒分析與事件風險評估
- 🏋️ **FinRL訓練環境** - 專業金融RL訓練與策略優化

## 🚀 快速开始

### 环境要求

- Python 3.11+
- Docker & Docker Compose
- Redis (可选，用于生产环境)

### 方式一：Docker 一键启动

```bash
# 克隆项目
git clone https://github.com/user/p1-overdrive-ns.git
cd p1-overdrive-ns

# 启动所有服务
docker-compose up --build

# 验证服务状态
curl http://localhost:8000/health
curl http://localhost:8010/health
curl http://localhost:8020/health
```

### 方式二：开发环境

```bash
# 安装依赖
pip install -r requirements.txt

# 启动开发服务
./scripts/run_dev.sh

# 或者手动启动各个服务
uvicorn services.decision.app:app --reload --port 8000 &
uvicorn services.featurehub.app:app --reload --port 8010 &
uvicorn services.vision.app:app --reload --port 8020 &
```

### 测试系统

**v1 API測試：**
```bash
# 运行测试脚本
python scripts/seed_examples.py

# 或直接测试API
curl -X POST http://localhost:8000/decide/enter \
  -H "Content-Type: application/json" \
  -d @services/decision/schemas/examples.py
```

**v2 API測試 (含LLM推理)：**
```bash
# 測試邊界情況LLM推理
curl -X POST http://localhost:8000/v2/decide/enter \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "ETHUSDT",
    "version": "2.0",
    "features": {
      "sigma_1m": 0.0018,
      "Z_4H": -0.9, "Z_1H": -0.7, "Z_15m": -0.6,
      "direction": {
        "dir_score_htf": -0.75, "dir_htf": -2,
        "dir_score_ltf": -0.65, "dir_ltf": -2,
        "dir_score_micro": -0.55, "dir_micro": -1
      },
      "news": {
        "sentiment_score": -0.3,
        "event_risk": 0.15
      }
    },
    "pgm": {
      "p_hit": 0.74,  # 邊界值，觸發LLM
      "mae_q999": 0.0058
    }
  }'
```

## 📡 API 端点

### Decision Service (端口 8000)

| 端点 | 方法 | 描述 |
|------|------|------|
| `/` | GET | 服务信息和功能概览 |
| `/health` | GET | 健康检查 |
| `/decide/enter` | POST | 入场决策API |
| `/decide/exit` | POST | 退出决策API |
| `/docs` | GET | OpenAPI文档 |

### FeatureHub Service (端口 8010)

| 端点 | 方法 | 描述 |
|------|------|------|
| `/snapshot` | GET | 获取市场快照 |
| `/tv/webhook` | POST | TradingView Pine Webhook |
| `/vision/tokens` | POST | YOLO视觉识别结果 |

### Vision Service (端口 8020)

| 端点 | 方法 | 描述 |
|------|------|------|
| `/detect` | POST | 图像模式检测 |

## 🔧 配置说明

### 环境变量

复制 `.env.example` 到 `.env` 并配置：

```bash
APP_ENV=dev                    # 环境：dev/prod
LOG_LEVEL=INFO                 # 日志级别
REDIS_URL=redis://redis:6379/0 # Redis连接
CONFIG_PATH=/app/configs/default.yaml
DECISION_PORT=8000
FEATUREHUB_PORT=8010
VISION_PORT=8020
```

### Gate配置 (configs/default.yaml)

```yaml
vol_sweet_spot:
  bull: {sigma_min: 0.0012, sigma_max: 0.0022, skew_min: 0.5}
  bear: {sigma_min: 0.0015, sigma_max: 0.0028, skew_max: -0.5}

gates:
  C_align_min: 0.85    # 多时间框架一致性阈值
  C_of_min: 0.80       # 订单流一致性阈值
  C_vision_min: 0.75   # 视觉识别一致性阈值
  p_hit_min: 0.75      # 最小命中概率
  epsilon: 0.0005      # 风险缓冲
  latency_slo_ms: 70   # 延迟SLA
```

## 🏗️ 系统架构

### v2 AI增強架構

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   DataHub v2    │    │ Decision Core   │    │   Vision YOLO   │
│                 │    │      v2         │    │                 │
│ • TradingView   │    │                 │    │ • Pattern Detect│
│ • OrderFlow     │────│ ┌─────────────┐ │────│ • C_vision Gen  │
│ • OnChain Data  │    │ │ CTFG Engine │ │    │ • Confidence    │
│ • FinGPT News   │    │ │ xLSTM Brain │ │    │ • YOLO Tokens   │
└─────────────────┘    │ │ 4-Gate Safe │ │    └─────────────────┘
         │              │ └─────────────┘ │              │
         │              │        │        │              │
         │              │ ┌─────────────┐ │              │
         │              │ │LLM Reasoner │ │              │
         │              │ │(Borderline) │ │              │
         │              │ └─────────────┘ │              │
         │              └─────────────────┘              │
         │                        │                      │
         └────────────────────────┼──────────────────────┘
                                  │
    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
    │ Learner/Trainer │    │   Adapters      │    │ Experience      │
    │                 │    │                 │    │ Store           │
    │ • Imitation     │────│ • Freqtrade     │    │                 │
    │ • RLHF          │    │ • Vedanta       │    │ • Replay Buffer │
    │ • FinRL Offline │    │ • Custom APIs   │────│ • Preference DB │
    └─────────────────┘    └─────────────────┘    └─────────────────┘
```

### v2 決策流程

```
Market Data → Feature Engineering → Multi-Brain Fusion → Decision
     │              │                      │              │
     │         ┌────────────┐         ┌──────────┐        │
     │         │ Likert-7   │         │   CTFG   │        │
     │         │ Direction  │         │ + xLSTM  │        │
     │         │ Encoding   │         │ Fusion   │        │
     │         └────────────┘         └──────────┘        │
     │              │                      │              │
     │              │              Borderline Check       │
     │              │                   (0.72-0.78)      │
     │              │                      │              │
     │              │                ┌──────────┐        │
     │              │                │   LLM    │        │
     │              └────────────────│ Reasoner │────────┤
     │                               │(FinGPT)  │        │
     │                               └──────────┘        │
     │                                     │              │
     └─────────────────────────────────────┴──────────────┘
                           │
                     Gates Check
                  (Vol/Consensus/Liq/Safety)
                           │
                      Final Decision
                    + Reason Chain
                    + Meta Tags
```

## 🎮 使用示例

### v2 入场决策示例 (含LLM推理)

```python
import requests

# v2 決策請求 (含Likert-7編碼 + 新聞分析)
enter_request = {
    "symbol": "ETHUSDT",
    "version": "2.0",  # 啟用v2功能
    "side_hint": "short",
    "ts": "2025-09-14T10:25:00Z",
    "tf": "15m",
    "features": {
        "sigma_1m": 0.0018,
        "skew_1m": -0.72,
        "Z_4H": -0.9, "Z_1H": -0.7, "Z_15m": -0.6,
        "C_align": 0.88, "C_of": 0.83, "C_vision": 0.79,
        "pine_match": True,
        # v2: Likert-7 方向編碼
        "direction": {
            "dir_score_htf": -0.75,   # 連續評分 [-1,1]
            "dir_htf": -2,            # Likert-7 標籤 [-3,+3]
            "dir_score_ltf": -0.65,
            "dir_ltf": -2,
            "dir_score_micro": -0.55,
            "dir_micro": -1
        },
        # v2: FinGPT新聞分析
        "news": {
            "sentiment_score": -0.3,   # 新聞情緒 [-1,1]
            "event_risk": 0.15,       # 事件風險 [0,1]
            "headline_summary": "Fed hawkish signals concern crypto markets"
        },
        # v2: xLSTM序列特徵
        "xlstm_features": {
            "sequence_embedding": [0.1, -0.3, 0.7, ...],  # 256-dim
            "attention_weights": [0.8, 0.15, 0.05],       # HTF/LTF/Micro
            "memory_state": "compressed_256_byte_state"
        }
    },
    "pgm": {
        "p_hit": 0.74,  # 邊界值！將觸發LLM Reasoner
        "mae_q999": 0.0058,
        "slip_q95": 0.0004,
        "t_hit_q50_bars": 6,
        # v2: 保形預測置信區間
        "conformal_ci": {
            "p_hit_lower": 0.71,
            "p_hit_upper": 0.77,
            "coverage_prob": 0.95
        }
    }
}

# 调用决策API
response = requests.post("http://localhost:8000/decide/enter", json=enter_request)
decision = response.json()

# v2 回應包含LLM推理結果
print(f"决策结果: {'允许' if decision['allow'] else '拒绝'}")
print(f"建议方向: {decision.get('side')}")
print(f"分配比例: {decision.get('alloc_equity_pct', 0):.1%}")
print(f"推理链: {decision['reason_chain']}")

# v2 新增欄位
if 'llm_reasoning' in decision:
    llm = decision['llm_reasoning']
    print(f"\n🤖 LLM推理 (邊界情況):")
    print(f"  Rationale: {llm['rationale']}")
    print(f"  Meta Tag: {llm['meta_tag']}")
    print(f"  LLM置信度: {llm['c_llm']:.2f}")
    print(f"  觸發原因: p_hit={enter_request['pgm']['p_hit']} in borderline range")

if 'learner_feedback' in decision:
    print(f"\n🎓 學習器建議:")
    print(f"  建議動作: {decision['learner_feedback']['suggested_action']}")
    print(f"  經驗相似度: {decision['learner_feedback']['experience_similarity']:.2f}")

# 範例輸出:
# 决策结果: 允许
# 建议方向: short
# 分配比例: 2.5%
# 推理链: Vol_OK→Consensus_OK→LiqBuffer_OK→Safety_OK→LLM_Arbitration
#
# 🤖 LLM推理 (邊界情況):
#   Rationale: "HTF/LTF bearish alignment with Fed hawkish sentiment creates high-probability short setup despite borderline hit rate"
#   Meta Tag: "fed-policy-crypto-short"
#   LLM置信度: 0.68
#   觸發原因: p_hit=0.74 in borderline range
#
# 🎓 學習器建議:
#   建議動作: reduce_position_size
#   經驗相似度: 0.82
```

### Freqtrade集成

```python
# 在Freqtrade策略中使用
from adapters.freqtrade.ExternalDecisionStrategy import ExternalDecisionStrategy

class MyP1Strategy(ExternalDecisionStrategy):
    def populate_entry_trend(self, dataframe, metadata):
        # 自动调用P1决策API
        return super().populate_entry_trend(dataframe, metadata)
```

## 🧪 测试

```bash
# 运行所有测试
pytest -v

# 测试特定模块
pytest tests/test_gates.py -v
pytest tests/test_decision_api.py -v
pytest tests/test_hazard_and_mpc.py -v

# 性能测试
pytest tests/ -k "test_latency" -v
```

## 🔄 开发工作流

### 代码质量检查

```bash
# 格式化代码
black .
isort .

# 检查代码质量
ruff check .
mypy services/ adapters/

# 运行pre-commit钩子
pre-commit run --all-files
```

### 添加新的Gate

1. 在 `services/decision/gates/` 下创建新Gate模块
2. 实现 `passes(features) -> Tuple[bool, str]` 接口
3. 在 `reasoner.py` 中集成新Gate
4. 添加对应的测试用例

### 扩展适配器

1. 在 `adapters/` 下创建新的交易平台适配器
2. 实现数据格式转换函数
3. 调用Decision API并处理响应
4. 添加集成测试

## 📊 监控与运维

### 健康检查

```bash
# 基础健康检查
curl http://localhost:8000/health

# 详细系统状态  
curl http://localhost:8000/status

# 性能指标
curl http://localhost:8000/metrics
```

### 日志分析

```bash
# 查看决策日志
docker-compose logs decision | grep "Decision completed"

# 查看Gate拒绝原因
docker-compose logs decision | grep "Gate FAIL"

# 监控延迟性能
docker-compose logs decision | grep "runtime_ms"
```

## 🛡️ 安全考虑

- ✅ **输入验证** - Pydantic严格验证所有API输入
- ✅ **参数边界** - 所有数值参数都有合理的边界检查
- ✅ **超时保护** - API调用都有超时限制
- ✅ **错误隔离** - 单个组件故障不影响整体系统
- ✅ **日志审计** - 详细的决策过程日志记录

## 📄 v2 Data Schema

### Likert-7 Direction Encoding

```json
{
  "direction": {
    "dir_score_htf": -0.75,    // 連續評分 [-1,1]
    "dir_htf": -2,             // Likert-7 標籤 [-3,+3]
    "dir_score_ltf": -0.65,    // 短期方向置信度
    "dir_ltf": -2,             // 短期Likert標籤
    "dir_score_micro": -0.55,  // 微觀方向評分
    "dir_micro": -1            // 微觀Likert標籤
  }
}
```

### LLM Reasoner Output

```json
{
  "llm_reasoning": {
    "rationale": "HTF bearish with Fed hawkish sentiment creates high-prob short",
    "meta_tag": "fed-policy-crypto-short",
    "c_llm": 0.68,             // LLM置信度 [0,1]
    "triggered_by": "borderline_p_hit",
    "reasoning_time_ms": 147   // 推理耗時
  }
}
```

### Experience Store Schema

```json
{
  "experience": {
    "trade_id": "uuid-12345",
    "features": { /* 完整特徵向量 */ },
    "decision": { /* 系統決策 */ },
    "outcome": {
      "p_hit_actual": 0.76,
      "mae_actual": 0.0052,
      "t_hit_actual_bars": 7,
      "human_rating": 4,       // 人類評分 [1-5]
      "preference_reason": "Good timing but size too large"
    },
    "meta": {
      "market_regime": "high_vol_bear",
      "learning_weight": 1.0
    }
  }
}
```

## 🤖 LLM Reasoner API

### 觸發條件

LLM Reasoner **僅在邊界情況下啟用**，避免過度依賴和成本浪費：

```python
# 邊界條件
borderline_triggers = {
    "p_hit": (0.72, 0.78),           # 命中率邊界
    "consensus_score": (0.75, 0.85), # 共識度邊界
    "conflicting_signals": True,     # 信號衝突
    "high_news_impact": True         # 重大新聞事件
}

# 超時保護
llm_config = {
    "timeout_ms": 150,    # 硬性超時
    "fallback_decision": "conservative",
    "max_daily_calls": 100  # 成本控制
}
```

### API端點

```bash
# LLM推理端點
POST /v2/llm/reason
{
  "features": { /* 特徵向量 */ },
  "context": {
    "current_p_hit": 0.74,
    "conflicting_signals": ["TV_bearish", "OF_bullish"],
    "market_regime": "high_vol"
  },
  "constraints": {
    "max_tokens": 100,
    "response_format": "structured"
  }
}
```

## 🎓 Learner/Trainer Pipeline

### 三階段學習架構

```
1. Imitation Learning (IL)
   ├── 收集人工標註交易決策
   ├── 訓練基礎決策模型
   └── Bootstrap系統基本能力

2. Reinforcement Learning from Human Feedback (RLHF)
   ├── 收集人類偏好反饋
   ├── 訓練獎勵模型
   └── 優化決策品質

3. Offline Reinforcement Learning (FinRL)
   ├── 大規模歷史數據訓練
   ├── 策略迭代優化
   └── 持續性能提升
```

### 使用Experience Store

```python
# 經驗存儲
from services.decision.learner.experience_store import ExperienceStore

store = ExperienceStore()

# 存儲交易經驗
store.add_experience(
    features=market_features,
    decision=system_decision,
    outcome=actual_outcome,
    human_feedback=trader_rating
)

# 檢索相似經驗
similar_cases = store.query_similar(
    current_features,
    similarity_threshold=0.8,
    limit=5
)

# 訓練學習器
learner.train_on_experience_batch(
    store.sample_batch(batch_size=256)
)
```

## 🔮 Roadmap

### v2.0.0 (當前開發)
- [x] LLM Reasoner基礎架構
- [x] xLSTM序列建模集成
- [x] Likert-7方向編碼
- [x] FinGPT新聞分析
- [ ] 完整Learner/Trainer pipeline
- [ ] 大規模Experience Store
- [ ] FinRL離線訓練環境

### v2.1.0 (效能優化)
- [ ] LLM推理加速 (<100ms)
- [ ] 分散式xLSTM訓練
- [ ] 動態學習率調整
- [ ] A/B測試框架

### v2.2.0 (生產就緒)
- [ ] 多模型集成 (GPT-4, Claude, FinGPT)
- [ ] 實時學習與適應
- [ ] 完整Web監控介面
- [ ] 高可用性部署

## 🤝 贡献指南

1. Fork项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📚 v2 文檔鏈接

- 📖 **[詳細v2架構說明](docs/README_v2.md)** - 深入解析v2各組件
- 🔄 **[v1到v2升級指南](docs/UPGRADE_TO_V2.md)** - 完整遷移步驟
- 🧪 **[v2 API文檔](http://localhost:8000/v2/docs)** - OpenAPI規格
- 🎯 **[LLM Reasoner範例](examples/llm_reasoning/)** - 實際使用案例
- 📊 **[Learner/Trainer教程](examples/learner_training/)** - 訓練流程

## ⚠️ v2 注意事項

### LLM成本控制
- 💰 **成本預算**: LLM推理成本約$0.01-0.05/次，建議設置每日上限
- ⏱️ **延遲管理**: LLM回應150ms超時，邊界情況外不啟用
- 🔧 **本地化選項**: 可使用本地FinGPT/LLaMA降低成本

### 資料標註需求
- 📝 **最少需求**: ≥100筆人工標註交易避免過擬合
- 👥 **專家參與**: 建議有經驗交易員參與標註和偏好設定
- 🔄 **持續更新**: 定期更新標註數據以適應市場變化


## 📞 支持

- 📧 Email: ids20232024@gmail.com
- 💬 Discord: [P1 Trading Community](https://discord.gg/p1trading)
- 📚 文档: [docs.p1trading.dev](https://docs.p1trading.dev)
- 🐛 问题报告: [GitHub Issues](https://github.com/user/p1-overdrive-ns/issues)
- 🆕 **v2專用**: [v2-feedback@p1trading.dev](mailto:v2-feedback@p1trading.dev)

---

🚀 **Happy Trading!** - P1 Team
