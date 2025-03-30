#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试DeepSeek客户端连接和功能
"""

import os
import sys
import json
import argparse
from pathlib import Path

# 添加项目根目录到sys.path
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from src.utils.deepseek_client import DeepSeekClient
from src.utils.logger import logger
from configs.config import OPENAI_API_KEY, DEEPSEEK_API_BASE

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="测试DeepSeek客户端功能")
    parser.add_argument("--mock", action="store_true", help="强制使用模拟模式")
    parser.add_argument("--api-key", type=str, help="指定API密钥")
    parser.add_argument("--api-base", type=str, help="指定API基础URL")
    return parser.parse_args()

def print_header(title, char="="):
    """打印漂亮的标题"""
    print(f"\n{char * 50}")
    print(f"{title}")
    print(f"{char * 50}")

def test_connection(client):
    """测试DeepSeek API连接"""
    print_header("测试DeepSeek API连接", "*")
    
    result = client.test_connection()
    
    if result["status"] == "success":
        print(f"✅ API连接成功: {result['message']}")
        if "details" in result and "data" in result["details"]:
            print(f"可用模型列表:")
            for model in result["details"]["data"]:
                print(f"  - {model['id']}")
    else:
        print(f"❌ API连接失败: {result['message']}")
        api_key_display = OPENAI_API_KEY[:5] + "..." if OPENAI_API_KEY and len(OPENAI_API_KEY) > 5 else "未设置"
        print(f"请检查您的API密钥设置。当前API密钥: {api_key_display}")
        print("您可以在.env文件中设置OPENAI_API_KEY或使用--api-key参数")
    
    print(f"\n当前模式: {'模拟模式' if client.mock_mode else 'API模式'}")
    print()

def test_chat_completion(client):
    """测试聊天完成功能"""
    print_header("测试DeepSeek聊天功能", "*")
    
    messages = [
        {"role": "system", "content": "你是一个有用的助手。"},
        {"role": "user", "content": "请解释什么是量化交易并举一个简单的例子。"}
    ]
    
    print("发送请求中...")
    print(f"当前模式: {'模拟模式' if client.mock_mode else 'API模式'}")
    response = client.chat_completion(messages, temperature=0.3)
    
    print("\n响应结果:")
    if hasattr(response, "choices") and len(response.choices) > 0:
        print(response.choices[0].message.content)
    else:
        print("未获取到有效响应")
    
    print()

def test_analyze_stock(client):
    """测试股票分析功能"""
    print_header("测试股票分析功能", "*")
    
    # 模拟股票数据
    stock_data = {
        "price_data": "收盘价: 130.5, 最高价: 135.2, 最低价: 128.9",
        "technical_indicators": "RSI: 56.7, MACD: 2.5, 信号线: 1.8, MA5: 131.2, MA20: 128.4",
        "fundamental_data": "市盈率: 25.3, 市净率: 4.8, 净利润增长率: 18.7%",
        "market_environment": "恒生指数近期上涨3.2%, 港股科技股整体表现积极"
    }
    
    print("分析中...")
    print(f"当前模式: {'模拟模式' if client.mock_mode else 'API模式'}")
    analysis = client.analyze_stock("9988.HK", stock_data)
    
    print("\n分析结果:")
    print(analysis)
    print()

def main():
    """主函数"""
    args = parse_args()
    
    print_header("DeepSeek客户端测试程序")
    print(f"API基础URL: {args.api_base or DEEPSEEK_API_BASE}")
    print(f"API密钥: {(args.api_key or OPENAI_API_KEY)[:5]}..." if args.api_key or OPENAI_API_KEY else "未设置")
    print(f"强制模拟模式: {'是' if args.mock else '否'}")
    
    # 创建客户端
    client = DeepSeekClient(
        api_key=args.api_key,
        api_base=args.api_base,
        mock_mode=args.mock
    )
    
    test_connection(client)
    test_chat_completion(client)
    test_analyze_stock(client)

if __name__ == "__main__":
    main() 