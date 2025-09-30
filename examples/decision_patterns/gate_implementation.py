"""
P1 Trading Builder - Gate 实现模式示例
这个文件展示如何在 P1 系统中实现新的安全门控制器
"""

from typing import Tuple, Dict, Any
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)

class BaseGate(ABC):
    """
    P1 Gate 基础类 - 所有安全门必须继承此类
    
    每个 Gate 负责验证特定的市场条件或风险指标
    返回 (通过状态, 失败原因) 元组
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.gate_name = self.__class__.__name__.replace('Gate', '').upper()
    
    @abstractmethod
    def passes(self, features: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Gate 验证逻辑
        
        Args:
            features: 标准化的市场特征字典
            
        Returns:
            (是否通过, 失败原因)
        """
        pass
    
    def log_decision(self, passed: bool, reason: str, features: Dict[str, Any]):
        """标准化的 Gate 日志记录"""
        status = "PASS" if passed else "FAIL"
        logger.info(
            f"Gate {self.gate_name}: {status} - {reason}",
            extra={
                "gate_name": self.gate_name,
                "passed": passed,
                "reason": reason,
                "symbol": features.get("symbol", "UNKNOWN"),
                "runtime_ms": features.get("_runtime_ms", 0)
            }
        )

class VolGate(BaseGate):
    """
    波动率 Gate - 验证市场波动率是否在理想范围内
    P1 系统要求在"甜蜜点"波动率下交易以提高胜率
    """
    
    def passes(self, features: Dict[str, Any]) -> Tuple[bool, str]:
        side_hint = features.get("side_hint", "").lower()
        sigma_1m = features.get("sigma_1m", 0)
        skew_1m = features.get("skew_1m", 0)
        
        # 获取配置的波动率甜蜜点
        if side_hint == "long":
            vol_config = self.config["vol_sweet_spot"]["bull"]
            skew_min = vol_config.get("skew_min", 0.5)
            valid_skew = skew_1m >= skew_min
        else:  # short
            vol_config = self.config["vol_sweet_spot"]["bear"] 
            skew_max = vol_config.get("skew_max", -0.5)
            valid_skew = skew_1m <= skew_max
            
        sigma_min = vol_config["sigma_min"]
        sigma_max = vol_config["sigma_max"]
        
        # 验证波动率范围
        vol_in_range = sigma_min <= sigma_1m <= sigma_max
        
        if not vol_in_range:
            reason = f"σ={sigma_1m:.4f} outside [{sigma_min:.4f}, {sigma_max:.4f}]"
            self.log_decision(False, reason, features)
            return False, reason
            
        if not valid_skew:
            reason = f"skew={skew_1m:.2f} invalid for {side_hint}"
            self.log_decision(False, reason, features)
            return False, reason
            
        reason = f"σ={sigma_1m:.4f} ∈ sweet_spot, skew={skew_1m:.2f} OK"
        self.log_decision(True, reason, features)
        return True, reason

# 使用示例
if __name__ == "__main__":
    config = {
        "vol_sweet_spot": {
            "bull": {"sigma_min": 0.0012, "sigma_max": 0.0022, "skew_min": 0.5},
            "bear": {"sigma_min": 0.0015, "sigma_max": 0.0028, "skew_max": -0.5}
        }
    }
    
    gate = VolGate(config)
    features = {
        "symbol": "ETHUSDT",
        "side_hint": "short",
        "sigma_1m": 0.0020,
        "skew_1m": -0.65
    }
    
    passed, reason = gate.passes(features)
    print(f"Gate 结果: {'✅ 通过' if passed else '❌ 失败'} - {reason}")
