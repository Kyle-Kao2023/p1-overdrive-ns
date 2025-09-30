# Command: delegate-task

智能任务分发命令 - 根据任务类型自动选择最适合的 AI CLI 工具执行

## 用法:
```bash
/delegate-task "任务描述" [--agent gemini|codex|aider] [--output-format json|code|analysis]
```

## 分发逻辑:

### 自动分发规则
根据任务关键词自动选择 AI CLI：

**数据分析任务** → **Gemini-CLI**
- 关键词: "分析", "统计", "计算", "验证", "回测", "性能"
- 示例: "分析 ETHUSDT 波动率分布", "验证 P1 Gate 阈值有效性"

**代码生成任务** → **Codex-CLI**  
- 关键词: "实现", "生成", "创建", "集成", "API", "测试"
- 示例: "实现 Binance WebSocket 连接器", "生成 Gate 单元测试"

**代码重构任务** → **Aider**
- 关键词: "优化", "重构", "修复", "改进", "性能"
- 示例: "优化 LLM 推理器性能", "重构 Gate 验证逻辑"

**架构设计任务** → **Claude (本地)**
- 关键词: "设计", "架构", "流程", "策略", "文档"
- 示例: "设计新的 AI 增强架构", "编写技术文档"

## 执行步骤:

1. **任务分析**
   - 解析任务描述
   - 识别任务类型和复杂度
   - 确定最适合的 AI CLI

2. **上下文准备**
   - 收集相关的 P1 项目文件
   - 准备必要的配置和示例
   - 格式化输入数据

3. **CLI 调用**
   - 构建专业化的提示词
   - 调用选定的 AI CLI
   - 监控执行状态和超时

4. **结果整合**
   - 验证输出质量
   - 集成到 P1 项目结构
   - 更新相关文档

## P1 项目专用模板:

### Gemini 数据分析模板
```bash
gemini-cli --prompt "
作为 P1 Trading Builder 的量化分析师：

任务: $ARGUMENTS

上下文:
- P1 系统要求 <70ms 决策延迟
- 使用 Likert-7 方向编码
- Gate 系统包含 Vol/Consensus/LiqBuffer/Event
- 目标胜率 >75%

请提供:
1. 数据分析结果 (JSON 格式)
2. 统计验证 (置信区间, p-values)
3. P1 系统集成建议
4. 性能影响评估
" --format json --timeout 30
```

### Codex 代码生成模板
```bash
codex-cli --prompt "
作为 P1 Trading Builder 的代码实现专家：

任务: $ARGUMENTS

技术栈:
- Python 3.11+ / FastAPI / Pydantic
- 异步编程 (asyncio/aiohttp)
- 微服务架构 (Decision/FeatureHub/Vision)
- Redis 缓存 / PostgreSQL

代码要求:
1. 遵循 P1 架构模式 (参考 examples/)
2. 包含完整的类型注解
3. 异常处理和超时保护
4. 结构化日志记录
5. 单元测试覆盖

输出: 立即可运行的 Python 代码
" --style fastapi --timeout 20
```

## 🔄 工作流示例

### 使用示例 1: 数据分析
```bash
# Claude 自动分发给 Gemini
/delegate-task "分析 P1 系统在不同市场波动率下的决策准确性"

# 执行流程:
# 1. Claude 识别为数据分析任务
# 2. 准备 P1 历史决策数据
# 3. 调用 gemini-cli 进行统计分析
# 4. Claude 整合结果并提供 P1 优化建议
```

### 使用示例 2: 代码实现
```bash
# Claude 自动分发给 Codex
/delegate-task "实现基于 WebSocket 的实时订单流数据连接器"

# 执行流程:
# 1. Claude 识别为代码生成任务
# 2. 提供 P1 DataHub 架构上下文
# 3. 调用 codex-cli 生成连接器代码
# 4. Claude 集成到 P1 架构并添加测试
```

### 使用示例 3: 混合协作
```bash
# 复杂任务需要多 AI 协作
/delegate-task "优化 LLM Reasoner 的成本效益比"

# 执行流程:
# 1. Gemini: 分析当前 LLM 调用成本和效果数据
# 2. Claude: 设计成本优化策略 (缓存、批处理、边界调整)
# 3. Codex: 实现优化后的推理器代码
# 4. Claude: 整合测试并验证性能提升
```

---

> ⚡ **启用多 AI 协作**: 现在您的 P1 项目支持 Claude + Gemini + Codex 的专业分工协作，大幅提升开发效率和代码质量！
