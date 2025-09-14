# P1-System v1 到 v2 升級指南

> 從純量化 Overdrive-NS 升級到 AI 增強的 LLM 共學版

## 🎯 升級概覽

v2 在保持 v1 核心穩定性的基礎上，增加了 AI 增強決策能力。升級過程設計為**向後兼容**，v1 API 仍可正常使用。

### 核心改變

| 組件 | v1 | v2 | 向後兼容 |
|------|----|----|----------|
| **API 端點** | `/decide/enter` | `/v2/decide/enter` | ✅ v1 端點保留 |
| **決策引擎** | CTFG | CTFG + xLSTM + LLM | ✅ CTFG 仍為主要引擎 |
| **方向編碼** | 三元組 | Likert-7 + 連續 | ✅ 自動轉換 |
| **配置文件** | `default.yaml` | `v2.yaml` | ✅ 默認 v1 配置 |

## 📋 升級前檢查清單

### 1. 系統要求檢查

```bash
# 檢查 Python 版本 (需要 3.11+)
python --version

# 檢查可用內存 (v2 需要額外 2GB)
free -h

# 檢查磁盤空間 (模型文件需要 5GB)
df -h

# 檢查 GPU (可選，加速 LLM 推理)
nvidia-smi  # 如果有 NVIDIA GPU
```

### 2. 數據備份

```bash
# 備份當前配置
cp configs/default.yaml configs/default_v1_backup.yaml

# 備份決策日誌
tar -czf decision_logs_v1_$(date +%Y%m%d).tar.gz logs/

# 備份數據庫 (如果使用)
pg_dump p1_trading > p1_trading_v1_backup.sql
```

### 3. 依賴檢查

```bash
# 檢查 Docker 版本
docker --version
docker-compose --version

# 檢查網絡連接 (下載模型需要)
curl -I https://huggingface.co

# 檢查 Redis 可用性
redis-cli ping
```

## 🚀 升級步驟

### Step 1: 停止 v1 服務

```bash
# 停止所有 v1 服務
docker-compose down

# 確認進程完全停止
ps aux | grep "uvicorn\|python" | grep -v grep
```

### Step 2: 更新代碼

```bash
# 拉取最新 v2 代碼
git fetch origin
git checkout main
git pull origin main

# 檢查 v2 文件存在
ls -la services/decision/brains/llm_reasoner.py
ls -la services/decision/learner/
ls -la update/p1-system-v2-overdrive-ns-llm/
```

### Step 3: 安裝 v2 依賴

```bash
# 安裝新依賴
pip install -r requirements-v2.txt

# 安裝 FinGPT 模型 (可選，使用本地 LLM)
pip install fingpt-toolkit

# 下載預訓練模型
python scripts/download_v2_models.py
```

### Step 4: 配置 v2

```bash
# 複製 v2 配置模板
cp configs/v2.yaml.example configs/v2.yaml

# 編輯 v2 配置
nano configs/v2.yaml
```

**關鍵配置項目：**

```yaml
# configs/v2.yaml
version: "2.0"

# v2 功能開關 (可逐步啟用)
features:
  enable_llm_reasoner: true      # 啟用 LLM 推理器
  enable_xlstm: true             # 啟用 xLSTM 序列建模
  enable_learner_trainer: false # 第一階段先關閉
  enable_fingpt: true            # 啟用新聞分析
  enable_finrl: false            # 離線訓練暫時關閉

# LLM 推理配置
llm_reasoner:
  provider: "fingpt"             # fingpt, openai, anthropic
  model: "fingpt-7b"
  api_key: ""                    # 如果使用雲端服務
  timeout_ms: 150                # 嚴格超時限制
  borderline_range: [0.72, 0.78] # 觸發 LLM 的範圍
  max_daily_calls: 100           # 成本控制
  fallback_strategy: "conservative" # 超時時的備用策略

# xLSTM 配置
xlstm:
  model_path: "models/xlstm_v2.pt"
  sequence_length: 256
  hidden_dim: 512
  num_layers: 6

# 學習器配置 (暫時關閉)
learner:
  experience_buffer_size: 10000
  learning_rate: 0.001
  batch_size: 128

# v1 兼容性設置
compatibility:
  v1_api_enabled: true           # 保持 v1 API 可用
  auto_convert_direction: true   # 自動轉換方向編碼
  fallback_to_v1: true           # 出錯時回退到 v1
```

