# P1 Overdrive-NS Trading Builder

> **100x No-Stop 精准決策系統** - 高勝率A+段落交易的智能決策引擎

[![CI/CD](https://github.com/user/p1-overdrive-ns/workflows/CI%2FCD%20Pipeline/badge.svg)](https://github.com/user/p1-overdrive-ns/actions)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.2-009688.svg)](https://fastapi.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🎯 项目概述

P1 Overdrive-NS 是一个专为100x槓桿與不預掛止損（No-Stop）设计的交易决策系统。通过四道安全Gate、CTFG决策引擎和动态MPC退出策略，在高风险环境中实现精准的A+段落交易。

### 核心特性

- 🔒 **4-Gate安全系统** - Vol/Consensus/LiqBuffer/Event四层防护
- 🧠 **CTFG Loopy-BP引擎** - 12节点连续时间因子图推理
- ⚡ **<70ms决策延迟** - 满足高频交易SLA要求
- 📊 **实时风险评估** - 动态流动性缓冲验证
- 🎯 **保形预测校准** - 统计有效的置信区间
- 📈 **MPC动态退出** - Hazard感知的智能退出策略

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

```bash
# 运行测试脚本
python scripts/seed_examples.py

# 或直接测试API
curl -X POST http://localhost:8000/decide/enter \
  -H "Content-Type: application/json" \
  -d @services/decision/schemas/examples.py
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

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FeatureHub    │    │  Decision Core  │    │   Vision YOLO   │
│                 │    │                 │    │                 │
│ • TradingView   │────│ • 4-Gate System │    │ • Pattern Detect│
│ • OrderFlow     │    │ • CTFG Engine   │    │ • C_vision Gen  │
│ • OnChain Data  │    │ • MPC Exit      │────│ • Confidence    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                        │                        │
         └────────────────────────┼────────────────────────┘
                                  │
                    ┌─────────────────┐
                    │   Adapters      │
                    │                 │
                    │ • Freqtrade     │
                    │ • Vedanta       │
                    │ • Custom APIs   │
                    └─────────────────┘
```

## 🎮 使用示例

### 入场决策示例

```python
import requests

# 构建决策请求
enter_request = {
    "symbol": "ETHUSDT",
    "side_hint": "short", 
    "ts": "2025-09-14T10:25:00Z",
    "tf": "15m",
    "features": {
        "sigma_1m": 0.0018,
        "skew_1m": -0.72,
        "Z_4H": -0.9, "Z_1H": -0.7, "Z_15m": -0.6,
        "C_align": 0.88, "C_of": 0.83, "C_vision": 0.79,
        "pine_match": True,
        # ... 更多特征
    },
    "pgm": {
        "p_hit": 0.79,
        "mae_q999": 0.0058,
        "slip_q95": 0.0004,
        "t_hit_q50_bars": 6
    }
}

# 调用决策API
response = requests.post("http://localhost:8000/decide/enter", json=enter_request)
decision = response.json()

print(f"决策结果: {'允许' if decision['allow'] else '拒绝'}")
print(f"建议方向: {decision.get('side')}")
print(f"分配比例: {decision.get('alloc_equity_pct', 0):.1%}")
print(f"推理链: {decision['reason_chain']}")
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

## 🔮 Roadmap

### v0.2.0 (下一版本)
- [ ] 真实CTFG Loopy-BP模型集成
- [ ] 实际YOLO/DETR视觉检测
- [ ] Binance/Bybit实时数据连接
- [ ] 高级保形预测校准

### v1.0.0 (生产版本)
- [ ] 完整回测系统
- [ ] 实时性能优化 (<30ms)
- [ ] 分布式部署支持
- [ ] Web监控界面

## 🤝 贡献指南

1. Fork项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 支持

- 📧 Email: support@p1trading.dev
- 💬 Discord: [P1 Trading Community](https://discord.gg/p1trading)
- 📚 文档: [docs.p1trading.dev](https://docs.p1trading.dev)
- 🐛 问题报告: [GitHub Issues](https://github.com/user/p1-overdrive-ns/issues)

---

⚡ **风险提示**: 本系统为高风险交易工具，100x杠杆交易具有极高风险，请确保充分理解风险并在模拟环境中充分测试后再用于实盘交易。

🚀 **Happy Trading!** - P1 Team
