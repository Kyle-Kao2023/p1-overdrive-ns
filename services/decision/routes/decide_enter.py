"""入场决策API路由"""
from fastapi import APIRouter, HTTPException
from loguru import logger

from ..decision.reasoner import decide_enter
from ..decision.trace import ReasoningTrace, generate_human_readable_reasoning, store_trace
from ..schemas.features import EnterRequest
from ..schemas.responses import EnterResponse
from ..schemas.examples import EXAMPLE_ENTER_BULL, EXAMPLE_ENTER_BEAR, EXAMPLE_ENTER_REJECT_VOL

router = APIRouter()


@router.post("/decide/enter", response_model=EnterResponse)
async def decide_enter_endpoint(request: EnterRequest) -> EnterResponse:
    """
    入场决策API
    
    接收市场特征和PGM指标，返回入场决策结果
    
    决策流程：
    1. Gate检查（Event/Latency, Vol, Consensus, Liq-Buffer）
    2. CTFG模型推理 
    3. 脆弱性测试
    4. 生成决策和推理链
    """
    # 创建推理追踪
    trace = ReasoningTrace()
    trace.add_step("Request_Received", "OK", {
        "symbol": request.symbol,
        "side_hint": request.side_hint,
        "tf": request.tf
    })
    
    try:
        logger.info(f"Enter decision request: {request.symbol} {request.side_hint} @ {request.ts}")
        
        # 执行决策
        response = decide_enter(request)
        
        # 记录决策结果
        trace.add_decision(response)
        
        # 存储追踪
        store_trace(trace)
        
        # 生成人类可读的推理说明（用于日志）
        human_reasoning = generate_human_readable_reasoning(request, response, trace)
        logger.info(f"Decision completed:\n{human_reasoning}")
        
        return response
        
    except Exception as e:
        logger.error(f"Error in enter decision: {e}")
        trace.add_step("Error", str(e))
        store_trace(trace)
        
        raise HTTPException(
            status_code=500,
            detail=f"Decision processing error: {str(e)}"
        )


@router.get("/decide/enter/examples")
async def get_enter_examples():
    """获取入场决策的示例请求"""
    return {
        "bull_scenario": EXAMPLE_ENTER_BULL,
        "bear_scenario": EXAMPLE_ENTER_BEAR,
        "reject_vol_scenario": EXAMPLE_ENTER_REJECT_VOL,
        "description": {
            "bull_scenario": "看涨场景，所有指标有利于多头入场",
            "bear_scenario": "看跌场景，所有指标有利于空头入场", 
            "reject_vol_scenario": "被Vol Gate拒绝的场景，波动率超出甜蜜点"
        }
    }


@router.post("/decide/enter/test")
async def test_enter_scenarios():
    """测试不同入场场景"""
    scenarios = [
        ("Bull Scenario", EXAMPLE_ENTER_BULL),
        ("Bear Scenario", EXAMPLE_ENTER_BEAR),
        ("Vol Reject Scenario", EXAMPLE_ENTER_REJECT_VOL)
    ]
    
    results = []
    
    for scenario_name, example_data in scenarios:
        try:
            # 创建请求对象
            test_request = EnterRequest(**example_data)
            
            # 执行决策
            response = decide_enter(test_request)
            
            results.append({
                "scenario": scenario_name,
                "success": True,
                "result": {
                    "allow": response.allow,
                    "side": response.side,
                    "allocation": response.alloc_equity_pct,
                    "runtime_ms": response.runtime_ms,
                    "reason_count": len(response.reason_chain)
                }
            })
            
        except Exception as e:
            results.append({
                "scenario": scenario_name,
                "success": False,
                "error": str(e)
            })
    
    return {
        "test_completed": True,
        "scenarios_tested": len(scenarios),
        "results": results
    }
