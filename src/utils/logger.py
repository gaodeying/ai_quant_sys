import os
import sys
from loguru import logger
from pathlib import Path
from datetime import datetime

# 获取项目根目录
ROOT_DIR = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 尝试加载配置
try:
    sys.path.insert(0, str(ROOT_DIR))
    from configs.config import LOG_DIR, LOG_LEVEL, LOG_FORMAT
except ImportError:
    # 默认配置
    LOG_DIR = ROOT_DIR / "logs"
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"

# 确保日志目录存在
os.makedirs(LOG_DIR, exist_ok=True)

# 生成日志文件路径（按日期分类）
log_file = LOG_DIR / f"{datetime.now().strftime('%Y-%m-%d')}.log"

# 配置日志记录器
logger.remove()  # 删除默认记录器

# 添加控制台记录器
logger.add(
    sys.stderr,
    format=LOG_FORMAT,
    level=LOG_LEVEL,
    colorize=True
)

# 添加文件记录器
logger.add(
    log_file,
    format=LOG_FORMAT,
    level=LOG_LEVEL,
    rotation="1 day",    # 每天轮换日志文件
    compression="zip",   # 压缩旧日志
    retention="30 days", # 保留30天的日志
    encoding="utf-8"
)

# 添加系统信息日志
logger.info(f"日志系统初始化完成，日志级别: {LOG_LEVEL}，日志目录: {LOG_DIR}")
logger.debug(f"项目根目录: {ROOT_DIR}")

__all__ = ["logger"] 