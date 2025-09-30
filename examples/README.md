# P1 Trading Builder - 代码示例库

这个目录包含 P1 Overdrive-NS 系统的核心开发模式示例，用于指导 AI 编程助手理解项目架构和编码规范。

## 📁 目录结构

### `decision_patterns/`
展示 P1 决策系统的核心模式：

- **`gate_implementation.py`** - Gate 安全门的实现模式
  - 抽象基类设计
  - 标准化日志记录
  - 配置驱动的验证逻辑
  - 错误处理和后备机制

### `ai_components/`
展示 P1 v2 AI 增强组件的实现模式：

- **`llm_reasoner_pattern.py`** - LLM 推理器集成模式
  - 边界条件触发逻辑
  - 超时保护和成本控制
  - 结构化输出解析
  - 异步调用模式

### `testing_patterns/`
展示 P1 系统的测试最佳实践：

- **`test_gate_pattern.py`** - Gate 组件测试模式
  - 完整的测试覆盖 (正常/边界/异常)
  - 性能测试 (延迟 SLA 验证)
  - Mock 和 Fixture 使用
  - 日志验证

## 🎯 使用指南

### 为 AI 助手提供示例

当请求 AI 助手开发新功能时，引用相关示例：

```markdown
## EXAMPLES:

参考 `examples/decision_patterns/gate_implementation.py` 的 Gate 实现模式：
- 继承 BaseGate 抽象类
- 实现 passes() 方法返回 (bool, str) 元组
- 使用标准化的日志记录格式
- 包含配置驱动的验证逻辑

参考 `examples/testing_patterns/test_gate_pattern.py` 的测试模式：
- 使用 pytest fixtures 管理测试数据
- 包含正常/边界/异常情况测试
- 验证延迟性能要求 (<70ms)
- Mock 外部依赖和 API 调用
```

### 开发新组件时

1. **Gate 开发**：遵循 `gate_implementation.py` 的模式
2. **AI 组件开发**：遵循 `llm_reasoner_pattern.py` 的模式  
3. **测试编写**：遵循 `test_gate_pattern.py` 的覆盖策略
4. **API 开发**：保持 FastAPI + Pydantic 验证模式

## 🔧 P1 特定约定

### 延迟要求
所有决策组件必须满足 **< 70ms** 的延迟要求：
```python
@pytest.mark.performance
def test_component_latency():
    start = time.time()
    result = component.process(data)
    runtime_ms = (time.time() - start) * 1000
    assert runtime_ms < 70
```

### 错误处理
使用统一的错误处理模式：
```python
try:
    result = risky_operation()
    return success_response(result)
except SpecificError as e:
    logger.error(f"Component failed: {e}", extra={"context": data})
    return fallback_response()
```

### 配置管理
所有组件使用配置驱动：
```python
class Component:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.threshold = config.get("threshold", default_value)
```

## 📊 数据格式标准

### 特征向量格式
```python
features = {
    "symbol": "ETHUSDT",
    "side_hint": "short|long", 
    "sigma_1m": float,          # 1分钟波动率
    "Z_4H": float,              # Z-score 4小时
    "C_align": float,           # 多时间框架一致性 [0,1]
    "direction": {              # v2: Likert-7 编码
        "dir_score_htf": float, # 连续评分 [-1,1]
        "dir_htf": int,         # Likert标签 [-3,+3]
    },
    "news": {                   # v2: 新闻分析
        "sentiment_score": float,
        "event_risk": float
    }
}
```

### 决策响应格式
```python
decision = {
    "allow": bool,
    "side": "short|long|none",
    "alloc_equity_pct": float,  # [0, 0.05] 最大5%
    "reason_chain": str,        # Gate通过链
    "runtime_ms": int,
    "llm_reasoning": {          # v2: LLM推理结果
        "rationale": str,
        "meta_tag": str,
        "c_llm": float
    }
}
```

---

> 💡 **提示**：在开发新功能时，优先参考这些示例确保代码风格和架构一致性。AI 助手会根据这些模式生成更符合 P1 项目标准的代码。
