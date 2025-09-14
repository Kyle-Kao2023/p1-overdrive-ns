"""CoinGlass OI连接器 (Stub)"""
from loguru import logger

class CoinGlassConnector:
    def __init__(self):
        logger.info("CoinGlass Connector (STUB)")
    
    def get_oi_data(self, symbol: str):
        return {"oi_roc": 0.05}
