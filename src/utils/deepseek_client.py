import os
import json
from typing import Dict, Any, Optional
from datetime import datetime
import httpx
from loguru import logger
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class DeepSeekClient:
    """DeepSeek API 客户端封装"""
    
    def __init__(self, mock_mode: bool = False):
        """初始化 DeepSeek 客户端
        
        Args:
            mock_mode: 是否使用模拟模式（用于测试）
        """
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        self.mock_mode = mock_mode
        self.base_url = "https://api.deepseek.com/v1"
        self.timeout = 120.0  # 设置超时时间为120秒
        self.max_retries = 3  # 最大重试次数
        
        # 初始化 HTTP 客户端，设置较长的超时时间
        self.client = httpx.Client(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=self.timeout
        )
        
        # 如果不是模拟模式，测试连接
        if not mock_mode:
            try:
                test_result = self.test_connection()
                if test_result["status"] == "success":
                    logger.info("DeepSeek API连接测试成功，已切换到API模式")
                else:
                    logger.warning(f"DeepSeek API连接测试失败: {test_result['message']}，将使用模拟模式")
                    self.mock_mode = True
            except Exception as e:
                logger.error(f"DeepSeek API初始化错误: {str(e)}，将使用模拟模式")
                self.mock_mode = True
    
    def test_connection(self) -> Dict[str, str]:
        """测试API连接
        
        Returns:
            测试结果字典
        """
        if self.mock_mode:
            return {"status": "success", "message": "模拟模式下的连接测试"}
            
        try:
            response = self.client.get("/health")
            if response.status_code == 200:
                return {"status": "success", "message": "API连接正常"}
            else:
                return {
                    "status": "error",
                    "message": f"API连接失败: {response.status_code}"
                }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def analyze_stock(self, stock_code: str, stock_data: Dict[str, Any]) -> str:
        """分析股票数据
        
        Args:
            stock_code: 股票代码
            stock_data: 股票数据字典
            
        Returns:
            分析结果文本
        """
        if self.mock_mode:
            return self._mock_analysis(stock_code, stock_data)
            
        # 重试机制
        for attempt in range(self.max_retries):
            try:
                # 准备分析请求
                prompt = self._prepare_analysis_prompt(stock_code, stock_data)
                
                logger.info(f"DeepSeek API请求分析 (尝试 {attempt+1}/{self.max_retries})")
                
                # 发送API请求
                response = self.client.post(
                    "/chat/completions",
                    json={
                        "model": "deepseek-chat",
                        "messages": [
                            {"role": "system", "content": "你是一个专业的股票分析师，请基于提供的数据进行分析。"},
                            {"role": "user", "content": prompt}
                        ]
                    },
                    timeout=self.timeout  # 明确指定超时时间
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result["choices"][0]["message"]["content"]
                else:
                    logger.error(f"API请求失败: {response.status_code}")
                    # 如果是最后一次尝试，则返回错误信息
                    if attempt == self.max_retries - 1:
                        return f"分析失败: API返回错误 {response.status_code}"
                    # 否则等待后重试
                    import time
                    time.sleep(2)  # 等待2秒后重试
                    continue
                    
            except httpx.TimeoutException as e:
                logger.error(f"API请求超时 (尝试 {attempt+1}/{self.max_retries}): {str(e)}")
                # 如果是最后一次尝试，则返回错误信息
                if attempt == self.max_retries - 1:
                    return f"分析失败: API请求超时，请稍后重试"
                # 否则等待后重试
                import time
                time.sleep(2)  # 等待2秒后重试
                continue
            except Exception as e:
                logger.error(f"生成分析时出错 (尝试 {attempt+1}/{self.max_retries}): {str(e)}")
                # 如果是最后一次尝试，则返回错误信息
                if attempt == self.max_retries - 1:
                    return f"分析失败: {str(e)}"
                # 否则等待后重试
                import time
                time.sleep(2)  # 等待2秒后重试
                continue
        
        # 如果所有尝试都失败，则返回模拟分析结果
        logger.warning(f"所有API请求尝试都失败，切换到模拟模式")
        return self._mock_analysis(stock_code, stock_data)
    
    def generate_trading_signal(
        self, 
        stock_code: str, 
        analysis_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成交易信号
        
        Args:
            stock_code: 股票代码
            analysis_data: 分析数据
            
        Returns:
            交易信号字典
        """
        if self.mock_mode:
            return self._mock_trading_signal(stock_code)
            
        # 重试机制
        for attempt in range(self.max_retries):
            try:
                # 准备信号生成请求
                prompt = self._prepare_signal_prompt(stock_code, analysis_data)
                
                logger.info(f"DeepSeek API请求交易信号 (尝试 {attempt+1}/{self.max_retries})")
                
                # 发送API请求
                response = self.client.post(
                    "/chat/completions",
                    json={
                        "model": "deepseek-chat",
                        "messages": [
                            {"role": "system", "content": "你是一个专业的交易策略师，请基于分析数据生成交易信号。"},
                            {"role": "user", "content": prompt}
                        ]
                    },
                    timeout=self.timeout  # 明确指定超时时间
                )
                
                if response.status_code == 200:
                    result = response.json()
                    # 解析AI响应为交易信号
                    return self._parse_signal_response(result["choices"][0]["message"]["content"])
                else:
                    logger.error(f"API请求失败: {response.status_code}")
                    # 如果是最后一次尝试，则返回错误信号
                    if attempt == self.max_retries - 1:
                        return self._generate_error_signal(stock_code, f"API返回错误 {response.status_code}")
                    # 否则等待后重试
                    import time
                    time.sleep(2)  # 等待2秒后重试
                    continue
                    
            except httpx.TimeoutException as e:
                logger.error(f"API请求超时 (尝试 {attempt+1}/{self.max_retries}): {str(e)}")
                # 如果是最后一次尝试，则返回错误信号
                if attempt == self.max_retries - 1:
                    return self._generate_error_signal(stock_code, "API请求超时，请稍后重试")
                # 否则等待后重试
                import time
                time.sleep(2)  # 等待2秒后重试
                continue
            except Exception as e:
                logger.error(f"生成交易信号时出错 (尝试 {attempt+1}/{self.max_retries}): {str(e)}")
                # 如果是最后一次尝试，则返回错误信号
                if attempt == self.max_retries - 1:
                    return self._generate_error_signal(stock_code, str(e))
                # 否则等待后重试
                import time
                time.sleep(2)  # 等待2秒后重试
                continue
        
        # 如果所有尝试都失败，则返回模拟交易信号
        logger.warning(f"所有API请求尝试都失败，切换到模拟模式")
        return self._mock_trading_signal(stock_code)
    
    def _prepare_analysis_prompt(self, stock_code: str, stock_data: Dict[str, Any]) -> str:
        """准备分析提示词
        
        Args:
            stock_code: 股票代码
            stock_data: 股票数据
            
        Returns:
            格式化的提示词
        """
        prompt = f"请分析股票 {stock_data.get('stock_full_name', stock_code)} ({stock_code}) 的以下数据：\n\n"
        
        # 添加价格数据摘要
        if "price_data" in stock_data:
            prompt += "1. 价格数据：\n"
            prompt += stock_data["price_data"] + "\n\n"
        
        # 添加技术指标
        if "technical_indicators" in stock_data:
            prompt += "2. 技术指标：\n"
            prompt += json.dumps(stock_data["technical_indicators"], indent=2, ensure_ascii=False) + "\n\n"
        
        # 添加市场环境
        if "market_environment" in stock_data:
            prompt += "3. 市场环境：\n"
            prompt += json.dumps(stock_data["market_environment"], indent=2, ensure_ascii=False) + "\n\n"
        
        prompt += "请提供以下分析：\n"
        prompt += "1. 近期走势分析\n"
        prompt += "2. 技术指标解读\n"
        prompt += "3. 市场环境影响\n"
        prompt += "4. 投资建议\n"
        
        return prompt
    
    def _prepare_signal_prompt(self, stock_code: str, analysis_data: Dict[str, Any]) -> str:
        """准备信号生成提示词
        
        Args:
            stock_code: 股票代码
            analysis_data: 分析数据
            
        Returns:
            格式化的提示词
        """
        prompt = f"请基于以下分析数据，生成股票 {stock_code} 的交易信号：\n\n"
        prompt += json.dumps(analysis_data, indent=2, ensure_ascii=False) + "\n\n"
        prompt += "请生成包含以下信息的交易信号：\n"
        prompt += "1. 交易动作（买入/卖出/持有）\n"
        prompt += "2. 信心水平（0-1之间的数值）\n"
        prompt += "3. 建议原因\n"
        prompt += "请以JSON格式返回结果"
        
        return prompt
    
    def _parse_signal_response(self, response_text: str) -> Dict[str, Any]:
        """解析AI响应为交易信号
        
        Args:
            response_text: AI响应文本
            
        Returns:
            交易信号字典
        """
        try:
            # 尝试直接解析JSON
            signal = json.loads(response_text)
        except json.JSONDecodeError:
            # 如果不是JSON，尝试提取关键信息
            signal = {
                "action": "持有",
                "confidence": 0.5,
                "reason": "无法解析AI响应",
                "generated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # 简单的文本分析
            if "买入" in response_text:
                signal["action"] = "买入"
                signal["confidence"] = 0.7
            elif "卖出" in response_text:
                signal["action"] = "卖出"
                signal["confidence"] = 0.7
                
            signal["reason"] = response_text[:200] + "..."  # 截取前200个字符作为原因
            
        return signal
    
    def _generate_error_signal(self, stock_code: str, error_message: str) -> Dict[str, Any]:
        """生成错误信号
        
        Args:
            stock_code: 股票代码
            error_message: 错误信息
            
        Returns:
            错误信号字典
        """
        return {
            "stock_code": stock_code,
            "action": "持有",
            "confidence": 0,
            "reason": f"生成信号时出错: {error_message}",
            "generated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def _mock_analysis(self, stock_code: str, stock_data: Dict[str, Any]) -> str:
        """生成模拟分析结果
        
        Args:
            stock_code: 股票代码
            stock_data: 股票数据
            
        Returns:
            模拟分析文本
        """
        stock_name = stock_data.get('stock_full_name', stock_code)
        
        analysis = f"""
{stock_name} ({stock_code}) 股票分析报告：

1. 近期走势分析：
   - 股票近期呈现震荡上行趋势
   - 成交量保持稳定，未见明显异常

2. 技术指标解读：
   - RSI指标显示股票处于中性区域
   - MACD指标显示多头趋势正在形成
   - 布林带显示价格运行在中轨附近

3. 市场环境影响：
   - 大盘整体表现平稳
   - 行业景气度良好
   - 市场情绪稳定

4. 投资建议：
   - 建议持有观望
   - 可在价格回调时考虑增持
   - 设置止损位，控制风险

注：此为模拟分析结果，仅供参考。
"""
        return analysis
    
    def _mock_trading_signal(self, stock_code: str) -> Dict[str, Any]:
        """生成模拟交易信号
        
        Args:
            stock_code: 股票代码
            
        Returns:
            模拟交易信号字典
        """
        return {
            "stock_code": stock_code,
            "action": "持有",
            "confidence": 0.6,
            "reason": "模拟模式：基于技术指标综合判断，建议持有观望",
            "generated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        } 