### Step 5: 數據遷移

```bash
# 運行 v2 數據遷移腳本
python scripts/migrate_to_v2.py

# 驗證數據遷移
python scripts/validate_v2_migration.py
```

### Step 6: 啟動 v2 服務

```bash
# 啟動 v2 服務 (混合模式)
docker-compose -f docker-compose.v2.yml up -d

# 檢查服務狀態
docker-compose ps
curl http://localhost:8000/health
curl http://localhost:8000/v2/health
```

## 🧪 v2 功能測試

### 1. 基本 API 測試

```bash
# 測試 v1 API 仍然工作
curl -X POST http://localhost:8000/decide/enter \
  -H "Content-Type: application/json" \
  -d @tests/data/v1_sample.json

# 測試 v2 API
curl -X POST http://localhost:8000/v2/decide/enter \
  -H "Content-Type: application/json" \
  -d @tests/data/v2_sample.json
```

### 2. LLM 推理測試

```python
# 測試邊界情況觸發 LLM
import requests

borderline_request = {
    "symbol": "ETHUSDT",
    "version": "2.0",
    "features": {
        "sigma_1m": 0.0018,
        "direction": {
            "dir_score_htf": -0.75,
            "dir_htf": -2,
            "dir_score_ltf": -0.65,
            "dir_ltf": -2
        }
    },
    "pgm": {
        "p_hit": 0.74,  # 邊界值，應觸發 LLM
        "mae_q999": 0.0058
    }
}

response = requests.post(
    "http://localhost:8000/v2/decide/enter",
    json=borderline_request
)

result = response.json()

# 檢查 LLM 推理是否啟用
assert "llm_reasoning" in result
print(f"LLM Rationale: {result['llm_reasoning']['rationale']}")
```

### 3. 性能基準測試

```bash
# 運行 v2 性能測試
python tests/benchmark_v2.py

# 比較 v1 vs v2 延遲
python tests/compare_v1_v2_latency.py
```

## 🔄 逐步功能啟用

### 階段 1: 核心 AI 功能 (推薦)

```yaml
# 僅啟用核心 AI 功能
features:
  enable_llm_reasoner: true
  enable_xlstm: true
  enable_learner_trainer: false
  enable_fingpt: true
  enable_finrl: false
```

**驗證步驟：**
- [ ] LLM 推理在邊界情況正常工作
- [ ] xLSTM 序列特徵正常生成
- [ ] 新聞情緒分析正常運行
- [ ] 延遲仍在 70ms SLA 內

### 階段 2: 學習器功能

```yaml
# 啟用學習器 (需要標註數據)
features:
  enable_learner_trainer: true
```

**前置需求：**
- [ ] 準備 ≥100 筆人工標註交易
- [ ] 設置 Experience Store 數據庫
- [ ] 配置人類反饋收集界面

### 階段 3: 離線訓練

```yaml
# 啟用 FinRL 離線訓練
features:
  enable_finrl: true
```

**前置需求：**
- [ ] 大量歷史數據 (≥1年)
- [ ] GPU 訓練環境
- [ ] 訓練計算資源預算

## 🛠️ 問題排除

### 常見問題

#### 1. LLM 推理超時

**症狀：** LLM 推理頻繁超時，回退到 conservative 策略

**解決方案：**
```yaml
llm_reasoner:
  timeout_ms: 200  # 增加超時時間
  provider: "fingpt"  # 切換到本地模型
  fallback_strategy: "use_ctfg_only"
```

#### 2. xLSTM 模型加載失敗

**症狀：** `FileNotFoundError: models/xlstm_v2.pt`

**解決方案：**
```bash
# 重新下載模型
python scripts/download_v2_models.py --force
# 或使用備用模型
cp models/xlstm_backup.pt models/xlstm_v2.pt
```

