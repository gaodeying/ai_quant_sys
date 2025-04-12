#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
股票信息配置

包含股票代码、名称和其他相关信息的映射
"""

from typing import Dict, Optional
from configs.config import STOCK_POOL

def get_stock_name(stock_code: str) -> str:
    """获取股票简称
    
    Args:
        stock_code: 股票代码
        
    Returns:
        股票简称
    """
    if stock_code in STOCK_POOL:
        # 返回简称（去掉后缀）
        full_name = STOCK_POOL[stock_code]
        return full_name.split('-')[0]
    return stock_code

def get_stock_full_name(stock_code: str) -> str:
    """获取股票完整名称
    
    Args:
        stock_code: 股票代码
        
    Returns:
        股票完整名称
    """
    return STOCK_POOL.get(stock_code, stock_code) 