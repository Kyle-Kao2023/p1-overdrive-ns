"""
P1 Trading Builder - LLM Reasoner 实现模式示例
展示如何在 P1 系统中集成 LLM 推理器，处理边界情况决策
"""

import asyncio
import json
import time
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class ReasoningTrigger(Enum):
    """LLM 推理触发条件"""
    BORDERLINE_P_HIT = "borderline_p_hit"
    CONFLICTING_SIGNALS = "conflicting_signals"
    HIGH_NEWS_IMPACT = "high_news_impact"
    MANUAL_REQUEST = "manual_request"

@dataclass
class LLMReasoningResult:
    """LLM 推理结果的标准化输出格式"""
    rationale: str              # 人类可读的推理解释
    meta_tag: str              # 情况标签 (如 "fed-policy-crypto-short")
    c_llm: float               # LLM 置信度 [0, 1]
    triggered_by: ReasoningTrigger
    reasoning_time_ms: int
    raw_response: str          # 原始 LLM 响应 (调试用)

class LLMReasoner:
    """
    P1 LLM 推理器 - 仅在边界情况下启用，避免成本浪费
    
    核心设计原则：
    1. 边界条件触发 - 只在不确定时使用
    2. 超时保护 - 硬性 150ms 限制
    3. 成本控制 - 每日调用次数限制
    4. 结构化输出 - 标准化返回格式
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.timeout_ms = config.get("timeout_ms", 150)
        self.daily_call_limit = config.get("max_daily_calls", 100)
        self.borderline_range = config.get("borderline_range", [0.72, 0.78])
        self.call_count_today = 0  # 实际应该从 Redis 读取
        
    def should_trigger_llm(self, features: Dict[str, Any], pgm: Dict[str, Any]) -> Tuple[bool, Optional[ReasoningTrigger]]:
        """
        判断是否需要触发 LLM 推理
        
        P1 策略：只在真正需要人类式推理的边界情况下使用
        """
        
        # 成本控制检查
        if self.call_count_today >= self.daily_call_limit:
            return False, None
            
        p_hit = pgm.get("p_hit", 0)
        
        # 边界条件 1：命中率在边界范围
        if self.borderline_range[0] <= p_hit <= self.borderline_range[1]:
            return True, ReasoningTrigger.BORDERLINE_P_HIT
            
        # 边界条件 2：信号冲突 (TV vs OrderFlow 不一致)
        pine_signal = features.get("pine_match", True)
        c_of = features.get("C_of", 1.0)
        if pine_signal and c_of < 0.7:  # TradingView 看涨但订单流看跌
            return True, ReasoningTrigger.CONFLICTING_SIGNALS
            
        # 边界条件 3：重大新闻影响
        news = features.get("news", {})
        event_risk = news.get("event_risk", 0)
        if event_risk > 0.3:  # 高风险新闻事件
            return True, ReasoningTrigger.HIGH_NEWS_IMPACT
            
        return False, None
    
    async def reason(self, features: Dict[str, Any], pgm: Dict[str, Any], context: Dict[str, Any] = None) -> Optional[LLMReasoningResult]:
        """
        执行 LLM 推理
        
        Args:
            features: 市场特征
            pgm: PGM 预测结果
            context: 额外上下文 (当前市场状态、历史模式等)
            
        Returns:
            LLM 推理结果或 None (如果不需要推理)
        """
        
        should_trigger, trigger_reason = self.should_trigger_llm(features, pgm)
        if not should_trigger:
            return None
            
        start_time = time.time()
        
        try:
            # 构建 LLM 提示词
            prompt = self._build_reasoning_prompt(features, pgm, context, trigger_reason)
            
            # 调用 LLM (带超时保护)
            raw_response = await asyncio.wait_for(
                self._call_llm_api(prompt),
                timeout=self.timeout_ms / 1000
            )
            
            # 解析结构化输出
            reasoning_result = self._parse_llm_response(raw_response, trigger_reason)
            reasoning_result.reasoning_time_ms = int((time.time() - start_time) * 1000)
            
            self.call_count_today += 1
            return reasoning_result
            
        except asyncio.TimeoutError:
            logger.warning(f"LLM reasoning timeout after {self.timeout_ms}ms")
            return self._fallback_reasoning(trigger_reason)
        except Exception as e:
            logger.error(f"LLM reasoning error: {e}")
            return self._fallback_reasoning(trigger_reason)
    
    def _build_reasoning_prompt(self, features: Dict[str, Any], pgm: Dict[str, Any], 
                               context: Dict[str, Any], trigger: ReasoningTrigger) -> str:
        """构建针对 P1 交易系统优化的 LLM 提示词"""
        
        symbol = features.get("symbol", "UNKNOWN")
        side_hint = features.get("side_hint", "unknown")
        p_hit = pgm.get("p_hit", 0)
        
        direction = features.get("direction", {})
        news = features.get("news", {})
        
        prompt = f"""
