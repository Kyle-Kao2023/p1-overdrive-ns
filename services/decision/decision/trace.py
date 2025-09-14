"""推理链生成和追踪模块"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from loguru import logger

from ..schemas.features import EnterRequest, Features
from ..schemas.responses import EnterResponse


class ReasoningTrace:
    """推理过程追踪器"""
    
    def __init__(self, request_id: str = None):
        self.request_id = request_id or f"req_{int(datetime.utcnow().timestamp())}"
        self.steps: List[Dict[str, Any]] = []
        self.start_time = datetime.utcnow()
    
    def add_step(self, step_name: str, result: Any, details: Dict = None) -> None:
        """添加推理步骤"""
        step = {
            "step": step_name,
            "timestamp": datetime.utcnow(),
            "result": result,
            "details": details or {}
        }
        self.steps.append(step)
        logger.debug(f"Trace {self.request_id}: {step_name} -> {result}")
    
    def add_gate_check(self, gate_name: str, passed: bool, message: str, details: Dict = None) -> None:
        """添加Gate检查记录"""
        self.add_step(
            f"Gate_{gate_name}",
            "PASS" if passed else "FAIL",
            {"message": message, "gate_details": details or {}}
        )
    
    def add_model_prediction(self, model_name: str, prediction: Any, confidence: float = None) -> None:
        """添加模型预测记录"""
        self.add_step(
            f"Model_{model_name}",
            prediction,
            {"confidence": confidence}
        )
    
    def add_decision(self, decision: EnterResponse) -> None:
        """添加最终决策"""
        self.add_step(
            "Final_Decision",
            "ALLOW" if decision.allow else "DENY",
            {
                "side": decision.side,
                "allocation": decision.alloc_equity_pct,
                "reason_chain": decision.reason_chain
            }
        )
    
    def get_summary(self) -> Dict[str, Any]:
        """获取推理摘要"""
        end_time = datetime.utcnow()
        duration_ms = int((end_time - self.start_time).total_seconds() * 1000)
        
        gate_results = [s for s in self.steps if s["step"].startswith("Gate_")]
        model_results = [s for s in self.steps if s["step"].startswith("Model_")]
        
        return {
            "request_id": self.request_id,
            "start_time": self.start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_ms": duration_ms,
            "total_steps": len(self.steps),
            "gates_passed": sum(1 for g in gate_results if g["result"] == "PASS"),
            "gates_total": len(gate_results),
            "models_used": len(model_results),
            "final_decision": self.steps[-1]["result"] if self.steps else None
        }
    
    def get_detailed_trace(self) -> Dict[str, Any]:
        """获取详细追踪信息"""
        return {
            "summary": self.get_summary(),
            "steps": self.steps
        }
    
    def export_for_audit(self) -> str:
        """导出审计格式"""
        lines = [f"Reasoning Trace: {self.request_id}"]
        lines.append(f"Start: {self.start_time.isoformat()}")
        lines.append("=" * 50)
        
        for i, step in enumerate(self.steps, 1):
            lines.append(f"{i:2d}. {step['step']}: {step['result']}")
            if step.get("details", {}).get("message"):
                lines.append(f"    -> {step['details']['message']}")
        
        lines.append("=" * 50)
        summary = self.get_summary()
        lines.append(f"Duration: {summary['duration_ms']}ms")
        lines.append(f"Gates: {summary['gates_passed']}/{summary['gates_total']}")
        lines.append(f"Final: {summary['final_decision']}")
        
        return "\n".join(lines)


def create_feature_summary(features: Features) -> Dict[str, str]:
    """创建特征摘要用于追踪"""
    return {
        "volatility": f"σ={features.sigma_1m:.4f}, skew={features.skew_1m:.2f}",
        "multi_timeframe": f"Z4H={features.Z_4H:.2f}, Z1H={features.Z_1H:.2f}, Z15m={features.Z_15m:.2f}",
        "consensus": f"C_align={features.C_align:.2f}, C_of={features.C_of:.2f}, C_vision={features.C_vision:.2f}",
        "orderflow": f"OBI={features.OF.obi:.2f}, dCVD={features.OF.dCVD:.2f}, replenish={features.OF.replenish:.2f}",
        "market": f"spread={features.market.spread_bp}bp, depth={features.market.depth_px:,.0f}",
        "onchain": f"OI_ROC={features.onchain.oi_roc:.3f}, gas_z={features.onchain.gas_z:.2f}"
    }


def generate_human_readable_reasoning(request: EnterRequest, response: EnterResponse, trace: ReasoningTrace = None) -> str:
    """生成人类可读的推理说明"""
    lines = []
    
    # 标题
    lines.append(f"🤖 Trading Decision for {request.symbol} ({request.side_hint.upper()})")
    lines.append(f"📅 {request.ts.strftime('%Y-%m-%d %H:%M:%S UTC')} | ⚡ {response.runtime_ms}ms")
    lines.append("")
    
    # 决策结果
    if response.allow:
        lines.append(f"✅ **APPROVED** - {response.side.upper()} position")
        lines.append(f"💰 Allocation: {response.alloc_equity_pct:.1%} of equity")
        if response.exec:
            lines.append(f"🎯 Execution: {response.exec.type}")
    else:
        lines.append(f"❌ **REJECTED**")
    
    lines.append("")
    
    # 市场条件
    lines.append("📊 **Market Conditions:**")
    feature_summary = create_feature_summary(request.features)
    for category, summary in feature_summary.items():
        lines.append(f"  • {category.title()}: {summary}")
    
    lines.append("")
    
    # 推理过程
    lines.append("🧠 **Reasoning Chain:**")
    for i, reason in enumerate(response.reason_chain, 1):
        emoji = "✓" if not reason.startswith("✗") and not "FAIL" in reason else "✗"
        lines.append(f"  {i}. {emoji} {reason}")
    
    # 风险评估
    if response.risk:
        lines.append("")
        lines.append("⚠️  **Risk Assessment:**")
        lines.append(f"  • Liquidation Buffer: {response.risk.liq_buffer_pct:.2%}")
        lines.append(f"  • Risk Budget: {response.risk.lhs_pct:.2%}")
        lines.append(f"  • Safety Margin: {(response.risk.liq_buffer_pct - response.risk.lhs_pct):.2%}")
    
    # 追踪摘要
    if trace:
        summary = trace.get_summary()
        lines.append("")
        lines.append("🔍 **Decision Process:**")
        lines.append(f"  • Total Steps: {summary['total_steps']}")
        lines.append(f"  • Gates Passed: {summary['gates_passed']}/{summary['gates_total']}")
        lines.append(f"  • Processing Time: {summary['duration_ms']}ms")
    
    return "\n".join(lines)


def analyze_decision_patterns(traces: List[ReasoningTrace]) -> Dict[str, Any]:
    """分析决策模式，用于系统监控"""
    if not traces:
        return {}
    
    # 统计基础信息
    total_decisions = len(traces)
    approved_decisions = sum(1 for t in traces if t.steps and t.steps[-1]["result"] == "ALLOW")
    
    # 性能统计
    durations = [s["duration_ms"] for s in [t.get_summary() for t in traces]]
    avg_duration = sum(durations) / len(durations) if durations else 0
    
    # Gate通过率
    gate_stats = {}
    for trace in traces:
        for step in trace.steps:
            if step["step"].startswith("Gate_"):
                gate_name = step["step"].replace("Gate_", "")
                if gate_name not in gate_stats:
                    gate_stats[gate_name] = {"total": 0, "passed": 0}
                gate_stats[gate_name]["total"] += 1
                if step["result"] == "PASS":
                    gate_stats[gate_name]["passed"] += 1
    
    # 计算通过率
    gate_pass_rates = {
        name: stats["passed"] / stats["total"] if stats["total"] > 0 else 0
        for name, stats in gate_stats.items()
    }
    
    return {
        "total_decisions": total_decisions,
        "approval_rate": approved_decisions / total_decisions if total_decisions > 0 else 0,
        "avg_processing_time_ms": avg_duration,
        "gate_pass_rates": gate_pass_rates,
        "performance_percentiles": {
            "p50_ms": sorted(durations)[len(durations)//2] if durations else 0,
            "p95_ms": sorted(durations)[int(len(durations)*0.95)] if durations else 0,
            "p99_ms": sorted(durations)[int(len(durations)*0.99)] if durations else 0
        }
    }


# 全局追踪存储（生产环境中应使用数据库）
_global_traces: List[ReasoningTrace] = []


def store_trace(trace: ReasoningTrace) -> None:
    """存储推理追踪"""
    global _global_traces
    _global_traces.append(trace)
    
    # 保持最近1000条记录
    if len(_global_traces) > 1000:
        _global_traces = _global_traces[-1000:]


def get_recent_patterns() -> Dict[str, Any]:
    """获取最近的决策模式分析"""
    recent_traces = _global_traces[-100:]  # 最近100条
    return analyze_decision_patterns(recent_traces)
