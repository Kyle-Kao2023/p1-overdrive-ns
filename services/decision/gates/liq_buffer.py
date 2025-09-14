"""流动性缓冲Gate - 风险边界检查"""
from typing import Tuple

from ..core.config import config_manager
from ..core.utils import calculate_liq_buffer
from ..schemas.features import Features, PGMMetrics


def calculate_risk_budget(pgm: PGMMetrics, epsilon: float) -> float:
    """
    计算风险预算
    
    风险预算 = MAE_Q999 + Slip_Q95 + ε
    """
    return pgm.mae_q999 + pgm.slip_q95 + epsilon


def check_liq_buffer_adequate(features: Features, pgm: PGMMetrics) -> Tuple[bool, str, dict]:
    """
    检查流动性缓冲是否充足
    
    条件: Q0.999(MAE) + Q0.95(Slip) + ε ≤ LiqBuffer
    """
    # 获取配置
    epsilon = config_manager.get("gates.epsilon", 0.0005)
    
    # 计算强平缓冲
    liq_buffer = calculate_liq_buffer(features.market.mark, features.market.liq_price)
    
    # 计算风险预算
    risk_budget = calculate_risk_budget(pgm, epsilon)
    
    # 风险指标详情
    risk_details = {
        "liq_buffer_pct": liq_buffer,
        "mae_q999": pgm.mae_q999,
        "slip_q95": pgm.slip_q95,
        "epsilon": epsilon,
        "risk_budget": risk_budget,
        "safety_margin": liq_buffer - risk_budget,
        "utilization_pct": risk_budget / liq_buffer if liq_buffer > 0 else float('inf')
    }
    
    # 判断是否通过
    if liq_buffer <= 0:
        return False, "Invalid liquidation buffer (<=0)", risk_details
    
    if risk_budget <= liq_buffer:
        return True, f"Risk budget {risk_budget:.4f} ≤ LiqBuffer {liq_buffer:.4f}", risk_details
    else:
        return False, f"Risk budget {risk_budget:.4f} > LiqBuffer {liq_buffer:.4f}", risk_details


def check_market_depth(features: Features) -> Tuple[bool, str]:
    """检查市场深度是否充足"""
    depth_px = features.market.depth_px
    min_depth = config_manager.get("gates.min_depth_px", 1000000)
    
    if depth_px >= min_depth:
        return True, f"Depth {depth_px:,.0f} >= {min_depth:,.0f}"
    else:
        return False, f"Depth {depth_px:,.0f} < {min_depth:,.0f}"


def check_spread(features: Features) -> Tuple[bool, str]:
    """检查点差是否在可接受范围"""
    spread_bp = features.market.spread_bp
    max_spread = config_manager.get("gates.spread_bp_max", 5)
    
    if spread_bp <= max_spread:
        return True, f"Spread {spread_bp}bp <= {max_spread}bp"
    else:
        return False, f"Spread {spread_bp}bp > {max_spread}bp"


def validate_market_microstructure(features: Features) -> Tuple[bool, list]:
    """验证市场微结构"""
    issues = []
    
    # 检查深度
    depth_ok, depth_msg = check_market_depth(features)
    if not depth_ok:
        issues.append(depth_msg)
    
    # 检查点差
    spread_ok, spread_msg = check_spread(features)
    if not spread_ok:
        issues.append(spread_msg)
    
    return len(issues) == 0, issues


def passes(features: Features, pgm: PGMMetrics) -> Tuple[bool, str, dict]:
    """
    流动性缓冲Gate主检查函数
    
    检查项：
    1. Q0.999(MAE) + Q0.95(Slip) + ε ≤ LiqBuffer
    2. 市场深度充足
    3. 点差在可接受范围内
    
    Returns:
        (通过状态, 原因说明, 风险详情)
    """
    # 1. 检查流动性缓冲
    buffer_ok, buffer_msg, risk_details = check_liq_buffer_adequate(features, pgm)
    
    # 2. 检查市场微结构
    micro_ok, micro_issues = validate_market_microstructure(features)
    
    # 组合结果
    if buffer_ok and micro_ok:
        return True, f"Liq-Buffer Gate PASS: {buffer_msg}", risk_details
    else:
        issues = []
        if not buffer_ok:
            issues.append(buffer_msg)
        if not micro_ok:
            issues.extend(micro_issues)
        
        return False, f"Liq-Buffer Gate FAIL: {'; '.join(issues)}", risk_details


def get_risk_summary(features: Features, pgm: PGMMetrics) -> dict:
    """获取风险摘要"""
    _, _, risk_details = check_liq_buffer_adequate(features, pgm)
    
    return {
        "liquidation_buffer_pct": risk_details["liq_buffer_pct"] * 100,
        "risk_utilization_pct": min(risk_details["utilization_pct"] * 100, 999),  # Cap at 999%
        "safety_margin_bp": risk_details["safety_margin"] * 10000,
        "components": {
            "mae_q999_bp": pgm.mae_q999 * 10000,
            "slip_q95_bp": pgm.slip_q95 * 10000,
            "epsilon_bp": risk_details["epsilon"] * 10000
        }
    }
