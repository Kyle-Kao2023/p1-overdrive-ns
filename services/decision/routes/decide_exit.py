"""退出决策API路由"""
from fastapi import APIRouter, HTTPException
from loguru import logger

from ..execution.mpc_exit import decide_exit, simulate_exit_scenarios
from ..schemas.features import ExitRequest
from ..schemas.responses import ExitResponse
from ..schemas.examples import EXAMPLE_EXIT

router = APIRouter()


@router.post("/decide/exit", response_model=ExitResponse)
async def decide_exit_endpoint(request: ExitRequest) -> ExitResponse:
    """
    退出决策API
    
    接收持仓信息和实时更新，返回退出决策结果
    
    决策基于：
    1. Hazard率 h(t)
    2. P_hit衰减
    3. OrderFlow反转
    4. 时间超时风险
    5. 盈利保护
    """
    try:
        logger.info(
            f"Exit decision request: {request.position.side} "
            f"{request.position.qty} @ {request.position.avg_entry}, "
            f"UPL: {request.position.upl_pct:.2%}, "
            f"H(t): {request.updates.h_t:.3f}, "
            f"P_hit: {request.updates.p_hit:.3f}"
        )
        
        # 执行退出决策
        response = decide_exit(request)
        
        logger.info(
            f"Exit decision: {response.action}"
            f"{f' ({response.reduce_pct:.1%})' if response.reduce_pct else ''} "
            f"in {response.runtime_ms}ms"
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error in exit decision: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Exit decision processing error: {str(e)}"
        )


@router.get("/decide/exit/examples")
async def get_exit_examples():
    """获取退出决策的示例请求"""
    return {
        "example_exit": EXAMPLE_EXIT,
        "description": "标准退出决策示例，包含持仓信息和实时更新数据"
    }


@router.post("/decide/exit/test")
async def test_exit_scenarios():
    """测试不同退出场景"""
    # 基础持仓数据
    base_position = {
        "avg_entry": 2415.0,
        "side": "short",
        "qty": 120,
        "upl_pct": 0.42
    }
    
    try:
        # 运行场景模拟
        results = simulate_exit_scenarios(base_position)
        
        return {
            "test_completed": True,
            "scenarios_tested": len(results),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error in exit scenario testing: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Exit scenario testing error: {str(e)}"
        )


@router.get("/decide/exit/strategies")
async def get_exit_strategies():
    """获取退出策略说明"""
    return {
        "strategies": {
            "hold": {
                "description": "保持当前持仓，所有信号在可接受范围内",
                "conditions": ["Hazard < threshold", "P_hit > floor", "OrderFlow稳定"]
            },
            "reduce": {
                "description": "部分减仓，降低风险暴露",
                "conditions": ["Hazard超过阈值", "P_hit低于floor", "OrderFlow反转"],
                "typical_reduction": "30-80%"
            },
            "close": {
                "description": "完全平仓，风险过高",
                "conditions": ["Critical hazard", "Critical p_hit", "极端市况"],
                "reduction": "100%"
            },
            "trail": {
                "description": "盈利保护，追踪止盈",
                "conditions": ["有盈利", "Hazard适中上升", "保护利润"],
                "typical_reduction": "15-50%"
            }
        },
        "risk_factors": {
            "hazard_rate": {
                "description": "市场regime shift概率",
                "threshold": 0.30,
                "critical": 0.45
            },
            "p_hit_decay": {
                "description": "命中概率衰减",
                "floor": 0.50,
                "critical": 0.30
            },
            "orderflow_flip": {
                "description": "订单流方向反转",
                "threshold": "dCVD > ±1.5"
            },
            "timing_pressure": {
                "description": "持仓时间过长风险",
                "grace_bars": 3,
                "timeout_bars": 15
            }
        }
    }
