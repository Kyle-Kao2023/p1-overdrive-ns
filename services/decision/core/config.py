"""配置管理模块"""
import os
from typing import Any, Dict, List

import yaml
from loguru import logger
from pydantic import BaseSettings


class Settings(BaseSettings):
    """应用设置"""
    app_env: str = "dev"
    log_level: str = "INFO"
    redis_url: str = "redis://localhost:6379/0"
    config_path: str = "/app/configs/default.yaml"
    decision_port: int = 8000
    featurehub_port: int = 8010
    vision_port: int = 8020

    class Config:
        env_file = ".env"


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_path: str = None):
        self.settings = Settings()
        self.config_path = config_path or self.settings.config_path
        self._config: Dict[str, Any] = {}
        self._load_config()
    
    def _load_config(self) -> None:
        """加载YAML配置文件"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r", encoding="utf-8") as f:
                    self._config = yaml.safe_load(f) or {}
                logger.info(f"Loaded config from {self.config_path}")
            else:
                logger.warning(f"Config file not found: {self.config_path}, using defaults")
                self._config = self._get_default_config()
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            self._config = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "vol_sweet_spot": {
                "bull": {"sigma_min": 0.0012, "sigma_max": 0.0022, "skew_min": 0.5},
                "bear": {"sigma_min": 0.0015, "sigma_max": 0.0028, "skew_max": -0.5}
            },
            "gates": {
                "C_align_min": 0.85,
                "C_of_min": 0.80,
                "C_vision_min": 0.75,
                "p_hit_min": 0.75,
                "epsilon": 0.0005,
                "slip_q95_max": 0.0005,
                "spread_bp_max": 5,
                "min_depth_px": 1000000
            },
            "exit": {
                "hazard_thresh": 0.30,
                "phit_floor": 0.50,
                "t_hit_grace_bars": 3,
                "reduce_pct": 0.5
            },
            "exec": {
                "mode": "post_only_limit_or_mpo",
                "reduce_only_fallback": True
            },
            "blacklist_events": [],
            "latency_slo_ms": 70
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值，支持点号分隔的嵌套键"""
        keys = key.split(".")
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_vol_config(self, side: str) -> Dict[str, float]:
        """获取波动率配置"""
        if side.lower() in ["bull", "long"]:
            return self.get("vol_sweet_spot.bull", {})
        elif side.lower() in ["bear", "short"]:
            return self.get("vol_sweet_spot.bear", {})
        else:
            return {}
    
    def get_gates_config(self) -> Dict[str, Any]:
        """获取Gate配置"""
        return self.get("gates", {})
    
    def get_exit_config(self) -> Dict[str, Any]:
        """获取退出配置"""
        return self.get("exit", {})
    
    def get_exec_config(self) -> Dict[str, Any]:
        """获取执行配置"""
        return self.get("exec", {})
    
    def get_blacklist_events(self) -> List[str]:
        """获取黑名单事件"""
        return self.get("blacklist_events", [])
    
    def get_latency_slo(self) -> int:
        """获取延迟SLA"""
        return self.get("latency_slo_ms", 70)


# 全局配置管理器实例
config_manager = ConfigManager()
