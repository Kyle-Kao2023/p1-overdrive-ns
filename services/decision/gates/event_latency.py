"""事件与延迟Gate - 黑名单事件和延迟检查"""
import time
from datetime import datetime, timedelta
from typing import List, Tuple

from ..core.config import config_manager
from ..core.utils import perf_monitor


def check_blacklist_events(current_time: datetime = None) -> Tuple[bool, str]:
    """
    检查是否在黑名单事件窗口内
    
    Args:
        current_time: 当前时间，如果为None则使用当前UTC时间
        
    Returns:
        (是否允许, 说明)
    """
    if current_time is None:
        current_time = datetime.utcnow()
    
    blacklist_events = config_manager.get_blacklist_events()
    
    if not blacklist_events:
        return True, "No blacklist events configured"
    
    # 检查每个黑名单事件
    for event in blacklist_events:
        event_name = event.get("name", "Unknown")
        event_start = event.get("start_time")
        event_end = event.get("end_time")
        
        if not event_start or not event_end:
            continue
        
        # 解析时间（假设格式为ISO格式）
        try:
            start_dt = datetime.fromisoformat(event_start.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(event_end.replace('Z', '+00:00'))
            
            # 检查当前时间是否在事件窗口内
            if start_dt <= current_time <= end_dt:
                return False, f"In blacklist event window: {event_name} ({event_start} to {event_end})"
                
        except Exception as e:
            # 时间解析错误，记录但不阻止交易
            continue
    
    return True, "Not in any blacklist event window"


def check_latency_sla(operation_name: str = "decision") -> Tuple[bool, str]:
    """
    检查延迟是否满足SLA
    
    Args:
        operation_name: 操作名称
        
    Returns:
        (是否满足SLA, 说明)
    """
    sla_ms = config_manager.get_latency_slo()
    stats = perf_monitor.get_stats(operation_name)
    
    if not stats:
        return True, "No latency data available"
    
    p95_latency = stats.get("p95_ms", 0)
    
    if p95_latency <= sla_ms:
        return True, f"P95 latency {p95_latency:.1f}ms <= SLA {sla_ms}ms"
    else:
        return False, f"P95 latency {p95_latency:.1f}ms > SLA {sla_ms}ms"


def validate_system_health() -> Tuple[bool, List[str]]:
    """验证系统健康状态"""
    issues = []
    
    # 可以在这里添加更多健康检查
    # 例如：Redis连接、模型服务状态等
    
    # 检查延迟SLA
    latency_ok, latency_msg = check_latency_sla()
    if not latency_ok:
        issues.append(f"Latency SLA violation: {latency_msg}")
    
    return len(issues) == 0, issues


def is_market_hours() -> bool:
    """检查是否在交易时间（加密货币24/7，此函数预留扩展用）"""
    # 加密货币市场24/7开放
    return True


def check_rate_limiting() -> Tuple[bool, str]:
    """检查是否触发频率限制"""
    # 这里可以实现更复杂的频率限制逻辑
    # 目前返回简单检查
    return True, "Rate limiting OK"


def passes(env_context: dict = None) -> Tuple[bool, str]:
    """
    事件与延迟Gate主检查函数
    
    检查项：
    1. 不在黑名单事件窗口内
    2. 系统延迟满足SLA要求
    3. 系统健康状态良好
    4. 频率限制检查
    
    Args:
        env_context: 环境上下文，可包含当前时间等信息
        
    Returns:
        (通过状态, 原因说明)
    """
    failed_checks = []
    passed_checks = []
    
    # 获取当前时间
    current_time = None
    if env_context and "current_time" in env_context:
        current_time = env_context["current_time"]
    
    # 1. 检查黑名单事件
    blacklist_ok, blacklist_msg = check_blacklist_events(current_time)
    if blacklist_ok:
        passed_checks.append("Blacklist events: CLEAR")
    else:
        failed_checks.append(blacklist_msg)
    
    # 2. 检查系统健康状态
    health_ok, health_issues = validate_system_health()
    if health_ok:
        passed_checks.append("System health: OK")
    else:
        failed_checks.extend(health_issues)
    
    # 3. 检查频率限制
    rate_ok, rate_msg = check_rate_limiting()
    if rate_ok:
        passed_checks.append("Rate limiting: OK")
    else:
        failed_checks.append(rate_msg)
    
    # 4. 检查市场时间（预留）
    if not is_market_hours():
        failed_checks.append("Outside market hours")
    else:
        passed_checks.append("Market hours: OK")
    
    # 判断是否通过
    if failed_checks:
        return False, f"Event & Latency Gate FAIL: {'; '.join(failed_checks)}"
    else:
        return True, f"Event & Latency Gate PASS: {', '.join(passed_checks)}"


def get_system_status() -> dict:
    """获取系统状态摘要"""
    latency_stats = perf_monitor.get_stats("decision")
    health_ok, health_issues = validate_system_health()
    
    return {
        "system_healthy": health_ok,
        "health_issues": health_issues,
        "latency_stats": latency_stats,
        "latency_sla_ms": config_manager.get_latency_slo(),
        "blacklist_events_count": len(config_manager.get_blacklist_events()),
        "market_open": is_market_hours()
    }
