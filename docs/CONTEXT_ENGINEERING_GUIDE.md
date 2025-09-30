# P1 Trading Builder - Context Engineering 使用指南

## 🎯 概述

Context Engineering 已集成到 P1 Overdrive-NS 系统中，专门优化 AI 增强交易系统的开发流程。通过标准化的上下文工程，确保 AI 助手能够高质量地协助复杂金融系统的开发。

## 🚀 快速开始

### 1. 检查集成状态

项目中现在包含以下 Context Engineering 组件：

```
P1_Trading_Builder/
├── .claude/                    # Claude Code 自定义命令
│   ├── commands/
│   │   ├── generate-prp.md    # 生成产品需求提示
│   │   └── execute-prp.md     # 执行实现计划
│   └── settings.local.json    # Claude 权限设置
├── CLAUDE.md                  # P1 项目 AI 助手规则
├── INITIAL.md                 # 功能开发模板
├── PRPs/                      # 产品需求提示库
│   └── templates/
│       └── prp_p1_base.md    # P1 专用 PRP 模板
├── examples/                  # P1 代码示例库
│   ├── decision_patterns/     # 决策系统模式
│   ├── ai_components/         # AI 组件模式
│   └── testing_patterns/      # 测试模式
└── tools/context-engineering/ # 原始模板 (参考用)
```

### 2. 开发新功能的标准流程

```bash
# 步骤 1: 编辑功能需求
# 编辑 INITIAL.md，描述要开发的功能

# 步骤 2: 生成详细实现计划
# 在 Claude Code 中运行:
/generate-prp INITIAL.md

# 步骤 3: 自动实现功能
# 在 Claude Code 中运行:
/execute-prp PRPs/your-feature-name.md
```

## 🔧 P1 专用配置

### AI 助手规则 (CLAUDE.md)

已针对 P1 系统定制的关键规则：

- **🏗️ 微服务架构**：保持 Decision/FeatureHub/Vision 三服务分离
- **⚡ 性能要求**：所有决策 < 70ms 延迟 SLA
- **🛡️ 安全约束**：4-Gate 系统 + 资金保护
- **🤖 AI 增强**：LLM 边界触发 + xLSTM 序列建模
- **📊 数据标准**：Likert-7 编码 + 结构化日志

### 示例代码库

#### 决策模式示例 (`examples/decision_patterns/`)
- **Gate 实现模式**：抽象基类 + 标准化验证逻辑
- **配置驱动设计**：YAML 配置 + 边界检查
- **日志记录标准**：结构化日志 + 性能追踪

#### AI 组件示例 (`examples/ai_components/`)
- **LLM 推理器模式**：边界触发 + 超时保护
- **成本控制策略**：调用次数限制 + 优雅降级
- **结构化输出**：标准化 rationale + meta_tag

#### 测试模式示例 (`examples/testing_patterns/`)
- **完整测试覆盖**：正常/边界/异常情况
- **性能验证**：延迟 SLA + 负载测试
- **AI 组件测试**：Mock LLM + 集成测试

## 📋 开发最佳实践

### 功能开发检查清单

#### ✅ 开发前准备
- [ ] 阅读 `PROJECT_STRUCTURE.md` 了解架构
- [ ] 检查 `examples/` 相关模式
- [ ] 确认性能和安全要求

#### ✅ 实现阶段
- [ ] 遵循 Gate/AI 组件设计模式
- [ ] 使用配置驱动的参数管理
- [ ] 实现完整的错误处理
- [ ] 添加结构化日志记录

#### ✅ 测试阶段
- [ ] 单元测试覆盖 (正常/边界/异常)
- [ ] 性能测试验证延迟 SLA
- [ ] 集成测试确保兼容性
- [ ] AI 组件的 Mock 测试

#### ✅ 部署准备
- [ ] 更新 Docker 配置
- [ ] 添加监控指标
- [ ] 准备回滚方案

### 常见问题与解决方案

#### Q: 如何确保新 Gate 符合 P1 标准？
```python
# 参考 examples/decision_patterns/gate_implementation.py
class YourGate(BaseGate):
    def passes(self, features) -> Tuple[bool, str]:
        # 实现验证逻辑
        return True, "reason"
```

#### Q: 如何集成 LLM 推理器？
```python
# 参考 examples/ai_components/llm_reasoner_pattern.py
# 只在边界情况触发，避免成本浪费
if should_trigger_llm(features, pgm):
    result = await llm_reasoner.reason(features, pgm)
```

#### Q: 如何保证延迟 SLA？
```python
# 参考 examples/testing_patterns/test_gate_pattern.py
@pytest.mark.performance
def test_latency():
    start = time.time()
    result = component.process(data)
    assert (time.time() - start) * 1000 < 70
```

## 🎨 自定义命令

### /generate-prp 命令
生成针对 P1 系统优化的详细实现计划：
- 分析现有代码模式
- 搜索相关文档和 API
- 创建分步骤实现计划
- 包含性能和安全验证

### /execute-prp 命令  
自动执行实现计划：
- 加载完整上下文
- 按步骤实现功能
- 运行测试和验证
- 确保满足 P1 标准

## 📈 成功指标

### 开发效率提升
- **需求理解准确性**: AI 助手理解复杂金融需求
- **代码质量一致性**: 符合 P1 架构和编码标准
- **开发速度**: 复杂功能实现时间显著减少

### 系统质量提升  
- **性能合规**: 新功能满足 < 70ms 延迟要求
- **安全性**: 所有新组件通过 4-Gate 安全验证
- **可维护性**: 代码结构清晰，文档完整

### AI 增强效果
- **推理质量**: LLM 决策解释清晰有用
- **成本控制**: LLM 调用在预算范围内
- **学习效果**: 系统在实际交易中持续改进

## 🔗 相关资源

- **原始模板**: [coleam00/context-engineering-intro](https://github.com/coleam00/context-engineering-intro.git)
- **P1 项目文档**: `docs/README_v2.md`
- **架构说明**: `PROJECT_STRUCTURE.md`
- **配置参考**: `configs/default.yaml`

---

> 🎯 **目标达成**：通过 Context Engineering，P1 Trading Builder 现在具备了工业级的 AI 协作开发能力，确保高质量、高性能的金融交易系统开发。
