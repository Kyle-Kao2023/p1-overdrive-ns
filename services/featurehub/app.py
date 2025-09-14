"""FeatureHub Service FastAPI应用"""
import json
import random
from datetime import datetime, timedelta
from typing import Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from .schemas import FeatureResponse, MarketSnapshot, PineWebhook, SnapshotRequest, VisionTokens

app = FastAPI(
    title="P1 FeatureHub Service",
    description="Feature aggregation and normalization service",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 简单的内存存储（生产环境应使用Redis）
pine_signals: List[PineWebhook] = []
vision_tokens: List[VisionTokens] = []
market_snapshots: Dict[str, MarketSnapshot] = {}


@app.get("/")
async def root():
    """根端点"""
    return {
        "service": "P1 FeatureHub Service",
        "description": "Feature aggregation and normalization",
        "version": "0.1.0",
        "endpoints": {
            "pine_webhook": "/tv/webhook",
            "vision_tokens": "/vision/tokens",
            "market_snapshot": "/snapshot"
        }
    }


@app.post("/tv/webhook")
async def receive_pine_webhook(webhook: PineWebhook) -> FeatureResponse:
    """接收TradingView Pine Script Webhook"""
    try:
        logger.info(f"Pine webhook received: {webhook.symbol} {webhook.signal} @ {webhook.price}")
        
        # 存储信号
        pine_signals.append(webhook)
        
        # 保持最近100条记录
        if len(pine_signals) > 100:
            pine_signals[:] = pine_signals[-100:]
        
        # TODO: 发送到Redis或消息队列
        
        return FeatureResponse(
            success=True,
            message=f"Pine signal stored: {webhook.signal}",
            data={"signal_count": len(pine_signals)}
        )
        
    except Exception as e:
        logger.error(f"Error processing pine webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/vision/tokens")
async def receive_vision_tokens(tokens: VisionTokens) -> FeatureResponse:
    """接收YOLO/Vision识别tokens"""
    try:
        logger.info(f"Vision tokens received: {tokens.image_ref}, confidence: {tokens.confidence_overall}")
        
        # 存储tokens
        vision_tokens.append(tokens)
        
        # 保持最近50条记录
        if len(vision_tokens) > 50:
            vision_tokens[:] = vision_tokens[-50:]
        
        return FeatureResponse(
            success=True,
            message="Vision tokens stored",
            data={"token_count": len(vision_tokens)}
        )
        
    except Exception as e:
        logger.error(f"Error processing vision tokens: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/snapshot", response_model=MarketSnapshot)
async def get_market_snapshot(symbol: str = "ETHUSDT", timeframe: str = "15m") -> MarketSnapshot:
    """
    获取市场快照（合成数据用于本地测试）
    
    生产环境中，这里会聚合来自各个connector的实时数据
    """
    try:
        # 生成模拟市场快照
        snapshot = generate_synthetic_snapshot(symbol, timeframe)
        
        # 存储到内存
        market_snapshots[f"{symbol}_{timeframe}"] = snapshot
        
        logger.info(f"Market snapshot generated: {symbol} {timeframe}")
        return snapshot
        
    except Exception as e:
        logger.error(f"Error generating market snapshot: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "featurehub",
        "data_status": {
            "pine_signals": len(pine_signals),
            "vision_tokens": len(vision_tokens),
            "market_snapshots": len(market_snapshots)
        }
    }


def generate_synthetic_snapshot(symbol: str, timeframe: str) -> MarketSnapshot:
    """生成合成市场快照用于测试"""
    
    # 基础价格（模拟不同标的）
    base_prices = {
        "BTCUSDT": 43250.0,
        "ETHUSDT": 2415.0,
        "ADAUSDT": 0.382,
        "SOLUSDT": 98.5
    }
    
    base_price = base_prices.get(symbol, 2415.0)
    
    # 随机波动
    price_change = random.uniform(-0.02, 0.02)  # ±2%
    current_price = base_price * (1 + price_change)
    
    # 生成技术指标
    sigma_1m = random.uniform(0.0012, 0.0025)
    skew_1m = random.uniform(-1.0, 1.0)
    
    # Z-scores (相关性较强)
    base_z = random.uniform(-1.5, 1.5)
    z_4h = base_z + random.uniform(-0.3, 0.3)
    z_1h = base_z + random.uniform(-0.2, 0.2)
    z_15m = base_z + random.uniform(-0.1, 0.1)
    
    # 共识指标（基于Z-scores生成）
    c_align = max(0, min(1, 0.8 + abs(base_z) * 0.1 + random.uniform(-0.1, 0.1)))
    c_of = max(0, min(1, 0.75 + abs(base_z) * 0.15 + random.uniform(-0.05, 0.05)))
    c_vision = max(0, min(1, 0.7 + abs(base_z) * 0.2 + random.uniform(-0.1, 0.1)))
    
    # OrderFlow（与Z-scores相关）
    obi = max(-1, min(1, base_z * 0.5 + random.uniform(-0.2, 0.2)))
    dcvd = base_z * 1.5 + random.uniform(-0.5, 0.5)
    replenish = max(0, min(1, 0.6 + random.uniform(-0.2, 0.2)))
    
    # 市场微结构
    spread_bp = random.uniform(2, 8)
    depth_px = random.uniform(800000, 2000000)
    
    # 链上数据
    oi_roc = random.uniform(-0.1, 0.1)
    gas_z = random.uniform(-2, 2)
    
    return MarketSnapshot(
        symbol=symbol,
        timestamp=datetime.utcnow(),
        mark_price=current_price,
        spread_bp=spread_bp,
        depth_px=depth_px,
        volume_24h=random.uniform(10000000, 50000000),
        sigma_1m=sigma_1m,
        skew_1m=skew_1m,
        z_scores={"4H": z_4h, "1H": z_1h, "15m": z_15m},
        c_align=c_align,
        c_of=c_of,
        c_vision=c_vision,
        orderflow={"obi": obi, "dCVD": dcvd, "replenish": replenish},
        onchain={"oi_roc": oi_roc, "gas_z": gas_z}
    )


@app.get("/data/pine/recent")
async def get_recent_pine_signals(limit: int = 10):
    """获取最近的Pine信号"""
    return {
        "signals": pine_signals[-limit:],
        "total_count": len(pine_signals)
    }


@app.get("/data/vision/recent")
async def get_recent_vision_tokens(limit: int = 5):
    """获取最近的Vision tokens"""
    return {
        "tokens": vision_tokens[-limit:],
        "total_count": len(vision_tokens)
    }


if __name__ == "__main__":
    import uvicorn
    
    logger.info("🌟 Starting FeatureHub Service on port 8010")
    
    uvicorn.run(
        "services.featurehub.app:app",
        host="0.0.0.0",
        port=8010,
        reload=True
    )
