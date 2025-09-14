"""日志配置模块"""
import sys
from loguru import logger
from .config import config_manager


def setup_logging() -> None:
    """设置日志配置"""
    # 移除默认handler
    logger.remove()
    
    # 获取日志级别
    log_level = config_manager.settings.log_level
    
    # 添加控制台输出
    logger.add(
        sys.stdout,
        level=log_level,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        ),
        colorize=True,
    )
    
    # 添加文件输出（在生产环境）
    if config_manager.settings.app_env == "prod":
        logger.add(
            "logs/decision_{time:YYYY-MM-DD}.log",
            level=log_level,
            rotation="1 day",
            retention="30 days",
            compression="zip",
            format=(
                "{time:YYYY-MM-DD HH:mm:ss} | "
                "{level: <8} | "
                "{name}:{function}:{line} | "
                "{message}"
            ),
        )
    
    logger.info(f"Logging initialized with level: {log_level}")


def get_logger(name: str = __name__):
    """获取logger实例"""
    return logger.bind(name=name)
