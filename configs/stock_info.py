#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
股票信息映射，包含股票代码与名称的对应关系
"""

# 港股常用股票代码与名称映射
HK_STOCK_NAMES = {
    # 科技股
    "9988.HK": "阿里巴巴",
    "9999.HK": "网易",
    "0700.HK": "腾讯控股",
    "3690.HK": "美团",
    "9618.HK": "京东集团",
    "1810.HK": "小米集团",
    "0981.HK": "中芯国际",
    "1024.HK": "快手",
    "2269.HK": "药明生物",
    "1833.HK": "平安好医生",
    
    # 金融股
    "1398.HK": "工商银行",
    "0939.HK": "建设银行",
    "2318.HK": "中国平安",
    "3988.HK": "中国银行",
    "0388.HK": "香港交易所",
    "1299.HK": "友邦保险",
    
    # 消费股
    "2020.HK": "安踏体育",
    "1177.HK": "中国生物制药",
    "0291.HK": "华润啤酒",
    "0914.HK": "海螺水泥",
    "1919.HK": "中远海控",
    
    # 其他
    "0001.HK": "长和",
    "0002.HK": "中电控股",
    "0003.HK": "香港中华煤气",
    "0005.HK": "汇丰控股",
    "0006.HK": "电能实业",
    "0011.HK": "恒生银行",
    "0016.HK": "新鸿基地产",
    "0017.HK": "新世界发展",
    "0027.HK": "银河娱乐",
    "HSI.HK": "恒生指数",
    "HST50.HK": "恒生科技指数"
}

def get_stock_name(stock_code: str, default_name: str = None) -> str:
    """获取股票名称
    
    Args:
        stock_code: 股票代码
        default_name: 默认名称，当找不到对应名称时返回
        
    Returns:
        股票名称
    """
    if default_name is None:
        default_name = stock_code
        
    return HK_STOCK_NAMES.get(stock_code, default_name)

def get_stock_full_name(stock_code: str) -> str:
    """获取股票完整名称（代码+名称）
    
    Args:
        stock_code: 股票代码
        
    Returns:
        股票完整名称，格式为: 代码 (名称)
    """
    stock_name = get_stock_name(stock_code)
    if stock_name == stock_code:
        return stock_code
    else:
        return f"{stock_code} ({stock_name})" 