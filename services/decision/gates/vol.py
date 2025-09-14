"""波动率甜蜜点Gate"""
from typing import Tuple

from ..core.config import config_manager
from ..core.utils import is_in_vol_sweet_spot
from ..schemas.features import Features


def is_in_band(features: Features, side_hint: str = "") -> Tuple[bool, str]:
    """
    检查是否在波动率甜蜜点
    
    Bull: σ_1m ∈ [0.0012,0.0022] 且 skew>+0.5
    Bear: σ_1m ∈ [0.0015,0.0028] 且 skew<−0.5
    |skew|<0.3 → 拒单
    """
    sigma = features.sigma_1m
    skew = features.skew_1m
    
    # 检查skew绝对值是否太小
    if abs(skew) < 0.3:
        return False, f"Skew absolute value {abs(skew):.2f} < 0.3, too neutral"
    
    # 根据skew判断市场偏向，如果有side_hint则使用
    if side_hint:
        market_side = side_hint.lower()
    elif skew > 0:
        market_side = "bull"
    else:
        market_side = "bear"
    
    # 获取对应的波动率配置
    vol_config = config_manager.get_vol_config(market_side)
    
    # 检查是否在甜蜜点
    return is_in_vol_sweet_spot(sigma, skew, market_side, vol_config)


def validate_vol_regime(features: Features) -> Tuple[bool, str]:
    """验证波动率环境是否适合交易"""
    sigma = features.sigma_1m
    
    # 极端波动率检查
    if sigma < 0.0005:
        return False, "Volatility too low, market likely stalled"
    
    if sigma > 0.01:  # 1%的波动率已经很高
        return False, "Volatility too high, extreme market conditions"
    
    return True, "Volatility regime acceptable"


def check_vol_gate(features: Features, side_hint: str = "") -> Tuple[bool, str]:
    """
    波动率Gate主检查函数
    
    Args:
        features: 市场特征
        side_hint: 方向提示
        
    Returns:
        (通过状态, 原因说明)
    """
    # 1. 基础波动率环境检查
    regime_ok, regime_msg = validate_vol_regime(features)
    if not regime_ok:
        return False, f"Vol Gate FAIL: {regime_msg}"
    
    # 2. 甜蜜点检查
    sweet_spot_ok, sweet_spot_msg = is_in_band(features, side_hint)
    if not sweet_spot_ok:
        return False, f"Vol Gate FAIL: {sweet_spot_msg}"
    
    return True, f"Vol Gate PASS: {sweet_spot_msg}"
