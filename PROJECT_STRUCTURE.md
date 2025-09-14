# P1 Overdrive-NS 专案架构说明

## 📁 专案结构

```
P1_Trading_Builder/
├── .git/                          # Git 版本控制
├── .github/                       # GitHub 配置
│   ├── ISSUE_TEMPLATE/            # Issue 模板
│   ├── workflows/                 # CI/CD 工作流
│   └── pull_request_template.md   # PR 模板
├── adapters/                      # 交易平台适配器
│   ├── freqtrade/                 # Freqtrade 适配器
│   │   ├── __init__.py
│   │   └── ExternalDecisionStrategy.py  # 外部决策策略
│   └── vedanta/                   # Vedanta 适配器
│       ├── __init__.py
│       ├── vedanta_enter_adapter.py
│       └── vedanta_exit_adapter.py
├── services/                      # 核心服务
│   ├── decision/                  # 决策服务 (端口 8000)
│   │   ├── core/                  # 核心配置
│   │   ├── decision/              # 决策逻辑
│   │   ├── execution/             # 执行逻辑
│   │   ├── gates/                 # 4-Gate 系统
│   │   ├── models/                # ML 模型
│   │   ├── routes/                # API 路由
│   │   ├── schemas/               # 数据结构
│   │   └── app.py                 # FastAPI 应用
│   ├── featurehub/               # 特征中心 (端口 8010)
│   │   ├── connectors/           # 数据连接器
│   │   ├── app.py
│   │   └── schemas.py
│   └── vision/                   # 视觉识别服务 (端口 8020)
│       ├── app.py
│       └── schemas.py
├── tests/                        # 测试文件
├── scripts/                      # 工具脚本
├── configs/                      # 配置文件
├── docs/                        # 项目文档
├── docker-compose.yml           # Docker 编排
├── Dockerfile                   # Docker 镜像
├── requirements.txt             # Python 依赖
├── pyproject.toml              # 项目配置
├── .gitignore                  # Git 忽略文件
├── .pre-commit-config.yaml     # 代码质量检查
└── README.md                   # 项目说明
```

## 🏗️ 核心组件

### 1. Decision Service (决策服务)
- **端口**: 8000
- **功能**: 提供入场/退出决策API
- **核心模块**:
  - 4-Gate安全系统 (Vol/Consensus/LiqBuffer/Event)
  - CTFG Loopy-BP推理引擎
  - MPC动态退出策略
  - 保形预测校准

### 2. FeatureHub Service (特征中心)
- **端口**: 8010
- **功能**: 实时市场数据聚合和特征工程
- **数据源**:
  - TradingView Pine信号
  - Binance WebSocket (计划)
  - 链上数据 (OI, Gas费等)
  - 订单流数据

### 3. Vision Service (视觉识别)
- **端口**: 8020
- **功能**: 图表模式识别和C_vision生成
- **技术**: YOLO/DETR模型 (计划集成)

### 4. Adapters (适配器层)
- **Freqtrade适配器**: 将决策API集成到Freqtrade策略
- **Vedanta适配器**: 自定义交易平台支持
- **扩展性**: 支持添加新的交易平台

## 🔄 数据流

```
[市场数据] → [FeatureHub] → [Decision Core] → [适配器] → [交易平台]
     ↑             ↓              ↓              ↓
[TradingView] [特征工程]    [4-Gate系统]   [信号转换]
[OrderFlow]   [风险计算]    [CTFG推理]     [仓位管理]
[OnChain]     [Vision]      [MPC退出]      [执行]
```

## 📊 技术栈

- **后端框架**: FastAPI 0.115.2
- **数据处理**: Pandas, NumPy, TA-Lib
- **机器学习**: PyTorch (计划), Scikit-learn
- **数据库**: Redis (缓存)
- **部署**: Docker, Docker Compose
- **监控**: 自定义健康检查和性能指标
- **代码质量**: Black, Ruff, MyPy, Pre-commit

## 🚀 部署架构

### 开发环境
```bash
# 方式一：Docker 一键启动
docker-compose up --build

# 方式二：本地开发
pip install -r requirements.txt
uvicorn services.decision.app:app --reload --port 8000 &
uvicorn services.featurehub.app:app --reload --port 8010 &
uvicorn services.vision.app:app --reload --port 8020 &
```

### 生产环境 (计划)
- Kubernetes 部署
- Redis Cluster
- 负载均衡
- 监控和日志聚合

## 🛡️ 安全特性

- **输入验证**: Pydantic 严格类型检查
- **参数边界**: 所有数值参数边界检查
- **超时保护**: API调用超时限制 (<70ms)
- **错误隔离**: 组件故障不影响其他服务
- **日志审计**: 完整的决策过程记录

## 📈 性能指标

- **决策延迟**: <70ms (SLA要求)
- **API可用性**: >99.9%
- **准确率目标**: P_hit >75%
- **风险控制**: MAE <0.6%, Slip <0.05%

## 🔮 下一步计划

### v0.2.0 (下一版本)
- [ ] 真实CTFG Loopy-BP模型
- [ ] YOLO视觉检测集成
- [ ] Binance实时数据
- [ ] 高级保形预测

### v1.0.0 (生产版本)
- [ ] 完整回测系统
- [ ] 分布式部署
- [ ] Web监控界面
- [ ] 性能优化 (<30ms)

## 🤝 开发指南

1. **Fork & Clone**: 
   ```bash
   git clone https://github.com/user/p1-overdrive-ns.git
   ```

2. **设置开发环境**:
   ```bash
   pip install -r requirements.txt
   pre-commit install
   ```

3. **运行测试**:
   ```bash
   pytest -v
   python scripts/seed_examples.py
   ```

4. **代码质量检查**:
   ```bash
   black .
   ruff check .
   mypy services/ adapters/
   ```