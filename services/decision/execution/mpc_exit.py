"""动态退出策略 - MPC Exit"""
import time
from typing import Dict, List

from loguru import logger

from ..core.config import config_manager
from ..schemas.features import ExitRequest
from ..schemas.responses import ExitResponse


def analyze_exit_signals(exit_request: ExitRequest, config: Dict) -> Dict[str, float]:
    """分析退出信号强度"""
    position = exit_request.position
    updates = exit_request.updates
    
    signals = {}
    
    # 1. Hazard信号
    hazard_thresh = config.get("hazard_thresh", 0.30)
    signals["hazard_strength"] = updates.h_t / hazard_thresh if hazard_thresh > 0 else 0
    
    # 2. P_hit衰减信号
    phit_floor = config.get("phit_floor", 0.50)
    if updates.p_hit < phit_floor:
        signals["phit_decay"] = (phit_floor - updates.p_hit) / phit_floor
    else:
        signals["phit_decay"] = 0.0
    
    # 3. 时间信号 (如果有时间限制的话)
    signals["timing_pressure"] = max(0, (updates.t_hit_q50_bars - 10) / 20)  # 超过10根K线开始有压力
    
    # 4. OrderFlow反转信号
    if position.side == "long":
        # 多头位置，dCVD变负为不利
        of_flip = max(0, -updates.dCVD / 2.0)  # dCVD越负，信号越强
    else:
        # 空头位置，dCVD变正为不利
        of_flip = max(0, updates.dCVD / 2.0)  # dCVD越正，信号越强
    
    signals["orderflow_flip"] = of_flip
    
    # 5. 补单率下降信号
    replenish_decline = max(0, (0.6 - updates.replenish) / 0.6)  # 补单率低于60%开始有信号
    signals["replenish_decline"] = replenish_decline
    
    return signals


def compute_exit_urgency(signals: Dict[str, float]) -> float:
    """计算退出紧急度"""
    weights = {
        "hazard_strength": 0.35,
        "phit_decay": 0.25,
        "orderflow_flip": 0.20,
        "replenish_decline": 0.10,
        "timing_pressure": 0.10
    }
    
    urgency = sum(
        weights.get(signal, 0) * strength 
        for signal, strength in signals.items()
    )
    
    return min(urgency, 1.0)


def determine_exit_action(exit_request: ExitRequest, urgency: float, config: Dict) -> tuple:
    """
    确定退出动作
    
    Returns:
        (action, reduce_pct, reasons)
    """
    position = exit_request.position
    updates = exit_request.updates
    
    reasons = []
    
    # 获取配置
    hazard_thresh = config.get("hazard_thresh", 0.30)
    phit_floor = config.get("phit_floor", 0.50)
    grace_bars = config.get("t_hit_grace_bars", 3)
    default_reduce_pct = config.get("reduce_pct", 0.5)
    
    # 强制平仓条件
    if updates.h_t > hazard_thresh * 1.5:  # Hazard超过1.5倍阈值
        reasons.append(f"Critical hazard {updates.h_t:.3f} > {hazard_thresh*1.5:.3f}")
        return "close", 1.0, reasons
    
    if updates.p_hit < phit_floor * 0.6:  # P_hit低于60%的floor
        reasons.append(f"Critical p_hit {updates.p_hit:.3f} < {phit_floor*0.6:.3f}")
        return "close", 1.0, reasons
    
    # 减仓条件
    if updates.h_t > hazard_thresh:
        reasons.append(f"hazard {updates.h_t:.3f} > {hazard_thresh}")
        reduce_pct = min(default_reduce_pct * (1 + urgency), 0.8)  # 最多减仓80%
        return "reduce", reduce_pct, reasons
    
    if updates.p_hit < phit_floor:
        reasons.append(f"p_hit {updates.p_hit:.3f} < {phit_floor}")
        reduce_pct = default_reduce_pct
        return "reduce", reduce_pct, reasons
    
    # OrderFlow反转
    if position.side == "long" and updates.dCVD < -1.5:
        reasons.append(f"of_flip: dCVD {updates.dCVD:.2f} (bearish for long)")
        return "reduce", default_reduce_pct * 0.7, reasons
    
    if position.side == "short" and updates.dCVD > 1.5:
        reasons.append(f"of_flip: dCVD {updates.dCVD:.2f} (bullish for short)")
        return "reduce", default_reduce_pct * 0.7, reasons
    
    # 时间超时风险 
    if updates.t_hit_q50_bars > grace_bars * 3:
        reasons.append(f"timeout_risk: t_hit {updates.t_hit_q50_bars} > {grace_bars*3}")
        return "reduce", default_reduce_pct * 0.5, reasons
    
    # 盈利保护（如果有盈利的话）
    if position.upl_pct > 0.5:  # 盈利超过50bp
        if updates.h_t > hazard_thresh * 0.7:  # 较低的hazard阈值用于盈利保护
            reasons.append(f"profit_protection: upl {position.upl_pct:.1%}, hazard {updates.h_t:.3f}")
            return "trail", default_reduce_pct * 0.3, reasons
    
    # 持有
    return "hold", None, ["All signals within acceptable range"]


