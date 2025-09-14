"""Decision Service FastAPI应用主文件"""
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from .core.config import config_manager
from .core.logging import setup_logging
from .routes import decide_enter, decide_exit, health


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时的初始化
    logger.info("🚀 Starting P1 Decision Service...")
    
    # 设置日志
    setup_logging()
    
    # 加载模型（当前为stub）
    try:
        from .models.ctfg import ctfg_model
        from .models.quantile import quantile_predictor
        
        ctfg_model.load_model()
        quantile_predictor.load_model()
        
        logger.info("✅ Models loaded successfully")
    except Exception as e:
        logger.warning(f"⚠️  Model loading warning: {e}")
    
    # 验证配置
    gates_config = config_manager.get_gates_config()
    logger.info(f"📋 Gates config loaded: {len(gates_config)} parameters")
    
    logger.info("✅ Decision Service startup completed")
    
    yield
    
    # 关闭时的清理
    logger.info("🛑 Shutting down P1 Decision Service...")


# 创建FastAPI应用
app = FastAPI(
    title="P1 Decision Service",
    description="P1 Trading Builder - 100x No-Stop Decision System",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(health.router, tags=["Health"])
app.include_router(decide_enter.router, tags=["Enter Decision"])
app.include_router(decide_exit.router, tags=["Exit Decision"])


@app.get("/")
async def root():
    """根端点，返回服务简介"""
    return {
        "service": "P1 Decision Service",
        "description": "100x No-Stop Trading Decision System",
        "version": "0.1.0",
        "timestamp": datetime.utcnow().isoformat(),
        "endpoints": {
            "health": "/health",
            "docs": "/docs", 
            "enter_decision": "/decide/enter",
            "exit_decision": "/decide/exit"
        },
        "features": [
            "🔒 4-Gate Safety System (Vol/Consensus/LiqBuffer/Event)",
            "🧠 CTFG Loopy-BP Decision Engine",
            "📊 Real-time Risk Assessment",
            "⚡ <70ms Decision Latency",
            "🎯 Conformal Prediction Calibration",
            "📈 Dynamic MPC Exit Strategy"
        ],
        "gate_system": {
            "vol_gate": "Volatility Sweet-Spot Detection",
            "consensus_gate": "Multi-dimensional Consensus Check", 
            "liq_buffer_gate": "Liquidation Buffer Validation",
            "event_latency_gate": "Event Blacklist & Latency SLA"
        }
    }


@app.get("/api/info")
async def api_info():
    """API信息端点"""
    return {
        "api_version": "v1",
        "service_type": "decision_engine",
        "capabilities": {
            "enter_decisions": True,
            "exit_decisions": True,
            "real_time_processing": True,
            "risk_assessment": True,
            "reasoning_traces": True,
            "conformal_calibration": True
        },
        "model_status": {
            "ctfg_model": "loaded (stub)",
            "quantile_predictor": "loaded (stub)",
            "conformal_calibrator": "ready",
            "bocpd_hazard": "ready"
        },
        "configuration": {
            "environment": config_manager.settings.app_env,
            "latency_slo_ms": config_manager.get_latency_slo(),
            "gates_enabled": 4
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    # 从环境变量获取端口
    port = config_manager.settings.decision_port
    
    logger.info(f"🌟 Starting Decision Service on port {port}")
    
    uvicorn.run(
        "services.decision.app:app",
        host="0.0.0.0",
        port=port,
        reload=config_manager.settings.app_env == "dev",
        log_config=None  # 使用我们自己的日志配置
    )
