# Command: analyze-data

专门调用 Gemini-CLI 进行 P1 Trading Builder 的数据分析任务

## 用法:
```bash
/analyze-data "数据分析需求描述" [数据文件路径]
```

## 功能说明:

这个命令自动将数据分析任务委托给 Gemini-CLI，专门处理 P1 交易系统的量化分析需求。

## 执行步骤:

1. **任务预处理**
   - 读取相关的 P1 配置参数 (configs/default.yaml)
   - 检查是否需要历史数据或实时数据
   - 准备 P1 系统的上下文信息

2. **调用 Gemini-CLI**
```bash
gemini-cli --prompt "
作为 P1 Overdrive-NS 交易系统的高级量化分析师：

分析任务: $ARGUMENTS

P1 系统背景:
- 高频交易系统，要求 <70ms 决策延迟
- 4-Gate 安全系统: Vol/Consensus/LiqBuffer/Event  
- v2 AI 增强: LLM Reasoner + xLSTM + Learner/Trainer
- 目标: 75%+ 胜率的 A+ 段落交易

关键参数:
- sigma_1m 波动率甜蜜点: bull [0.0012, 0.0022], bear [0.0015, 0.0028]
- p_hit_min: 0.75 (最小胜率要求)
- LLM 触发边界: [0.72, 0.78]
- alloc_equity_pct 上限: 5%

请提供:
1. 📊 数据分析结果 (具体数值 + 统计显著性)
2. 🎯 对 P1 系统的具体建议 (参数优化/阈值调整)
3. ⚠️ 风险评估 (对交易性能的潜在影响)
4. 📈 预期改进效果 (量化的性能提升预测)

输出格式: JSON + 图表说明
" --format json --timeout 30 --model gemini-1.5-pro
```

3. **结果验证与集成**
   - 验证 Gemini 分析结果的合理性
   - 将分析建议转换为 P1 系统的具体配置更改
   - 生成对应的代码修改建议
   - 更新相关文档

## P1 专用分析场景:

### 市场数据分析
```bash
/analyze-data "分析不同加密货币的波动率模式，优化 Vol Gate 参数"
```

### 性能优化分析  
```bash
/analyze-data "分析 P1 决策延迟分布，识别性能瓶颈"
```

### AI 模型效果评估
```bash  
/analyze-data "评估 LLM Reasoner 在边界情况下的决策改进效果"
```

### 风险模型验证
```bash
/analyze-data "验证当前 Gate 阈值的统计有效性和误报率"
```

## 输出示例:

Gemini 分析完成后，Claude 会整合结果并提供：
- 📊 **数据洞察**: 关键发现和统计结论
- 🔧 **P1 配置建议**: 具体的参数调整方案  
- 💡 **实现建议**: 如何在 P1 代码中应用分析结果
- 📋 **后续行动**: 推荐的开发任务和验证步骤
