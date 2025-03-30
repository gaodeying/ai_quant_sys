import os
import argparse
import threading
from datetime import datetime
import time
import schedule
import sys

# 添加项目根目录到Python路径
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT_DIR)

from src.api.api_server import start_api_server
# 检查UI模块是否可用
try:
    from src.ui.app import start_ui
except ImportError:
    def start_ui(share=False):
        print("警告：UI模块未找到或存在导入错误，仅启动API服务")

from src.utils.logger import logger
from configs.config import (
    DATA_UPDATE_TIME, 
    DAILY_STRATEGY_TIME, 
    STOCK_POOL
)

from src.data.data_loader import DataLoader
# 检查models模块是否可用
try:
    from src.models.stock_analyzer import StockAnalyzer
except ImportError:
    try:
        from src.models.stock_analyzer import StockAnalyzer
    except ImportError:
        logger.error("无法导入StockAnalyzer，请确保模块存在")
        class StockAnalyzer:
            def __init__(self, *args, **kwargs):
                pass
            def analyze_stock_pool(self, *args, **kwargs):
                return {}
            def rank_stocks(self, *args, **kwargs):
                return []

from src.strategies.trading_strategy import StrategyFactory
from src.backtest.backtester import Backtester

def check_dependencies():
    """检查关键依赖是否可用"""
    missing_deps = []
    try:
        import pandas
    except ImportError:
        missing_deps.append("pandas")
    try:
        import numpy
    except ImportError:
        missing_deps.append("numpy")
    try:
        import fastapi
    except ImportError:
        missing_deps.append("fastapi")
    try:
        import uvicorn
    except ImportError:
        missing_deps.append("uvicorn")
        
    if missing_deps:
        logger.error(f"缺少关键依赖: {', '.join(missing_deps)}")
        logger.error("请运行: pip install -r requirements.txt")
        return False
    return True

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="AI量化交易系统")
    parser.add_argument("--api-only", action="store_true", help="仅启动API服务")
    parser.add_argument("--ui-only", action="store_true", help="仅启动UI服务")
    parser.add_argument("--no-scheduler", action="store_true", help="不启动定时任务")
    parser.add_argument("--debug", action="store_true", help="启用调试模式")
    return parser.parse_args()

def update_data():
    """更新股票数据的定时任务"""
    logger.info("开始执行数据更新定时任务")
    
    data_loader = DataLoader()
    today = datetime.now().strftime('%Y-%m-%d')
    
    # 更新指数数据
    try:
        logger.info("更新恒生科技指数数据")
        data_loader.get_index_data("HST50.HK", "2023-01-01", today, use_cache=False)
    except Exception as e:
        logger.error(f"更新指数数据失败: {str(e)}")
    
    # 更新股票池数据
    for stock_code in STOCK_POOL.keys():
        try:
            logger.info(f"更新股票数据: {stock_code}")
            data_loader.get_stock_data(stock_code, "2023-01-01", today, use_cache=False)
        except Exception as e:
            logger.error(f"更新股票数据失败: {stock_code}, 错误: {str(e)}")
    
    logger.info("数据更新定时任务完成")

def run_daily_strategy():
    """执行每日策略分析的定时任务"""
    logger.info("开始执行每日策略分析")
    
    data_loader = DataLoader()
    stock_analyzer = StockAnalyzer(data_loader)
    
    # 分析股票池
    try:
        logger.info("开始分析股票池")
        analysis_results = stock_analyzer.analyze_stock_pool(days=90)
        
        # 排名
        rankings = stock_analyzer.rank_stocks(analysis_results)
        
        # 打印排名靠前的股票
        logger.info("今日股票推荐排名:")
        for item in rankings[:5]:
            logger.info(f"{item['stock_code']}: {item['action']}, 评分: {item['rank_score']}")
    except Exception as e:
        logger.error(f"股票池分析失败: {str(e)}")
    
    logger.info("每日策略分析完成")

def setup_scheduler():
    """设置定时任务"""
    logger.info("设置定时任务")
    
    # 每日更新数据
    schedule.every().day.at(DATA_UPDATE_TIME).do(update_data)
    logger.info(f"已设置数据更新任务，执行时间: 每日 {DATA_UPDATE_TIME}")
    
    # 每日执行策略
    schedule.every().day.at(DAILY_STRATEGY_TIME).do(run_daily_strategy)
    logger.info(f"已设置策略分析任务，执行时间: 每日 {DAILY_STRATEGY_TIME}")
    
    # 启动一个线程来运行定时任务
    def run_scheduler():
        while True:
            schedule.run_pending()
            time.sleep(60)  # 每分钟检查一次是否有待执行的任务
    
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    logger.info("定时任务调度器已启动")

def main():
    """主程序入口"""
    args = parse_args()
    
    # 检查依赖项
    if not check_dependencies():
        return
    
    if args.debug:
        logger.info("已启用调试模式")
    
    # 初始化必要的目录
    for dir_path in ["data", "logs", "data/backtest_results"]:
        os.makedirs(os.path.join(ROOT_DIR, dir_path), exist_ok=True)
    
    # 设置定时任务（如果未禁用）
    if not args.no_scheduler:
        setup_scheduler()
    
    # 启动 API 服务
    if not args.ui_only:
        logger.info("启动 API 服务")
        api_thread = threading.Thread(target=start_api_server, daemon=True)
        api_thread.start()
    
    # 启动 UI 服务（如果未禁用）
    if not args.api_only:
        logger.info("启动 UI 服务")
        if args.ui_only:
            # 如果只启动UI，则直接运行（非后台）
            start_ui(share=args.debug)
        else:
            # 否则在单独的线程中运行
            ui_thread = threading.Thread(target=start_ui, args=(args.debug,))
            ui_thread.start()
            
            # 等待UI线程退出
            ui_thread.join()
    else:
        # 如果只启动API，则保持主线程运行
        logger.info("系统已启动，按Ctrl+C退出")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("接收到退出信号，正在关闭系统...")

if __name__ == "__main__":
    main()