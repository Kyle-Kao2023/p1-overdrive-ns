"""基础共用类型定义"""
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class BaseResponse(BaseModel):
    """基础响应模型"""
    runtime_ms: int = Field(..., description="执行时间(毫秒)")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class OrderFlow(BaseModel):
    """订单流数据"""
    obi: float = Field(..., description="Order Book Imbalance", ge=-1.0, le=1.0)
    dCVD: float = Field(..., description="Delta Cumulative Volume Delta")
    replenish: float = Field(..., description="补单率", ge=0.0, le=1.0)


class VisionTokens(BaseModel):
    """视觉识别token"""
    tokens: Dict[str, float] = Field(default_factory=dict, description="识别到的形态及其置信度")
    
    class Config:
        schema_extra = {
            "example": {
                "tokens": {
                    "bear_engulfing": 0.82,
                    "long_upper_wick": 0.74,
                    "doji": 0.65
                }
            }
        }


class OnChain(BaseModel):
    """链上数据"""
    oi_roc: float = Field(..., description="Open Interest Rate of Change")
    gas_z: float = Field(..., description="Gas price Z-score")


class MarketSnapshot(BaseModel):
    """市场快照"""
    mark: float = Field(..., description="标记价格", gt=0)
    liq_price: float = Field(..., description="强平价格", gt=0)
    spread_bp: float = Field(..., description="点差(bp)", ge=0)
    depth_px: float = Field(..., description="深度(价值)", ge=0)


class Position(BaseModel):
    """持仓信息"""
    avg_entry: float = Field(..., description="平均开仓价", gt=0)
    side: str = Field(..., description="方向", regex="^(long|short)$")
    qty: float = Field(..., description="数量", gt=0)
    upl_pct: float = Field(..., description="未实现盈亏百分比")


class ExecutionConfig(BaseModel):
    """执行配置"""
    type: str = Field(default="post_only_limit_or_mpo", description="执行类型")
    reduce_only_fallback: bool = Field(default=True, description="是否允许仅减仓fallback")


class RiskMetrics(BaseModel):
    """风险指标"""
    liq_buffer_pct: float = Field(..., description="强平缓冲百分比", ge=0)
    lhs_pct: float = Field(..., description="左侧风险百分比", ge=0)
