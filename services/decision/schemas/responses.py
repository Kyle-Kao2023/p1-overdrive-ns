"""决策响应模型"""
from typing import List, Optional

from pydantic import BaseModel, Field

from .base import BaseResponse, ExecutionConfig, RiskMetrics


class EnterResponse(BaseResponse):
    """入场决策响应"""
    allow: bool = Field(..., description="是否允许入场")
    side: Optional[str] = Field(None, description="建议方向", regex="^(long|short)$")
    alloc_equity_pct: Optional[float] = Field(
        None, description="建议权益分配百分比", ge=0.0, le=1.0
    )
    exec: Optional[ExecutionConfig] = Field(None, description="执行配置")
    risk: Optional[RiskMetrics] = Field(None, description="风险指标")
    reason_chain: List[str] = Field(default_factory=list, description="决策推理链")

    class Config:
        schema_extra = {
            "example": {
                "allow": True,
                "side": "short",
                "alloc_equity_pct": 0.8,
                "exec": {
                    "type": "post_only_limit_or_mpo",
                    "reduce_only_fallback": True
                },
                "risk": {
                    "liq_buffer_pct": 0.0180,
                    "lhs_pct": 0.0065
                },
                "reason_chain": [
                    "C_align=0.88",
                    "C_of=0.83",
                    "C_vision=0.79",
                    "p_hit=0.79/T50=6",
                    "MAE+Slip+ε ≤ LiqBuffer",
                    "Fragility OK"
                ],
                "runtime_ms": 55,
                "timestamp": "2025-09-14T10:25:01Z"
            }
        }


class ExitResponse(BaseResponse):
    """退出决策响应"""
    action: str = Field(
        ..., 
        description="退出动作", 
        regex="^(hold|reduce|close|trail)$"
    )
    reduce_pct: Optional[float] = Field(
        None, 
        description="减仓百分比(当action为reduce时)", 
        ge=0.0, 
        le=1.0
    )
    reason: List[str] = Field(default_factory=list, description="退出原因")

    class Config:
        schema_extra = {
            "example": {
                "action": "reduce",
                "reduce_pct": 0.5,
                "reason": [
                    "hazard>0.3",
                    "of_flip",
                    "timeout_risk"
                ],
                "runtime_ms": 39,
                "timestamp": "2025-09-14T10:30:00Z"
            }
        }
