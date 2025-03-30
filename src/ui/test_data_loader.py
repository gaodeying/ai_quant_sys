import os
import sys
import pandas as pd
from datetime import datetime, timedelta

# 获取项目根目录
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT_DIR)

from src.data.data_loader import DataLoader
from src.utils.logger import logger

def test_stock_data():
    """测试股票数据加载功能"""
    data_loader = DataLoader()
    
    # 设置日期范围
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    # 测试阿里巴巴数据
    stock_code = "9988.HK"
    logger.info(f"测试获取股票数据: {stock_code}, 日期范围: {start_date} 至 {end_date}")
    
    # 强制不使用缓存
    stock_data = data_loader.get_stock_data(stock_code, start_date, end_date, use_cache=False)
    
    if stock_data.empty:
        logger.error(f"获取股票数据失败: {stock_code}")
    else:
        logger.info(f"成功获取股票数据: {stock_code}, 数据行数: {len(stock_data)}")
        logger.info(f"数据列: {stock_data.columns.tolist()}")
        logger.info(f"数据示例:\n{stock_data.head()}")
    
    return stock_data

if __name__ == "__main__":
    test_stock_data() 