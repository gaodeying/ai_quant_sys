"""
配置文件

包含系统所需的所有配置常量和设置
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

# 加载环境变量
load_dotenv()

# 项目根目录
ROOT_DIR = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 数据目录
DATA_DIR = ROOT_DIR / "data"
CACHE_DIR = DATA_DIR / "cache"
BACKTEST_DIR = DATA_DIR / "backtest_results"

# 日志目录
LOG_DIR = ROOT_DIR / "logs"

# API密钥
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_API_BASE = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1")

# 数据源配置
TUSHARE_TOKEN = os.getenv("TUSHARE_TOKEN")
AKSHARE_TOKEN = os.getenv("AKSHARE_TOKEN")

# 数据更新时间
DATA_UPDATE_TIME = "09:30"  # 每日数据更新时间
DAILY_STRATEGY_TIME = "09:45"  # 每日策略执行时间

# 恒生科技指数代码
HSTECH_INDEX_CODE = "HST50.HK"

# 股票池配置
STOCK_POOL = {
    "9618.HK": "京东集团-SW",
    "9999.HK": "网易-S",
    "9988.HK": "阿里巴巴-SW",
    "0700.HK": "腾讯控股",
    "9626.HK": "哔哩哔哩-SW",
    "1024.HK": "快手-W",
    "3690.HK": "美团-W",
    "9888.HK": "百度集团-SW"
}

# 数据缓存设置
CACHE_EXPIRY = 24 * 60 * 60  # 缓存过期时间（秒）

# 回测设置
BACKTEST_START = "2023-01-01"  # 回测开始日期
BACKTEST_END = datetime.now().strftime('%Y-%m-%d')  # 回测结束日期（默认为当前日期）
INITIAL_CAPITAL = 1000000  # 初始资金

# 交易设置
MAX_POSITION_SIZE = 0.3  # 单个股票最大仓位
STOP_LOSS_PCT = 0.1  # 止损比例
TAKE_PROFIT_PCT = 0.2  # 止盈比例

# 技术指标参数
TECHNICAL_PARAMS = {
    "RSI_PERIOD": 14,
    "MACD_FAST": 12,
    "MACD_SLOW": 26,
    "MACD_SIGNAL": 9,
    "BB_PERIOD": 20,
    "BB_STD": 2
}

# 日志设置
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"

# API服务器设置
API_HOST = "0.0.0.0"
API_PORT = 8000
API_WORKERS = 4

# UI设置
UI_PORT = 7860
UI_SHARE = False  # 是否公开分享UI

# 调试模式
DEBUG = os.getenv("DEBUG", "False").lower() == "true"