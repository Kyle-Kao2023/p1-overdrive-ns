"""共识Gate - 多维度一致性检查"""
from typing import Tuple

from ..core.config import config_manager
from ..schemas.features import Features


def check_alignment(features: Features) -> Tuple[bool, str]:
    """检查多时间框架一致性"""
    c_align = features.C_align
    threshold = config_manager.get("gates.C_align_min", 0.85)
    
    if c_align >= threshold:
        return True, f"C_align={c_align:.2f} >= {threshold}"
    else:
        return False, f"C_align={c_align:.2f} < {threshold}"


def check_orderflow(features: Features) -> Tuple[bool, str]:
    """检查订单流一致性"""
    c_of = features.C_of
    threshold = config_manager.get("gates.C_of_min", 0.80)
    
    if c_of >= threshold:
        return True, f"C_of={c_of:.2f} >= {threshold}"
    else:
        return False, f"C_of={c_of:.2f} < {threshold}"


def check_vision(features: Features) -> Tuple[bool, str]:
    """检查视觉识别一致性"""
    c_vision = features.C_vision
    threshold = config_manager.get("gates.C_vision_min", 0.75)
    
    if c_vision >= threshold:
        return True, f"C_vision={c_vision:.2f} >= {threshold}"
    else:
        return False, f"C_vision={c_vision:.2f} < {threshold}"


def check_pine_match(features: Features) -> Tuple[bool, str]:
    """检查Pine Script指标匹配"""
    if features.pine_match:
        return True, "Pine_match=True"
    else:
        return False, "Pine_match=False"


def analyze_consensus_strength(features: Features) -> dict:
    """分析共识强度"""
    return {
        "multi_tf_strength": features.C_align,
        "orderflow_strength": features.C_of,
        "vision_strength": features.C_vision,
        "technical_confirm": features.pine_match,
        "overall_score": (features.C_align + features.C_of + features.C_vision) / 3
    }


def passes(features: Features) -> Tuple[bool, str]:
    """
    共识Gate主检查函数
    
    检查项：
    1. C_align ≥ 0.85（Z_4H/Z_1H/Z_15m 一致）
    2. C_of ≥ 0.80（OBI/ΔCVD/补单率 统合）
    3. C_vision ≥ 0.75（YOLO/DETR tokens → 方向分）
    4. Pine_match = true（TradingView 指标同向）
    """
    failed_checks = []
    passed_checks = []
    
    # 检查C_align
    align_ok, align_msg = check_alignment(features)
    if align_ok:
        passed_checks.append(align_msg)
    else:
        failed_checks.append(align_msg)
    
    # 检查C_of
    of_ok, of_msg = check_orderflow(features)
    if of_ok:
        passed_checks.append(of_msg)
    else:
        failed_checks.append(of_msg)
    
    # 检查C_vision
    vision_ok, vision_msg = check_vision(features)
    if vision_ok:
        passed_checks.append(vision_msg)
    else:
        failed_checks.append(vision_msg)
    
    # 检查Pine match
    pine_ok, pine_msg = check_pine_match(features)
    if pine_ok:
        passed_checks.append(pine_msg)
    else:
        failed_checks.append(pine_msg)
    
    # 判断是否通过（所有检查都必须通过）
    if failed_checks:
        return False, f"Consensus Gate FAIL: {', '.join(failed_checks)}"
    else:
        return True, f"Consensus Gate PASS: {', '.join(passed_checks)}"


def get_consensus_summary(features: Features) -> str:
    """获取共识摘要"""
    strength = analyze_consensus_strength(features)
    return (
        f"Consensus Summary: "
        f"MTF={strength['multi_tf_strength']:.2f}, "
        f"OF={strength['orderflow_strength']:.2f}, "
        f"Vision={strength['vision_strength']:.2f}, "
        f"Pine={strength['technical_confirm']}, "
        f"Overall={strength['overall_score']:.2f}"
    )
