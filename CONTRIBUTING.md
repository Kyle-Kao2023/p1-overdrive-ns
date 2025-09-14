# Contributing to P1 Trading Builder

首先，感谢您对P1 Trading Builder项目的贡献！

## 🚀 快速开始

1. Fork这个仓库
2. 创建您的功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交您的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建一个Pull Request

## 📋 开发规范

### 代码风格

我们使用以下工具确保代码质量：

```bash
# 格式化代码
black .
isort .

# 代码检查
ruff check .
mypy services/ adapters/

# 运行pre-commit钩子
pre-commit run --all-files
```

### 提交信息规范

使用以下格式提交代码：

```
type(scope): description

[optional body]

[optional footer]
```

类型包括：
- `feat`: 新功能
- `fix`: 修复bug
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建过程或辅助工具的变动

例如：
```
feat(gates): add volatility regime detection
fix(api): resolve timeout issues in decision endpoint
docs(readme): update installation instructions
```

## 🧪 测试要求

所有代码更改都需要相应的测试：

```bash
# 运行所有测试
pytest -v

# 运行特定测试文件
pytest tests/test_gates.py -v

# 检查测试覆盖率
pytest --cov=services --cov=adapters tests/
```

### 测试类型

1. **单元测试**: 测试单个函数/类
2. **集成测试**: 测试服务间交互
3. **API测试**: 测试HTTP endpoints
4. **性能测试**: 验证<70ms延迟SLA

## 🔧 开发环境设置

### 本地开发

```bash
# 创建虚拟环境
python3.11 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 安装pre-commit钩子
pre-commit install

# 启动开发服务器
./scripts/run_dev.sh
```

### Docker开发

```bash
# 构建并启动所有服务
docker-compose up --build

# 查看日志
docker-compose logs -f decision

# 运行测试
docker-compose exec decision pytest tests/ -v
```

## 📁 项目结构

```
p1-overdrive-ns/
├─ services/           # 微服务
│  ├─ decision/        # 核心决策服务
│  ├─ featurehub/      # 特征聚合服务
│  └─ vision/          # 视觉识别服务
├─ adapters/           # 外部平台适配器
├─ tests/              # 测试文件
├─ configs/            # 配置文件
└─ scripts/            # 工具脚本
```

## 🚪 Gate系统贡献指南

### 添加新Gate

1. 在 `services/decision/gates/` 创建新文件
2. 实现 `passes(features) -> Tuple[bool, str]` 接口
3. 在 `reasoner.py` 中集成
4. 添加对应测试

例如：
```python
def passes(features: Features) -> Tuple[bool, str]:
    """
    新Gate检查函数
    
    Returns:
        (是否通过, 说明信息)
    """
    # 实现检查逻辑
    pass
```

### Gate测试要求

每个Gate都需要测试：
- 通过场景
- 拒绝场景  
- 边界值测试
- 错误处理

## 🤖 模型集成指南

### 替换Stub模型

1. 保持现有接口不变
2. 在 `models/` 目录下实现真实模型
3. 更新相应的测试
4. 确保性能满足SLA要求

### 性能要求

- Decision API: < 70ms (p95)
- Exit API: < 50ms (p95)
- Gate检查: < 10ms each
- 模型推理: < 30ms

## 📊 监控和日志

### 日志规范

使用loguru进行日志记录：

```python
from loguru import logger

logger.info("Decision completed", extra={
    "symbol": symbol,
    "allow": decision.allow,
    "runtime_ms": runtime_ms
})
```

### 性能监控

添加性能监控：

```python
from services.decision.core.utils import timer, perf_monitor

with timer() as timing:
    # 执行代码
    pass

perf_monitor.record("operation_name", timing["duration_ms"])
```

## 🔒 安全要求

- 所有API输入都要验证
- 敏感配置使用环境变量
- 不要在代码中硬编码秘钥
- 添加适当的错误处理

## 📚 文档要求

### 代码文档

- 所有public函数需要docstring
- 复杂逻辑需要注释
- API更改需要更新OpenAPI文档

### README更新

当添加新功能时，请更新：
- 功能列表
- 使用示例
- 配置说明

## 🐛 Bug报告

请包含以下信息：
- 详细的重现步骤
- 期望的行为
- 实际的行为
- 环境信息
- 错误日志

## 💡 功能请求

请包含：
- 功能描述
- 使用场景
- 预期影响
- 实现复杂度估计

## 📞 获取帮助

- 📧 Email: support@p1trading.dev
- 💬 Discord: [P1 Trading Community](https://discord.gg/p1trading)
- 🐛 Issues: [GitHub Issues](https://github.com/user/p1-overdrive-ns/issues)

## 📄 许可证

通过贡献代码，您同意您的贡献将在MIT许可证下授权。

---

感谢您帮助我们改进P1 Trading Builder！🚀
