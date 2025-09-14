"""Vedanta退出适配器"""
import requests
from datetime import datetime
from typing import Dict, Optional


DECISION_URL = "http://localhost:8000"


def vedanta_to_exit_request(vedanta_position: Dict, market_updates: Dict) -> Dict:
    """
    将Vedanta的持仓和市场更新数据转换为Decision API的ExitRequest格式
    
    Args:
        vedanta_position: Vedanta持仓信息
        market_updates: 实时市场更新
        
    Returns:
        Decision API兼容的退出请求字典
    """
    
    # 持仓信息
    position = {
        "avg_entry": vedanta_position.get("entry_price", 0.0),
        "side": vedanta_position.get("side", "long"),
        "qty": vedanta_position.get("quantity", 0.0),
        "upl_pct": vedanta_position.get("unrealized_pnl_pct", 0.0)
    }
    
    # 实时更新数据
    updates = {
        "p_hit": market_updates.get("p_hit", 0.65),
        "mae_q90": market_updates.get("mae_q90", 0.003),
        "t_hit_q50_bars": market_updates.get("t_hit_q50_bars", 8),
        "h_t": market_updates.get("hazard_rate", 0.25),
        "dCVD": market_updates.get("dcvd", 0.0),
        "replenish": market_updates.get("replenish", 0.6)
    }
    
    return {
        "position": position,
        "updates": updates
    }


def call_p1_exit_decision(vedanta_position: Dict, market_updates: Dict, timeout: float = 0.05) -> Optional[Dict]:
    """
    调用P1决策API进行退出决策
    
    Args:
        vedanta_position: Vedanta持仓信息
        market_updates: 实时市场更新
        timeout: API超时时间（秒）
        
    Returns:
        决策结果字典，如果失败返回None
    """
    try:
        # 转换数据格式
        exit_request = vedanta_to_exit_request(vedanta_position, market_updates)
        
        # 调用P1 Decision API
        response = requests.post(
            f"{DECISION_URL}/decide/exit",
            json=exit_request,
            timeout=timeout
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"P1 Decision API error: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"Error calling P1 exit decision: {e}")
        return None


def vedanta_exit_hook(vedanta_position: Dict, market_updates: Dict) -> Dict:
    """
    Vedanta退出决策钩子函数
    
    可以直接集成到Vedanta的持仓管理系统中
    
    Args:
        vedanta_position: Vedanta持仓信息
        market_updates: 实时市场更新
        
    Returns:
        处理后的退出决策结果
    """
    
    # 调用P1退出决策
    p1_decision = call_p1_exit_decision(vedanta_position, market_updates)
    
    if p1_decision:
        action = p1_decision.get("action", "hold")
        
        if action == "hold":
            vedanta_result = {
                "action": "hold",
                "reduce_percentage": 0.0,
                "urgency": "low",
                "reasons": p1_decision.get("reason", []),
                "processing_time_ms": p1_decision.get("runtime_ms", 0)
            }
        elif action == "reduce":
            vedanta_result = {
                "action": "reduce",
                "reduce_percentage": p1_decision.get("reduce_pct", 0.5),
                "urgency": "medium",
                "reasons": p1_decision.get("reason", []),
                "processing_time_ms": p1_decision.get("runtime_ms", 0)
            }
        elif action == "close":
            vedanta_result = {
                "action": "close",
                "reduce_percentage": 1.0,
                "urgency": "high",
                "reasons": p1_decision.get("reason", []),
                "processing_time_ms": p1_decision.get("runtime_ms", 0)
            }
        elif action == "trail":
            vedanta_result = {
                "action": "trail",
                "reduce_percentage": p1_decision.get("reduce_pct", 0.3),
                "urgency": "low",
                "reasons": p1_decision.get("reason", []),
                "processing_time_ms": p1_decision.get("runtime_ms", 0)
            }
        else:
            vedanta_result = {
                "action": "hold",
                "reduce_percentage": 0.0,
                "urgency": "low",
                "reasons": ["Unknown P1 action"],
                "processing_time_ms": p1_decision.get("runtime_ms", 0)
            }
    else:
        # 决策失败，保守处理
        vedanta_result = {
            "action": "hold",
            "reduce_percentage": 0.0,
            "urgency": "unknown",
            "reasons": ["P1 Decision API unavailable"],
            "processing_time_ms": 0
        }
    
    return vedanta_result


# 示例使用
def example_vedanta_exit_integration():
    """示例：如何在Vedanta中集成P1退出决策"""
    
    # 模拟Vedanta的持仓信息
    vedanta_position = {
        "entry_price": 2415.0,
        "side": "short",
        "quantity": 120.0,
        "unrealized_pnl_pct": 0.42  # 42bp盈利
    }
    
    # 模拟实时市场更新
    market_updates = {
        "p_hit": 0.46,          # P_hit衰减
        "mae_q90": 0.0035,
        "t_hit_q50_bars": 12,   # 持仓时间过长
        "hazard_rate": 0.37,    # Hazard上升
        "dcvd": 0.9,            # OrderFlow反转
        "replenish": 0.25       # 补单率下降
    }
    
    # 调用P1退出决策
    result = vedanta_exit_hook(vedanta_position, market_updates)
    
    print("Vedanta-P1 Exit Integration Result:")
    print(f"Action: {result['action']}")
    print(f"Reduce Percentage: {result['reduce_percentage']:.1%}")
    print(f"Urgency: {result['urgency']}")
    print(f"Reasons: {result['reasons']}")
    print(f"Processing Time: {result['processing_time_ms']}ms")
    
    return result


if __name__ == "__main__":
    example_vedanta_exit_integration()