你是一个专业的加密货币交易分析师，正在协助 P1 Overdrive-NS 系统做出交易决策。

当前情况：
- 交易对: {symbol}
- 建议方向: {side_hint}
- 系统预测胜率: {p_hit:.2f} (边界值！)
- 触发原因: {trigger.value}

技术分析：
- HTF方向: {direction.get('dir_htf', 'N/A')} (评分: {direction.get('dir_score_htf', 'N/A')})
- LTF方向: {direction.get('dir_ltf', 'N/A')} (评分: {direction.get('dir_score_ltf', 'N/A')})
- 微观方向: {direction.get('dir_micro', 'N/A')} (评分: {direction.get('dir_score_micro', 'N/A')})

市场情绪：
- 新闻情绪: {news.get('sentiment_score', 'N/A')}
- 事件风险: {news.get('event_risk', 'N/A')}
- 头条摘要: {news.get('headline_summary', 'N/A')}

任务：基于当前边界情况，提供人类式交易推理。

请以 JSON 格式回复：
{{
    "rationale": "简洁的推理解释 (≤100字)",
    "meta_tag": "情况标签 (如 fed-policy-crypto-short)",
    "confidence": 0.68,
    "risk_factors": ["factor1", "factor2"],
    "opportunity_score": 0.75
}}
"""
        return prompt.strip()
    
    async def _call_llm_api(self, prompt: str) -> str:
        """
        调用 LLM API (这里是示例实现)
        实际实现应该调用 FinGPT 或其他金融 LLM
        """
        # 模拟 LLM API 调用
        await asyncio.sleep(0.1)  # 模拟网络延迟
        
        # 示例响应
        mock_response = {
            "rationale": "HTF/LTF 空头一致性配合美联储鹰派情绪，创造高概率空头设置",
            "meta_tag": "fed-policy-crypto-short", 
            "confidence": 0.68,
            "risk_factors": ["fed_policy_uncertainty", "crypto_correlation"],
            "opportunity_score": 0.72
        }
        
        return json.dumps(mock_response)
    
    def _parse_llm_response(self, raw_response: str, trigger: ReasoningTrigger) -> LLMReasoningResult:
        """解析 LLM 响应为标准化格式"""
        try:
            data = json.loads(raw_response)
            
            return LLMReasoningResult(
                rationale=data.get("rationale", "未提供推理"),
                meta_tag=data.get("meta_tag", "unknown"),
                c_llm=data.get("confidence", 0.5),
                triggered_by=trigger,
                reasoning_time_ms=0,  # 将在 reason() 方法中设置
                raw_response=raw_response
            )
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return self._fallback_reasoning(trigger)
    
    def _fallback_reasoning(self, trigger: ReasoningTrigger) -> LLMReasoningResult:
        """LLM 失败时的后备推理"""
        return LLMReasoningResult(
            rationale="LLM 推理不可用，使用保守策略",
            meta_tag="llm-fallback", 
            c_llm=0.3,
            triggered_by=trigger,
            reasoning_time_ms=0,
            raw_response=""
        )

# 使用示例
async def example_usage():
    """演示 LLM Reasoner 在 P1 系统中的使用"""
    
    config = {
        "timeout_ms": 150,
        "max_daily_calls": 100,
        "borderline_range": [0.72, 0.78]
    }
    
    reasoner = LLMReasoner(config)
    
    # 边界情况的市场特征
    features = {
        "symbol": "ETHUSDT",
        "side_hint": "short",
        "direction": {
            "dir_score_htf": -0.75,
            "dir_htf": -2,
            "dir_score_ltf": -0.65, 
            "dir_ltf": -2
        },
        "news": {
            "sentiment_score": -0.3,
            "event_risk": 0.15,
            "headline_summary": "Fed hawkish signals concern crypto markets"
        }
    }
    
    pgm = {"p_hit": 0.74}  # 边界值，将触发 LLM
    
    # 执行推理
    result = await reasoner.reason(features, pgm)
    
    if result:
        print(f"🤖 LLM 推理结果:")
        print(f"  推理: {result.rationale}")
        print(f"  标签: {result.meta_tag}")
        print(f"  置信度: {result.c_llm:.2f}")
        print(f"  耗时: {result.reasoning_time_ms}ms")
    else:
        print("⚡ 无需 LLM 推理，使用传统决策")

if __name__ == "__main__":
    asyncio.run(example_usage())
