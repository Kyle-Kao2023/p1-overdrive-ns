# Command: generate-code

专门调用 Codex-CLI 进行 P1 Trading Builder 的代码生成任务

## 用法:
```bash
/generate-code "代码生成需求描述" [--type api|gate|connector|test]
```

## 功能说明:

这个命令自动将代码生成任务委托给 Codex-CLI，专门处理 P1 交易系统的快速开发需求。

## 执行步骤:

1. **任务预处理**
   - 分析代码生成类型 (API/Gate/Connector/Test)
   - 读取 P1 项目的代码模式 (examples/ 目录)
   - 准备相关的架构上下文

2. **调用 Codex-CLI**
```bash
codex-cli --prompt "
作为 P1 Overdrive-NS 交易系统的资深 Python 开发工程师：

开发任务: $ARGUMENTS

P1 技术栈:
- Python 3.11+ / FastAPI / Pydantic
- 异步编程: asyncio, aiohttp, asyncpg
- 微服务架构: Decision(8000) / FeatureHub(8010) / Vision(8020)
- 数据: Redis 缓存 / PostgreSQL / WebSocket 实时流

P1 架构要求:
- 📁 文件结构: 遵循 services/{service_name}/ 模式
- ⚡ 性能: 所有决策 API <70ms 延迟
- 🛡️ 安全: 4-Gate 验证 + 输入边界检查
- 📊 日志: 结构化 JSON + trade_id + runtime_ms
- 🧪 测试: pytest + 完整覆盖 (正常/边界/异常)

代码模式参考:
- Gate 实现: 继承 BaseGate，实现 passes() 方法
- API 路由: FastAPI + Pydantic 验证 + 异常处理
- 连接器: 异步 WebSocket + 重连逻辑 + 错误隔离
- 测试: pytest fixtures + Mock + 性能验证

必需组件:
1. 类型注解 (完整的 typing 支持)
2. 异常处理 (try/except + 日志记录)
3. 配置驱动 (从 configs/default.yaml 读取)
4. 文档字符串 (详细的 docstring)
5. 单元测试 (pytest + 边界测试)

输出要求: 立即可运行的 Python 代码 + 完整测试
" --style python --framework fastapi --timeout 20
```

3. **代码集成与优化**
   - 验证生成代码的 P1 架构兼容性
   - 集成到现有微服务结构
   - 运行测试并修复问题
   - 更新 API 文档

## P1 专用代码生成场景:

### API 端点开发
```bash
/generate-code "为 Decision 服务创建新的风险评估 API 端点" --type api
```

### Gate 组件开发
```bash
/generate-code "实现基于社交媒体情绪的 SentimentGate" --type gate
```

### 数据连接器开发
```bash
/generate-code "创建 Coinbase WebSocket 实时价格连接器" --type connector
```

### 测试套件生成
```bash
/generate-code "为 LLM Reasoner 模块生成完整的测试套件" --type test
```

## 代码生成模板:

### Gate 组件模板
```python
# Codex 会基于此模式生成新 Gate
class {GateName}Gate(BaseGate):
    def passes(self, features: Dict[str, Any]) -> Tuple[bool, str]:
        # 验证逻辑
        # 配置驱动的参数
        # 边界检查
        # 日志记录
        return passed, reason
```

### API 端点模板
```python
# Codex 会基于此模式生成新 API
@router.post("/v2/{endpoint}")
async def endpoint_handler(request: RequestModel) -> ResponseModel:
    # 输入验证
    # 业务逻辑
    # 异常处理  
    # 性能监控
    return response
```

### 连接器模板
```python
# Codex 会基于此模式生成新连接器
class {Exchange}Connector:
    async def connect(self) -> None:
        # WebSocket 连接
        # 重连逻辑
        # 错误处理
        
    async def on_message(self, data: dict) -> None:
        # 数据解析
        # 格式标准化
        # 实时推送
```

## 输出处理:

Codex 生成完成后，Claude 会自动：
- 🔍 **代码审查**: 检查 P1 架构兼容性
- 🧪 **测试验证**: 运行生成的测试确保质量
- 📝 **文档更新**: 更新 API 文档和使用说明
- 🚀 **部署准备**: 更新 Docker 配置和环境变量

## 质量保证:

- ✅ **即时可运行**: 生成的代码无需修改即可运行
- ✅ **完整测试**: 包含单元测试和集成测试
- ✅ **性能合规**: 满足 P1 的 <70ms 延迟要求
- ✅ **安全标准**: 包含输入验证和错误处理
- ✅ **架构一致**: 符合 P1 微服务架构模式
