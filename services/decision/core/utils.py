"""工具函数模块"""
import time
from contextlib import contextmanager
from typing import Any, Dict, Generator, Tuple

import numpy as np
from loguru import logger


@contextmanager
def timer() -> Generator[Dict[str, Any], None, None]:
    """计时器上下文管理器"""
    result = {"start_time": time.time()}
    try:
        yield result
    finally:
        result["end_time"] = time.time()
        result["duration_ms"] = int((result["end_time"] - result["start_time"]) * 1000)


def validate_symbol(symbol: str) -> bool:
    """验证交易标的格式"""
    return symbol.endswith("USDT") and len(symbol) > 4


def calculate_liq_buffer(mark_price: float, liq_price: float) -> float:
    """计算强平缓冲"""
    if mark_price <= 0:
        return 0.0
    return abs(mark_price - liq_price) / mark_price


def calculate_sigma_and_skew(returns: np.ndarray, sigma_window: int = 5, skew_window: int = 20) -> Tuple[float, float]:
    """计算波动率和偏度"""
    if len(returns) < max(sigma_window, skew_window):
        return 0.0, 0.0
    
    # 计算sigma (标准差)
    sigma = np.std(returns[-sigma_window:])
    
    # 计算skew (偏度)
    recent_returns = returns[-skew_window:]
    mean_ret = np.mean(recent_returns)
    std_ret = np.std(recent_returns)
    
    if std_ret == 0:
        skew = 0.0
    else:
        skew = np.mean(((recent_returns - mean_ret) / std_ret) ** 3)
    
    return float(sigma), float(skew)


def is_in_vol_sweet_spot(sigma: float, skew: float, side: str, vol_config: Dict[str, float]) -> Tuple[bool, str]:
    """检查是否在波动率甜蜜点"""
    if not vol_config:
        return False, "Vol config not found"
    
    if side.lower() in ["long", "bull"]:
        # Bull条件：sigma在范围内且skew > skew_min
        sigma_ok = vol_config.get("sigma_min", 0) <= sigma <= vol_config.get("sigma_max", float("inf"))
        skew_ok = skew >= vol_config.get("skew_min", 0)
        
        if not sigma_ok:
            return False, f"Sigma {sigma:.4f} not in bull range [{vol_config.get('sigma_min')}, {vol_config.get('sigma_max')}]"
        if not skew_ok:
            return False, f"Skew {skew:.2f} < {vol_config.get('skew_min')} (bull min)"
        
        return True, "Bull vol sweet-spot OK"
    
    elif side.lower() in ["short", "bear"]:
        # Bear条件：sigma在范围内且skew < skew_max (负值)
        sigma_ok = vol_config.get("sigma_min", 0) <= sigma <= vol_config.get("sigma_max", float("inf"))
        skew_ok = skew <= vol_config.get("skew_max", 0)
        
        if not sigma_ok:
            return False, f"Sigma {sigma:.4f} not in bear range [{vol_config.get('sigma_min')}, {vol_config.get('sigma_max')}]"
        if not skew_ok:
            return False, f"Skew {skew:.2f} > {vol_config.get('skew_max')} (bear max)"
        
        return True, "Bear vol sweet-spot OK"
    
    else:
        return False, f"Unknown side: {side}"


def format_reason_chain(reasons: list) -> str:
    """格式化推理链为可读字符串"""
    return " → ".join(reasons)


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.metrics = {}
    
    def record(self, name: str, duration_ms: int) -> None:
        """记录性能指标"""
        if name not in self.metrics:
            self.metrics[name] = []
        self.metrics[name].append(duration_ms)
        
        # 保持最近100条记录
        if len(self.metrics[name]) > 100:
            self.metrics[name] = self.metrics[name][-100:]
    
    def get_stats(self, name: str) -> Dict[str, float]:
        """获取性能统计"""
        if name not in self.metrics or not self.metrics[name]:
            return {}
        
        values = self.metrics[name]
        return {
            "count": len(values),
            "avg_ms": np.mean(values),
            "p50_ms": np.percentile(values, 50),
            "p95_ms": np.percentile(values, 95),
            "p99_ms": np.percentile(values, 99),
            "max_ms": np.max(values)
        }
    
    def check_sla(self, name: str, sla_ms: int) -> bool:
        """检查是否违反SLA"""
        stats = self.get_stats(name)
        if not stats:
            return True
        return stats.get("p95_ms", 0) <= sla_ms


# 全局性能监控器
perf_monitor = PerformanceMonitor()
