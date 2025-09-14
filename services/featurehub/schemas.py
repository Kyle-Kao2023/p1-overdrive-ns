"""FeatureHub数据模式定义"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class PineWebhook(BaseModel):
    """TradingView Pine Script Webhook数据"""
    symbol: str = Field(..., description="交易标的")
    timeframe: str = Field(..., description="时间框架")
    timestamp: datetime = Field(..., description="信号时间")
    signal: str = Field(..., description="信号类型", regex="^(BUY|SELL|NEUTRAL)$")
    price: float = Field(..., description="信号价格", gt=0)
    indicators: Dict[str, float] = Field(default_factory=dict, description="指标值")
    confidence: Optional[float] = Field(None, description="信号置信度", ge=0, le=1)
    
    class Config:
        schema_extra = {
            "example": {
                "symbol": "ETHUSDT",
                "timeframe": "15m",
                "timestamp": "2025-09-14T10:25:00Z",
                "signal": "SELL",
                "price": 2415.3,
                "indicators": {
                    "rsi": 75.2,
                    "macd": -0.5,
                    "bb_position": 0.85
                },
                "confidence": 0.78
            }
        }


class VisionTokens(BaseModel):
    """视觉识别Tokens"""
    image_ref: str = Field(..., description="图像引用ID")
    timestamp: datetime = Field(..., description="检测时间")
    tokens: Dict[str, float] = Field(..., description="识别到的形态及置信度")
    confidence_overall: float = Field(..., description="整体检测置信度", ge=0, le=1)
    
    class Config:
        schema_extra = {
            "example": {
                "image_ref": "chart_20250914_102500",
                "timestamp": "2025-09-14T10:25:00Z",
                "tokens": {
                    "bear_engulfing": 0.82,
                    "long_upper_wick": 0.74,
                    "support_break": 0.68
                },
                "confidence_overall": 0.79
            }
        }


class MarketSnapshot(BaseModel):
    """市场快照数据"""
    symbol: str = Field(..., description="交易标的")
    timestamp: datetime = Field(..., description="快照时间")
    mark_price: float = Field(..., description="标记价格", gt=0)
    spread_bp: float = Field(..., description="点差(bp)", ge=0)
    depth_px: float = Field(..., description="深度(价值)", ge=0)
    volume_24h: float = Field(..., description="24小时成交量", ge=0)
    
    # 技术指标
    sigma_1m: float = Field(..., description="1分钟波动率", ge=0)
    skew_1m: float = Field(..., description="1分钟偏度")
    z_scores: Dict[str, float] = Field(..., description="多时间框架Z-scores")
    
    # 共识指标
    c_align: float = Field(..., description="多时间框架一致性", ge=0, le=1)
    c_of: float = Field(..., description="订单流一致性", ge=0, le=1)
    c_vision: float = Field(..., description="视觉识别一致性", ge=0, le=1)
    
    # OrderFlow
    orderflow: Dict[str, float] = Field(..., description="订单流数据")
    
    # 链上数据
    onchain: Dict[str, float] = Field(..., description="链上指标")
    
    class Config:
        schema_extra = {
            "example": {
                "symbol": "ETHUSDT",
                "timestamp": "2025-09-14T10:25:00Z",
                "mark_price": 2415.3,
                "spread_bp": 3.2,
                "depth_px": 1200000,
                "volume_24h": 15000000,
                "sigma_1m": 0.0018,
                "skew_1m": -0.72,
                "z_scores": {"4H": -0.9, "1H": -0.7, "15m": -0.6},
                "c_align": 0.88,
                "c_of": 0.83,
                "c_vision": 0.79,
                "orderflow": {"obi": 0.31, "dCVD": -1.2, "replenish": 0.67},
                "onchain": {"oi_roc": 0.08, "gas_z": 1.1}
            }
        }


class FeatureResponse(BaseModel):
    """特征响应"""
    success: bool = Field(..., description="是否成功")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: Optional[Any] = Field(None, description="响应数据")
    message: str = Field(default="", description="消息")


class SnapshotRequest(BaseModel):
    """快照请求"""
    symbol: str = Field(..., description="交易标的")
    timeframe: Optional[str] = Field("15m", description="时间框架")
    include_history: bool = Field(False, description="是否包含历史数据")