#### 3. 性能退化

**症狀：** v2 延遲超過 70ms SLA

**診斷：**
```bash
# 檢查各組件延遲
curl http://localhost:8000/v2/metrics/latency
```

**解決方案：**
- 關閉 LLM 推理: `enable_llm_reasoner: false`
- 調整 xLSTM 參數: `sequence_length: 128`
- 使用 GPU 加速: `device: "cuda"`

#### 4. v1 API 不工作

**症狀：** v1 端點返回 404

**解決方案：**
```yaml
compatibility:
  v1_api_enabled: true  # 確保啟用
```

## 🔙 回退計劃

如果 v2 出現嚴重問題，可以快速回退到 v1：

### 快速回退

```bash
# 1. 停止 v2 服務
docker-compose -f docker-compose.v2.yml down

# 2. 恢復 v1 配置
cp configs/default_v1_backup.yaml configs/default.yaml

# 3. 啟動 v1 服務
docker-compose up -d

# 4. 驗證服務正常
curl http://localhost:8000/health
```

### 數據回退

```bash
# 恢復 v1 數據庫
psql p1_trading < p1_trading_v1_backup.sql

# 恢復日誌
tar -xzf decision_logs_v1_*.tar.gz
```

## 📊 升級後監控

### 關鍵指標

```bash
# 延遲監控
watch 'curl -s http://localhost:8000/v2/metrics | jq .latency_p95'

# LLM 使用率
watch 'curl -s http://localhost:8000/v2/metrics | jq .llm_usage'

# 錯誤率
watch 'curl -s http://localhost:8000/v2/metrics | jq .error_rate'
```

### 報警設置

```yaml
# alerts.yaml
alerts:
  - name: "v2_high_latency"
    condition: "latency_p95 > 70"
    action: "email,slack"

  - name: "llm_timeout_rate"
    condition: "llm_timeout_rate > 0.1"
    action: "disable_llm"

  - name: "v2_error_rate"
    condition: "error_rate > 0.05"
    action: "fallback_to_v1"
```

## 📚 進階配置

### 多模型 LLM 設置

```yaml
# 支持多個 LLM 提供商
llm_reasoner:
  providers:
    - name: "fingpt"
      model: "fingpt-7b"
      weight: 0.6
    - name: "openai"
      model: "gpt-4-turbo"
      weight: 0.3
    - name: "anthropic"
      model: "claude-3-sonnet"
      weight: 0.1

  ensemble_strategy: "weighted_average"
```

### 自定義學習器配置

```yaml
learner:
  imitation_learning:
    data_path: "data/expert_trades.jsonl"
    model_architecture: "transformer"
    learning_rate: 0.001

  rlhf:
    preference_model: "bradley_terry"
    reward_learning_rate: 0.0005

  offline_rl:
    algorithm: "CQL"  # Conservative Q-Learning
    env_config: "finrl_crypto_100x"
```

## ✅ 升級完成檢查

- [ ] v1 API 仍然正常工作
- [ ] v2 API 響應正確的 JSON 格式
- [ ] LLM 推理在邊界情況正常觸發
- [ ] xLSTM 特徵提取正常工作
- [ ] 延遲仍在 SLA 範圍內 (<70ms)
- [ ] 所有 Gate 檢查正常通過
- [ ] 新聞情緒分析正常運行
- [ ] 監控和報警配置完成
- [ ] 回退計劃測試通過

## 🆘 獲取幫助

如果升級過程中遇到問題：

- 📧 **技術支持**: [v2-support@p1trading.dev](mailto:v2-support@p1trading.dev)
- 💬 **Discord**: [#v2-upgrade 頻道](https://discord.gg/p1trading)
- 📚 **文檔**: [完整 v2 文檔](README_v2.md)
- 🐛 **問題報告**: [GitHub Issues](https://github.com/user/p1-overdrive-ns/issues) (標記 `v2-upgrade`)

---

🎉 **恭喜！** 您已成功升級到 P1-System v2，享受 AI 增強的交易決策能力！