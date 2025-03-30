import os
from pathlib import Path
from dotenv import load_dotenv, dotenv_values

# 获取项目根目录
ROOT_DIR = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 明确指定.env文件路径
env_path = ROOT_DIR / '.env'

# 直接从.env文件读取值，而不是通过系统环境变量
env_values = dotenv_values(dotenv_path=env_path)

# 数据存储目录
DATA_DIR = ROOT_DIR / "data"
LOG_DIR = ROOT_DIR / "logs"

# API配置 - 优先使用.env文件中的设置，而不是系统环境变量
OPENAI_API_KEY = env_values.get("OPENAI_API_KEY", "")
DEEPSEEK_API_BASE = env_values.get("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1")

# 调试信息 - 仅显示密钥前几个字符，保护安全
api_key_display = OPENAI_API_KEY[:5] + "..." if OPENAI_API_KEY and len(OPENAI_API_KEY) > 5 else "未设置"
print(f"使用API密钥: {api_key_display}")
print(f"API基础URL: {DEEPSEEK_API_BASE}")
print(f"环境变量加载自: {env_path}")

# Tushare API配置
TUSHARE_TOKEN = env_values.get("TUSHARE_TOKEN", "")

# 恒生科技指数配置
HSTECH_INDEX_CODE = "HST50.HK"  # 恒生科技指数

# 股票池配置 (恒生科技指数前20权重股)
STOCK_POOL = {
    "9988.HK": "阿里巴巴",
    "0700.HK": "腾讯控股",
    "9618.HK": "京东集团",
    "1024.HK": "快手",
    "9888.HK": "百度集团",
    "0981.HK": "中芯国际",
    "9999.HK": "网易",
    "3690.HK": "美团",
    "1810.HK": "小米集团",
    "0992.HK": "联想集团",
    "9626.HK": "哔哩哔哩",
    "0268.HK": "金蝶国际",
    "2382.HK": "舜宇光学",
    "9923.HK": "医渡科技",
    "6969.HK": "思摩尔国际",
    "9991.HK": "百胜中国",
    "0968.HK": "信义光能",
    "1579.HK": "颐海国际",
    "1347.HK": "华虹半导体",
    "9898.HK": "微盟集团"
}

# 回测参数
BACKTEST_START = "2023-01-01"
BACKTEST_END = "2023-12-31"
INITIAL_CAPITAL = 1000000  # 初始资金100万

# 策略参数
BOLLINGER_PERIOD = 20
RSI_PERIOD = 14
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9

# Web应用配置
APP_HOST = "127.0.0.1"
APP_PORT = 8080

# 定时任务配置
DATA_UPDATE_TIME = "09:00"  # 每天早上9点更新数据
DAILY_STRATEGY_TIME = "16:00"  # 每天下午4点运行策略

# 日志配置
LOG_LEVEL = "INFO"
LOG_FORMAT = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"