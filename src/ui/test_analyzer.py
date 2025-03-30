#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试股票分析器功能
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

# 添加项目根目录到sys.path
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from src.models.stock_analyzer import StockAnalyzer
from src.data.data_loader import DataLoader
from src.utils.logger import logger
from configs.config import STOCK_POOL
from configs.stock_info import get_stock_full_name

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="测试股票分析器功能")
    parser.add_argument("--stock", type=str, default="9988.HK", help="要分析的股票代码")
    parser.add_argument("--days", type=int, default=90, help="分析的历史天数")
    parser.add_argument("--pool", action="store_true", help="分析整个股票池")
    return parser.parse_args()

def test_stock_analyzer(stock_code="9988.HK", days=90):
    """测试单个股票分析功能"""
    # 获取股票完整名称
    stock_full_name = get_stock_full_name(stock_code)
    
    logger.info(f"测试分析股票: {stock_full_name}, 天数: {days}")
    
    # 创建数据加载器和股票分析器
    data_loader = DataLoader()
    analyzer = StockAnalyzer(data_loader)
    
    # 分析股票
    result = analyzer.analyze_stock(stock_code, days)
    
    # 输出分析结果
    logger.info("分析成功！获取到的信息:")
    logger.info(f"股票代码: {result.get('stock_code')}")
    logger.info(f"股票名称: {result.get('stock_name')}")
    logger.info(f"分析日期: {result.get('analysis_date')}")
    logger.info(f"期间: {result.get('period')}")
    
    # 输出交易信号
    signal = result.get("trading_signal", {})
    logger.info(f"交易信号: {signal.get('action', '未知')}")
    logger.info(f"置信度: {signal.get('confidence', 0)}")
    logger.info(f"理由: {signal.get('reason', '无')}")
    
    # 输出技术指标
    logger.info("技术指标:")
    indicators = result.get("technical_indicators", {})
    for key, value in indicators.items():
        logger.info(f"  {key}: {value}")
    
    return result

def test_stock_pool(days=90):
    """测试股票池分析功能"""
    logger.info(f"测试分析股票池, 共{len(STOCK_POOL)}支股票, 天数: {days}")
    
    # 创建数据加载器和股票分析器
    data_loader = DataLoader()
    analyzer = StockAnalyzer(data_loader)
    
    # 分析股票池
    results = analyzer.analyze_stock_pool(days)
    
    # 输出分析结果
    logger.info(f"分析成功！共分析{len(results)}/{len(STOCK_POOL)}支股票")
    
    # 对股票进行排名
    ranked_stocks = analyzer.rank_stocks(results)
    
    # 输出排名前5的股票
    logger.info("排名前5的股票:")
    for i, stock in enumerate(ranked_stocks[:5]):
        stock_full_name = get_stock_full_name(stock["stock_code"])
        logger.info(f"{i+1}. {stock_full_name}: {stock.get('action')} (置信度: {stock.get('confidence')})")
    
    return results, ranked_stocks

def main():
    """主函数"""
    args = parse_args()
    
    if args.pool:
        test_stock_pool(args.days)
    else:
        test_stock_analyzer(args.stock, args.days)

if __name__ == "__main__":
    main() 