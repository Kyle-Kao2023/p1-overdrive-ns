# P1 Overdrive-NS Trading Builder - AI Assistant Rules

## 🔄 项目感知与上下文

- **优先阅读项目文档**：每次对话开始时先查看 `PROJECT_STRUCTURE.md` 和 `README.md` 了解架构、目标和约束
- **检查配置文件**：使用 `configs/default.yaml` 中的配置参数和阈值
- **遵循现有架构**：保持微服务架构模式（Decision/FeatureHub/Vision 三服务分离）
- **理解 v2 架构**：熟悉 LLM Reasoner、xLSTM、Learner/Trainer 等 AI 增强组件

## 🏗️ 代码结构与模块化

### 文件大小限制
- **单文件不超过 300 行代码**：对于复杂算法文件，拆分为多个模块
- **API 路由文件不超过 150 行**：每个路由组分别建立文件
- **配置文件保持简洁**：复杂配置拆分为多个 YAML 文件

### 架构约定
```
services/
├── decision/          # 核心决策服务 (端口 8000)
│   ├── app.py        # FastAPI 应用入口
│   ├── routes/       # API 路由按功能分组
│   ├── brains/       # AI 推理引擎 (CTFG, xLSTM, LLM)
│   ├── gates/        # 安全门控制器
│   ├── learner/      # 学习训练管道
│   └── datahub/      # 数据连接器
├── featurehub/       # 特征工程服务 (端口 8010)
├── vision/           # 视觉识别服务 (端口 8020)
```

### 导入约定
- **使用相对导入**：包内使用 `from .module import Class`
- **绝对导入用于跨服务**：`from services.decision.core import Config`
- **按类型分组导入**：标准库 → 第三方 → 本地导入

## 🤖 AI/LLM 开发规范

### LLM Reasoner 开发
- **边界条件触发**：仅在 p_hit ∈ [0.72, 0.78] 等边界情况启用 LLM
- **超时保护**：所有 LLM 调用必须有 150ms 硬超时
- **成本控制**：每日 LLM 调用次数限制，优雅降级到传统决策
- **结构化输出**：LLM 返回必须包含 `rationale`, `meta_tag`, `c_llm` 字段

```python
# LLM 调用模式
async def llm_reason(features: dict, timeout_ms: int = 150):
    try:
        result = await asyncio.wait_for(
            llm_client.generate(prompt), 
            timeout=timeout_ms/1000
        )
        return structured_parse(result)
    except asyncio.TimeoutError:
        return fallback_decision()
```

### xLSTM 序列建模
- **内存状态管理**：压缩长序列到 256 字节状态
- **多模态融合**：HTF/LTF/Micro 三层时间框架注意力权重
- **增量训练**：支持在线学习，避免重新训练整个模型

## 🛡️ 交易系统安全规范

### 延迟要求
- **决策 SLA < 70ms**：所有 API 响应必须在 70ms 内完成
- **实时监控**：记录每个决策的 `runtime_ms` 指标
- **熔断机制**：连续超时时自动降级到快速决策模式

### 风险控制
- **输入验证**：使用 Pydantic 严格验证所有数值边界
- **Gate 系统**：四重安全门 (Vol/Consensus/LiqBuffer/Event) 必须通过
- **资金保护**：所有 `alloc_equity_pct` 输出必须有合理上限

```python
# 风险参数边界示例
RISK_LIMITS = {
    "alloc_equity_pct": {"min": 0.0, "max": 0.05},  # 最大 5%
    "p_hit_min": 0.75,  # 最小胜率要求
    "sigma_max": 0.003,  # 最大波动率限制
}
```

## 🧪 测试与可靠性

### 测试要求
- **延迟性能测试**：每个关键路径必须有延迟测试 `pytest -k test_latency`
- **Gate 逻辑测试**：每个 Gate 的边界条件测试
- **AI 组件测试**：LLM/xLSTM 的 mock 测试和集成测试
- **异常处理测试**：网络超时、API 故障等异常情况

