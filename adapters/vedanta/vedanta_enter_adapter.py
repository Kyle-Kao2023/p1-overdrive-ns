"""Vedanta入场适配器"""
import requests
from datetime import datetime
from typing import Dict, Optional


DECISION_URL = "http://localhost:8000"


def vedanta_to_enter_request(vedanta_data: Dict) -> Dict:
    """
    将Vedanta的数据格式转换为Decision API的EnterRequest格式
    
    Args:
        vedanta_data: Vedanta回测/实盘数据字典
        
    Returns:
        Decision API兼容的请求字典
    """
    
    # 从Vedanta数据中提取关键信息
    symbol = vedanta_data.get("symbol", "BTCUSDT")
    current_price = vedanta_data.get("price", 50000.0)
    
    # 技术指标映射
    indicators = vedanta_data.get("indicators", {})
    
    # 构造Features对象
    features = {
        "sigma_1m": indicators.get("volatility", 0.002),
        "skew_1m": indicators.get("skew", 0.0),
        "Z_4H": indicators.get("z_4h", 0.0),
        "Z_1H": indicators.get("z_1h", 0.0),
        "Z_15m": indicators.get("z_15m", 0.0),
        "C_align": indicators.get("c_align", 0.85),
        "C_of": indicators.get("c_of", 0.80),
        "C_vision": indicators.get("c_vision", 0.75),
        "pine_match": indicators.get("pine_match", True),
        
        # OrderFlow数据
        "OF": {
            "obi": indicators.get("obi", 0.0),
            "dCVD": indicators.get("dcvd", 0.0),
            "replenish": indicators.get("replenish", 0.6)
        },
        
        # 视觉token（如果有的话）
        "vision_tokens": {
            "tokens": indicators.get("vision_tokens", {})
        },
        
        # 链上数据
        "onchain": {
            "oi_roc": indicators.get("oi_roc", 0.0),
            "gas_z": indicators.get("gas_z", 0.0)
        },
        
        # 市场数据
        "market": {
            "mark": current_price,
            "liq_price": current_price * (1.1 if vedanta_data.get("side_hint") == "long" else 0.9),
            "spread_bp": indicators.get("spread_bp", 5.0),
            "depth_px": indicators.get("depth_px", 1000000)
        }
    }
    
    # PGM指标
    pgm = {
        "p_hit": indicators.get("p_hit", 0.78),
        "mae_q999": indicators.get("mae_q999", 0.006),
        "slip_q95": indicators.get("slip_q95", 0.0005),
        "t_hit_q50_bars": indicators.get("t_hit_q50_bars", 6),
        "factors": indicators.get("factors", [])
    }
    
    return {
        "symbol": symbol,
        "side_hint": vedanta_data.get("side_hint", "long"),
        "ts": vedanta_data.get("timestamp", datetime.utcnow().isoformat()),
        "tf": vedanta_data.get("timeframe", "15m"),
        "features": features,
        "pgm": pgm
    }


def call_p1_enter_decision(vedanta_data: Dict, timeout: float = 0.05) -> Optional[Dict]:
    """
    调用P1决策API进行入场决策
    
    Args:
        vedanta_data: Vedanta格式的市场数据
        timeout: API超时时间（秒）
        
    Returns:
        决策结果字典，如果失败返回None
    """
    try:
        # 转换数据格式
        enter_request = vedanta_to_enter_request(vedanta_data)
        
        # 调用P1 Decision API
        response = requests.post(
            f"{DECISION_URL}/decide/enter",
            json=enter_request,
            timeout=timeout
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"P1 Decision API error: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"Error calling P1 enter decision: {e}")
        return None


def vedanta_enter_hook(vedanta_data: Dict) -> Dict:
    """
    Vedanta入场决策钩子函数
    
    可以直接集成到Vedanta的回测或实盘系统中
    
    Args:
        vedanta_data: Vedanta的市场数据和信号
        
    Returns:
        处理后的决策结果
    """
    
    # 调用P1决策
    p1_decision = call_p1_enter_decision(vedanta_data)
    
    if p1_decision:
        # 将P1决策结果转换为Vedanta格式
        vedanta_result = {
            "action": "enter" if p1_decision.get("allow") else "skip",
            "side": p1_decision.get("side"),
            "size": p1_decision.get("alloc_equity_pct", 0.0),
            "confidence": len([r for r in p1_decision.get("reason_chain", []) if "PASS" in r]) / max(len(p1_decision.get("reason_chain", [])), 1),
            "reasons": p1_decision.get("reason_chain", []),
            "risk_metrics": p1_decision.get("risk"),
            "execution_params": p1_decision.get("exec"),
            "processing_time_ms": p1_decision.get("runtime_ms", 0)
        }
    else:
        # 决策失败，保守处理
        vedanta_result = {
            "action": "skip",
            "side": None,
            "size": 0.0,
            "confidence": 0.0,
            "reasons": ["P1 Decision API unavailable"],
            "risk_metrics": None,
            "execution_params": None,
            "processing_time_ms": 0
        }
    
    return vedanta_result


# 示例使用
def example_vedanta_integration():
    """示例：如何在Vedanta中集成P1决策"""
    
    # 模拟Vedanta的市场数据
    vedanta_market_data = {
        "symbol": "ETHUSDT",
        "price": 2415.3,
        "side_hint": "short",
        "timestamp": datetime.utcnow().isoformat(),
        "timeframe": "15m",
        "indicators": {
            "volatility": 0.0018,
            "skew": -0.72,
            "z_4h": -0.9,
            "z_1h": -0.7,
            "z_15m": -0.6,
            "c_align": 0.88,
            "c_of": 0.83,
            "c_vision": 0.79,
            "obi": 0.31,
            "dcvd": -1.2,
            "replenish": 0.67,
            "oi_roc": 0.08,
            "gas_z": 1.1,
            "spread_bp": 3.2,
            "depth_px": 1200000
        }
    }
    
    # 调用P1决策
    result = vedanta_enter_hook(vedanta_market_data)
    
    print("Vedanta-P1 Integration Result:")
    print(f"Action: {result['action']}")
    print(f"Side: {result['side']}")
    print(f"Size: {result['size']:.1%}")
    print(f"Confidence: {result['confidence']:.2f}")
    print(f"Reasons: {result['reasons']}")
    
    return result


if __name__ == "__main__":
    example_vedanta_integration()
