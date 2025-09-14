"""示例数据载荷"""
from datetime import datetime

# 示例入场请求 - Bull场景
EXAMPLE_ENTER_BULL = {
    "symbol": "BTCUSDT",
    "side_hint": "long",
    "ts": "2025-09-14T10:25:00Z",
    "tf": "15m",
    "features": {
        "sigma_1m": 0.0015,
        "skew_1m": 0.65,
        "Z_4H": 0.8,
        "Z_1H": 0.6,
        "Z_15m": 0.7,
        "C_align": 0.89,
        "C_of": 0.85,
        "C_vision": 0.82,
        "pine_match": True,
        "OF": {"obi": 0.67, "dCVD": 2.1, "replenish": 0.78},
        "vision_tokens": {"tokens": {"bull_hammer": 0.85, "morning_star": 0.73}},
        "onchain": {"oi_roc": 0.12, "gas_z": -0.5},
        "market": {"mark": 43250.5, "liq_price": 41800.0, "spread_bp": 2, "depth_px": 2500000}
    },
    "pgm": {
        "p_hit": 0.82,
        "mae_q999": 0.0045,
        "slip_q95": 0.0003,
        "t_hit_q50_bars": 4,
        "factors": [
            ["Z4H//Z15m", 0.25],
            ["OF_triad", 0.22],
            ["Pine_match", 0.15],
            ["C_vision", 0.12]
        ]
    }
}

# 示例入场请求 - Bear场景
EXAMPLE_ENTER_BEAR = {
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

# 示例退出请求
EXAMPLE_EXIT = {
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

# 拒单示例 - Vol Gate失败
EXAMPLE_ENTER_REJECT_VOL = {
    "symbol": "ETHUSDT", 
    "side_hint": "short",
    "ts": "2025-09-14T10:25:00Z",
    "tf": "15m",
    "features": {
        "sigma_1m": 0.0045,  # 超出Bear范围上限
        "skew_1m": -0.15,    # skew绝对值太小
        "Z_4H": -0.9,
        "Z_1H": -0.7,
        "Z_15m": -0.6,
        "C_align": 0.88,
        "C_of": 0.83,
        "C_vision": 0.79,
        "pine_match": True,
        "OF": {"obi": 0.31, "dCVD": -1.2, "replenish": 0.67},
        "vision_tokens": {"tokens": {"bear_engulfing": 0.82}},
        "onchain": {"oi_roc": 0.08, "gas_z": 1.1},
        "market": {"mark": 2415.3, "liq_price": 2458.8, "spread_bp": 3, "depth_px": 1200000}
    },
    "pgm": {
        "p_hit": 0.79,
        "mae_q999": 0.0058,
        "slip_q95": 0.0004,
        "t_hit_q50_bars": 6,
        "factors": []
    }
}