### 测试结构
```
tests/
├── test_decision_api.py      # 决策 API 集成测试
├── test_gates.py            # Gate 逻辑单元测试
├── test_hazard_and_mpc.py   # 风险检测测试
├── test_llm_reasoner.py     # LLM 推理器测试
└── test_performance.py      # 性能和延迟测试
```

## 📊 数据模式与编码

### Likert-7 编码标准
```python
# 方向编码：连续评分 + 离散标签
direction = {
    "dir_score_htf": float,    # [-1, 1] 连续评分
    "dir_htf": int,            # [-3, +3] Likert-7 标签
    "dir_score_ltf": float,    
    "dir_ltf": int,
    "dir_score_micro": float,
    "dir_micro": int
}
```

### 特征工程约定
- **特征命名**：使用下划线命名 `sigma_1m`, `Z_4H`, `C_align`
- **时间框架后缀**：`_4H`, `_1H`, `_15m`, `_1m` 表示时间框架
- **置信度前缀**：`C_` 表示置信度/一致性指标

## 🔗 适配器开发

### 交易平台集成
- **统一接口**：所有适配器继承 `BaseAdapter` 抽象类
- **错误处理**：包装平台特定异常为标准 `AdapterError`
- **数据转换**：提供 `to_standard_format()` 和 `from_standard_format()` 方法

```python
# 适配器模式
class FreqtradeAdapter(BaseAdapter):
    def execute_decision(self, decision: DecisionResponse) -> ExecutionResult:
        # 转换决策格式
        # 调用平台 API
        # 返回标准结果
```

## 📈 监控与运维

### 日志标准
- **结构化日志**：使用 JSON 格式，包含 `trade_id`, `symbol`, `runtime_ms`
- **决策链追踪**：记录完整的 Gate 通过流程
- **错误上下文**：异常时记录完整的市场状态和输入特征

### 性能监控
- **关键指标**：`runtime_ms`, `p_hit_actual`, `success_rate`
- **实时告警**：超时、Gate 失败、异常率过高时触发
- **容量规划**：监控 LLM 调用次数和成本

## 🎯 AI 增强开发约定

### Learner/Trainer 管道
- **经验存储**：标准化经验格式，包含特征、决策、结果、人类反馈
- **批处理训练**：异步训练，不阻塞实时决策
- **模型版本控制**：所有模型更新记录版本和性能指标

### 人机协同接口
- **人类反馈集成**：支持 1-5 评分和文本反馈
- **偏好学习**：RLHF 管道收集交易员偏好
- **解释性输出**：所有 AI 决策包含自然语言解释

## ⚡ 开发流程

### 功能开发
1. **创建 INITIAL.md**：明确功能需求和约束
2. **生成 PRP**：使用 `/generate-prp` 创建详细实现计划
3. **执行开发**：使用 `/execute-prp` 实现功能
4. **性能验证**：确保满足延迟和准确性要求
5. **集成测试**：验证与现有系统的兼容性

### 代码审查重点
- **延迟性能**：关键路径是否满足 <70ms 要求
- **错误处理**：是否有优雅的降级机制
- **资源管理**：内存、连接池、LLM 调用次数控制
- **安全性**：输入验证、数值边界检查

## 🔧 工具链配置

### 开发环境
- **Python 3.11+**：使用最新特性支持 AI 库
- **FastAPI + Uvicorn**：高性能异步 API
- **Pytest + Coverage**：完整测试覆盖
- **Black + Ruff**：代码格式化和质量检查

### AI 库栈
- **FinGPT**：金融领域 LLM 推理
- **xLSTM**：长序列建模和记忆
- **FinRL**：金融强化学习环境
- **Conformal Prediction**：不确定性量化

---

> 🎯 **目标**：通过 Context Engineering 确保 AI 助手能够高质量地协助 P1 Trading Builder 的开发，特别是 v2 的 AI 增强功能。
