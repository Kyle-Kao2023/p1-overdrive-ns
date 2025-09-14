"""特征数据和PGM指标的Pydantic模型"""
from datetime import datetime
from typing import List, Tuple

from pydantic import BaseModel, Field

from .base import MarketSnapshot, OnChain, OrderFlow, VisionTokens


class Features(BaseModel):
    """市场特征集合"""
    sigma_1m: float = Field(..., description="1分钟波动率", ge=0.0)
    skew_1m: float = Field(..., description="1分钟偏度")
    Z_4H: float = Field(..., description="4小时Z-score")
    Z_1H: float = Field(..., description="1小时Z-score")
    Z_15m: float = Field(..., description="15分钟Z-score")
    C_align: float = Field(..., description="多时间框架一致性", ge=0.0, le=1.0)
    C_of: float = Field(..., description="订单流一致性", ge=0.0, le=1.0)
    C_vision: float = Field(..., description="视觉识别一致性", ge=0.0, le=1.0)
    pine_match: bool = Field(..., description="Pine Script指标匹配")
    onchain: OnChain = Field(..., description="链上数据")
    OF: OrderFlow = Field(..., description="订单流数据")
    vision_tokens: VisionTokens = Field(..., description="视觉识别tokens")
    market: MarketSnapshot = Field(..., description="市场快照")


class PGMMetrics(BaseModel):
    """概率图模型预测指标"""
    p_hit: float = Field(..., description="命中概率", ge=0.0, le=1.0)
    mae_q999: float = Field(..., description="最大不利变动99.9分位数", ge=0.0)
    slip_q95: float = Field(..., description="滑点95分位数", ge=0.0)
    t_hit_q50_bars: int = Field(..., description="命中时间中位数(K线数)", ge=1)
    factors: List[Tuple[str, float]] = Field(
        default_factory=list, 
        description="因子贡献度列表[(因子名, 权重)]"
    )

    class Config:
        schema_extra = {
            "example": {
                "p_hit": 0.79,
                "mae_q999": 0.0058,
                "slip_q95": 0.0004,
                "t_hit_q50_bars": 6,
                "factors": [
                    ["Z4H//Z15m", 0.21],
                    ["OF_triad", 0.18],
                    ["OI_ROC//GasZ", 0.12],
                    ["Event_H", -0.05]
                ]
            }
        }


class EnterRequest(BaseModel):
    """入场决策请求"""
    symbol: str = Field(..., description="交易标的", regex="^[A-Z]+USDT$")
    side_hint: str = Field(..., description="方向提示", regex="^(long|short)$")
    ts: datetime = Field(..., description="时间戳")
    tf: str = Field(..., description="时间框架", regex="^(1m|5m|15m|1h|4h|1d)$")
    features: Features = Field(..., description="市场特征")
    pgm: PGMMetrics = Field(..., description="PGM预测指标")

    class Config:
        schema_extra = {
            "example": {
                "symbol": "ETHUSDT",
                "side_hint": "short",
                "ts": "2025-09-14T10:25:00Z",
                "tf": "15m",
                "features": {
                    "sigma_1m": 0.0018,
                    "skew_1m": -0.72,
                    "Z_4H": -0.9,
                    "Z_1H": -0.7,
                    "Z_15m": -0.6,
                    "C_align": 0.88,
                    "C_of": 0.83,
                    "C_vision": 0.79,
                    "pine_match": True,
                    "OF": {"obi": 0.31, "dCVD": -1.2, "replenish": 0.67},
                    "vision_tokens": {"tokens": {"bear_engulfing": 0.82, "long_upper_wick": 0.74}},
                    "onchain": {"oi_roc": 0.08, "gas_z": 1.1},
                    "market": {"mark": 2415.3, "liq_price": 2458.8, "spread_bp": 3, "depth_px": 1200000}
                },
                "pgm": {
                    "p_hit": 0.79,
                    "mae_q999": 0.0058,
                    "slip_q95": 0.0004,
                    "t_hit_q50_bars": 6,
                    "factors": [
                        ["Z4H//Z15m", 0.21],
                        ["OF_triad", 0.18],
                        ["OI_ROC//GasZ", 0.12],
                        ["Event_H", -0.05]
                    ]
                }
            }
        }


class ExitUpdates(BaseModel):
    """退出决策更新数据"""
    p_hit: float = Field(..., description="当前命中概率", ge=0.0, le=1.0)
    mae_q90: float = Field(..., description="MAE 90分位数", ge=0.0)
    t_hit_q50_bars: int = Field(..., description="命中时间中位数", ge=1)
    h_t: float = Field(..., description="Hazard rate", ge=0.0, le=1.0)
    dCVD: float = Field(..., description="实时dCVD")
    replenish: float = Field(..., description="实时补单率", ge=0.0, le=1.0)


class ExitRequest(BaseModel):
    """退出决策请求"""
    position: "Position" = Field(..., description="当前持仓信息")
    updates: ExitUpdates = Field(..., description="实时更新数据")

    class Config:
        schema_extra = {
            "example": {
                "position": {
                    "avg_entry": 2415.0,
                    "side": "short",
                    "qty": 120,
                    "upl_pct": 0.42
                },
                "updates": {
                    "p_hit": 0.46,
                    "mae_q90": 0.0035,
                    "t_hit_q50_bars": 12,
                    "h_t": 0.37,
                    "dCVD": 0.9,
                    "replenish": 0.25
                }
            }
        }


# 为了避免循环导入
from .base import Position
ExitRequest.model_rebuild()
