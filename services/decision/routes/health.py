"""健康检查和系统状态路由"""
from datetime import datetime
from typing import Dict

from fastapi import APIRouter
from loguru import logger

from ..core.config import config_manager
from ..core.utils import perf_monitor
from ..gates.event_latency import get_system_status
from ..decision.trace import get_recent_patterns

router = APIRouter()


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """基础健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "p1-decision-service"
    }


@router.get("/version")
async def get_version() -> Dict[str, str]:
    """获取版本信息"""
    return {
        "service": "p1-decision-service",
        "version": "0.1.0",
        "environment": config_manager.settings.app_env,
        "build_time": "2025-09-14T10:00:00Z"
    }


@router.get("/status")
async def get_detailed_status() -> Dict:
    """获取详细系统状态"""
    try:
        # 系统基础状态
        system_status = get_system_status()
        
        # 性能统计
        decision_stats = perf_monitor.get_stats("decision")
        
        # 最近决策模式
        decision_patterns = get_recent_patterns()
        
        # 配置状态
        config_status = {
            "config_loaded": True,
            "gates_config": config_manager.get_gates_config(),
            "latency_slo_ms": config_manager.get_latency_slo(),
            "blacklist_events": len(config_manager.get_blacklist_events())
        }
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_health": "healthy" if system_status["system_healthy"] else "degraded",
            "system": system_status,
            "performance": {
                "decision_latency": decision_stats,
                "patterns": decision_patterns
            },
            "configuration": config_status,
            "uptime_info": {
                "start_time": "2025-09-14T10:00:00Z",  # 应该从实际启动时间获取
                "current_time": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting detailed status: {e}")
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_health": "error",
            "error": str(e)
        }


@router.get("/metrics")
async def get_metrics() -> Dict:
    """获取Prometheus格式的指标（简化版）"""
    try:
        decision_stats = perf_monitor.get_stats("decision")
        system_status = get_system_status()
        patterns = get_recent_patterns()
        
        # 模拟Prometheus格式的指标
        metrics = {
            "decision_requests_total": patterns.get("total_decisions", 0),
            "decision_approvals_total": int(patterns.get("total_decisions", 0) * patterns.get("approval_rate", 0)),
            "decision_latency_seconds": {
                "avg": decision_stats.get("avg_ms", 0) / 1000,
                "p50": decision_stats.get("p50_ms", 0) / 1000,
                "p95": decision_stats.get("p95_ms", 0) / 1000,
                "p99": decision_stats.get("p99_ms", 0) / 1000
            },
            "system_health_status": 1 if system_status["system_healthy"] else 0,
            "latency_sla_violations": 1 if not perf_monitor.check_sla("decision", config_manager.get_latency_slo()) else 0
        }
        
        # Gate通过率
        if "gate_pass_rates" in patterns:
            for gate_name, pass_rate in patterns["gate_pass_rates"].items():
                metrics[f"gate_{gate_name.lower()}_pass_rate"] = pass_rate
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": metrics
        }
        
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }


@router.get("/config")
async def get_current_config() -> Dict:
    """获取当前配置（用于调试）"""
    return {
        "vol_sweet_spot": {
            "bull": config_manager.get_vol_config("bull"),
            "bear": config_manager.get_vol_config("bear")
        },
        "gates": config_manager.get_gates_config(),
        "exit": config_manager.get_exit_config(),
        "exec": config_manager.get_exec_config(),
        "latency_slo_ms": config_manager.get_latency_slo(),
        "blacklist_events": config_manager.get_blacklist_events()
    }