def decide_exit(exit_request: ExitRequest, config: Dict = None) -> ExitResponse:
    """
    主退出决策函数
    
    Args:
        exit_request: 退出请求
        config: 配置字典，如果为None则使用全局配置
        
    Returns:
        ExitResponse
    """
    start_time = time.time()
    
    # 获取配置
    if config is None:
        config = config_manager.get_exit_config()
    
    try:
        # 1. 分析退出信号
        signals = analyze_exit_signals(exit_request, config)
        
        # 2. 计算紧急度
        urgency = compute_exit_urgency(signals)
        
        # 3. 确定动作
        action, reduce_pct, reasons = determine_exit_action(exit_request, urgency, config)
        
        # 4. 记录决策过程
        logger.info(
            f"Exit decision: {action}"
            f"{f' ({reduce_pct:.1%})' if reduce_pct else ''}"
            f" | Urgency: {urgency:.2f}"
            f" | H(t): {exit_request.updates.h_t:.3f}"
            f" | P_hit: {exit_request.updates.p_hit:.3f}"
        )
        
        # 5. 构建响应
        runtime_ms = int((time.time() - start_time) * 1000)
        
        return ExitResponse(
            action=action,
            reduce_pct=reduce_pct,
            reason=reasons,
            runtime_ms=runtime_ms
        )
        
    except Exception as e:
        logger.error(f"Error in exit decision: {e}")
        runtime_ms = int((time.time() - start_time) * 1000)
        
        # 出错时保守处理：减仓50%
        return ExitResponse(
            action="reduce",
            reduce_pct=0.5,
            reason=[f"Error in exit logic: {str(e)}", "Conservative reduce as fallback"],
            runtime_ms=runtime_ms
        )


def simulate_exit_scenarios(position_data: Dict, config: Dict = None) -> List[Dict]:
    """
    模拟不同退出场景，用于测试和验证
    
    Args:
        position_data: 基础持仓数据
        config: 退出配置
        
    Returns:
        List of scenario results
    """
    scenarios = [
        {"name": "Normal", "h_t": 0.15, "p_hit": 0.70, "dCVD": 0.2},
        {"name": "High Hazard", "h_t": 0.35, "p_hit": 0.65, "dCVD": 0.1},
        {"name": "Low P_hit", "h_t": 0.20, "p_hit": 0.45, "dCVD": 0.1},
        {"name": "OF Flip (Long)", "h_t": 0.15, "p_hit": 0.70, "dCVD": -2.0},
        {"name": "Critical", "h_t": 0.50, "p_hit": 0.30, "dCVD": -1.5},
    ]
    
    results = []
    
    for scenario in scenarios:
        # 构建测试请求
        from ..schemas.features import ExitUpdates
        from ..schemas.base import Position
        
        test_request = ExitRequest(
            position=Position(**position_data),
            updates=ExitUpdates(
                p_hit=scenario["p_hit"],
                mae_q90=0.003,
                t_hit_q50_bars=8,
                h_t=scenario["h_t"],
                dCVD=scenario["dCVD"],
                replenish=0.65
            )
        )
        
        # 执行决策
        response = decide_exit(test_request, config)
        
        results.append({
            "scenario": scenario["name"],
            "input": scenario,
            "action": response.action,
            "reduce_pct": response.reduce_pct,
            "reasons": response.reason,
            "runtime_ms": response.runtime_ms
        })
    
    return results
