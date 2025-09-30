# P1 Trading Builder - 功能开发模板

> 使用此模板创建新功能的需求文档，然后使用 `/generate-prp` 和 `/execute-prp` 命令实现

## FEATURE:

[在此描述您要构建的功能 - 对功能和需求要具体明确]

### 功能类型示例：
- **新 Gate 组件**：如流动性 Gate、情绪 Gate、技术指标 Gate
- **AI 增强模块**：如新的 LLM 推理器、xLSTM 变体、学习算法
- **数据连接器**：如新交易所 API、DeFi 协议数据、链上指标
- **适配器开发**：如新交易平台集成、策略执行器
- **监控工具**：如性能仪表板、告警系统、回测框架

## EXAMPLES:

[列出 `examples/` 文件夹中的相关示例文件，并解释应如何使用]

### P1 系统示例参考：
- **Gate 开发**：参考 `examples/decision_patterns/gate_implementation.py`
  - 继承 BaseGate 抽象类模式
  - 标准化的配置和日志处理
  - 边界条件验证逻辑

- **AI 组件开发**：参考 `examples/ai_components/llm_reasoner_pattern.py`
  - 边界触发和成本控制
  - 异步调用和超时保护
  - 结构化输出解析

- **测试模式**：参考 `examples/testing_patterns/test_gate_pattern.py`
  - 完整测试覆盖策略
  - 性能和延迟验证
  - Mock 和 Fixture 使用

## DOCUMENTATION:

[列出开发过程中需要参考的文档、API 文档、MCP 服务器资源等]

### P1 系统文档：
- **架构文档**：`PROJECT_STRUCTURE.md` - 系统整体架构
- **v2 功能说明**：`docs/README_v2.md` - AI 增强功能详解
- **升级指南**：`docs/UPGRADE_TO_V2.md` - v1 到 v2 迁移
- **配置参考**：`configs/default.yaml` - 系统配置参数

### 外部文档：
- [FastAPI 文档](https://fastapi.tiangolo.com/) - API 开发框架
- [Pydantic 文档](https://docs.pydantic.dev/) - 数据验证和序列化
- [Pytest 文档](https://docs.pytest.org/) - 测试框架

### AI/ML 相关：
- FinGPT 模型文档 (如果使用本地 LLM)
- xLSTM 架构文档 (长序列建模)
- FinRL 环境文档 (强化学习训练)

## OTHER CONSIDERATIONS:

[其他考虑因素或特定要求 - 记录 AI 助手在您的项目中经常遗漏的问题]

### P1 系统特定要求：

#### 性能约束
- **延迟 SLA**: 所有决策 API 必须在 70ms 内响应
- **并发处理**: 支持多symbol同时决策，避免阻塞
- **内存管理**: 长序列模型的内存使用优化

#### 安全要求
- **输入验证**: 使用 Pydantic 严格验证所有数值边界
- **资金保护**: alloc_equity_pct 不得超过 5%
- **异常隔离**: 单个组件故障不能影响整个系统

#### AI 组件约束
- **LLM 成本控制**: 每日调用次数限制，优雅降级
- **边界触发**: LLM 仅在真正需要的边界情况下使用
- **可解释性**: 所有 AI 决策必须包含推理解释

#### 集成要求
- **微服务架构**: 保持 Decision/FeatureHub/Vision 服务分离
- **配置驱动**: 所有参数可通过 YAML 配置文件调整
- **向后兼容**: v2 功能不能破坏 v1 API 兼容性

#### 常见陷阱
- **忘记超时保护**: 所有外部调用 (LLM, API) 必须有超时
- **忽略成本控制**: LLM 调用要有频次限制和成本估算
- **缺少性能测试**: 关键路径必须有延迟性能测试
- **硬编码配置**: 避免硬编码阈值，使用配置文件
- **不完整的错误处理**: 网络故障、超时等异常情况处理

#### 开发工具链
- **使用 Black + Ruff**: 代码格式化和质量检查
- **类型注解**: 所有函数使用 Python 类型提示
- **结构化日志**: JSON 格式，包含 trade_id 和 runtime_ms
- **环境变量**: 使用 python-dotenv 管理配置

---

> ⚡ **提示**：填写完此模板后，在 Claude Code 中运行 `/generate-prp INITIAL.md` 生成详细实现计划，然后运行 `/execute-prp PRPs/your-feature.md` 自动实现功能！
