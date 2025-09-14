"""Binance WebSocket连接器 (Stub)"""
from loguru import logger

class BinanceWSConnector:
    def __init__(self):
        logger.info("Binance WS Connector (STUB)")
    
    def connect(self):
        return True
    
    def get_orderbook(self, symbol: str):
        return {"bids": [], "asks": []}
