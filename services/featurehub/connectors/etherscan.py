"""Etherscan Gas连接器 (Stub)"""
from loguru import logger

class EtherscanConnector:
    def __init__(self):
        logger.info("Etherscan Connector (STUB)")
    
    def get_gas_data(self):
        return {"gas_z": 1.2}
