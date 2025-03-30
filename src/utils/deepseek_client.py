import os
import json
import requests
from typing import List, Dict, Any, Optional
from loguru import logger
from datetime import datetime

from configs.config import OPENAI_API_KEY, DEEPSEEK_API_BASE
from configs.stock_info import get_stock_name, get_stock_full_name

class DeepSeekClient:
    """DeepSeek API客户端，通过HTTP直接访问API接口"""
    
    def __init__(self, api_key: Optional[str] = None, api_base: Optional[str] = None, mock_mode: bool = False):
        """初始化DeepSeek客户端
        
        Args:
            api_key: DeepSeek API密钥，默认从环境变量获取
            api_base: DeepSeek API基础URL，默认从环境变量获取
            mock_mode: 是否启用模拟模式，默认False
        """
        self.api_key = api_key or OPENAI_API_KEY
        self.api_base = api_base or DEEPSEEK_API_BASE
        self.mock_mode = mock_mode
        self.connection_tested = False
        self.connection_valid = False
        
        if not self.api_key:
            logger.warning("DeepSeek API密钥未设置，自动启用模拟模式")
            self.mock_mode = True
            
        if self.mock_mode:
            logger.warning("DeepSeek客户端运行在模拟模式，将返回模拟响应")
            
        logger.info(f"DeepSeek客户端初始化完成，API基础URL: {self.api_base}")
        
        # 如果不是模拟模式，自动测试连接
        if not self.mock_mode:
            self._test_connection_silently()
    
    def _test_connection_silently(self):
        """静默测试API连接，失败时自动切换到模拟模式"""
        try:
            # 构建轻量级的模型列表请求
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            # 使用models端点测试连接
            url = f"{self.api_base}/models"
            response = requests.get(url, headers=headers, timeout=5)  # 短超时
            
            # 标记连接状态
            self.connection_tested = True
            if response.status_code == 200:
                self.connection_valid = True
                logger.info("API连接测试成功")
            else:
                self.connection_valid = False
                self.mock_mode = True
                logger.warning(f"API连接测试失败，自动切换到模拟模式。状态码: {response.status_code}")
                
        except Exception as e:
            self.connection_tested = True
            self.connection_valid = False
            self.mock_mode = True
            logger.warning(f"API连接测试异常，自动切换到模拟模式: {str(e)}")
    
    def test_connection(self) -> Dict[str, Any]:
        """测试API连接是否正常
        
        Returns:
            测试结果，包含状态和详细信息
        """
        if not self.api_key:
            return {
                "status": "error",
                "message": "API密钥未设置，请在.env文件中设置OPENAI_API_KEY"
            }
            
        try:
            # 构建轻量级的模型列表请求，用于测试连接
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            # 使用models端点测试连接
            url = f"{self.api_base}/models"
            response = requests.get(url, headers=headers, timeout=30)
            
            # 检查响应状态
            if response.status_code == 200:
                # 成功连接
                self.connection_valid = True
                self.connection_tested = True
                self.mock_mode = False
                return {
                    "status": "success",
                    "message": "API连接正常",
                    "details": response.json()
                }
            else:
                # 连接失败
                self.connection_valid = False
                self.connection_tested = True
                self.mock_mode = True
                error_msg = f"API连接失败，状态码: {response.status_code}"
                try:
                    error_details = response.json()
                    if "error" in error_details:
                        error_msg += f", 错误信息: {error_details['error']}"
                except:
                    error_msg += f", 响应内容: {response.text[:100]}"
                
                return {
                    "status": "error",
                    "message": error_msg
                }
                
        except requests.exceptions.RequestException as e:
            self.connection_valid = False
            self.connection_tested = True
            self.mock_mode = True
            return {
                "status": "error",
                "message": f"API连接请求异常: {str(e)}"
            }
        except Exception as e:
            self.connection_valid = False
            self.connection_tested = True
            self.mock_mode = True
            return {
                "status": "error",
                "message": f"测试连接时发生错误: {str(e)}"
            }
    
    def chat_completion(
        self, 
        messages: List[Dict[str, str]],
        model: str = "deepseek-chat",
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> Dict[str, Any]:
        """使用DeepSeek聊天模型生成回复
        
        Args:
            messages: 消息列表，格式为[{"role": "user", "content": "内容"}]
            model: 模型名称，默认为"deepseek-chat"
            temperature: 生成多样性，默认0.7
            max_tokens: 最大生成token数，默认4096
            
        Returns:
            OpenAI格式的响应对象
        """
        # 如果处于模拟模式，直接返回模拟响应
        if self.mock_mode:
            last_message = messages[-1]["content"] if messages else "无消息"
            logger.info(f"使用模拟模式生成回复，最后消息: {last_message[:30]}...")
            return self._create_mock_response(self._generate_mock_response(messages))
            
        if not self.api_key:
            # 如果API密钥未设置，返回模拟响应
            return self._create_mock_response("DeepSeek API密钥未设置，无法调用API")
            
        try:
            # 构建API请求
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            data = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            # 发送HTTP请求
            url = f"{self.api_base}/chat/completions"
            response = requests.post(url, headers=headers, json=data, timeout=60)
            
            # 检查响应状态
            response.raise_for_status()
            
            # 解析响应数据
            result = response.json()
            
            # 创建模拟的响应对象
            return self._parse_api_response(result)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"DeepSeek API请求失败: {str(e)}")
            # 自动切换到模拟模式
            self.mock_mode = True
            return self._create_mock_response(self._generate_mock_response(messages, f"API请求失败: {str(e)}"))
        except json.JSONDecodeError as e:
            logger.error(f"DeepSeek API响应解析失败: {str(e)}")
            # 自动切换到模拟模式
            self.mock_mode = True
            return self._create_mock_response(self._generate_mock_response(messages, f"API响应解析失败: {str(e)}"))
        except Exception as e:
            logger.error(f"DeepSeek API调用失败: {str(e)}")
            # 自动切换到模拟模式
            self.mock_mode = True
            return self._create_mock_response(self._generate_mock_response(messages, f"API调用失败: {str(e)}"))
    
    def _generate_mock_response(self, messages: List[Dict[str, str]], error_msg: Optional[str] = None) -> str:
        """生成模拟响应内容
        
        Args:
            messages: 消息列表
            error_msg: 错误信息，如果有的话
            
        Returns:
            模拟响应内容
        """
        if error_msg:
            return f"【模拟响应】（原因：{error_msg}）\n\n这是一个模拟的AI响应，因为API调用失败。"
            
        # 提取最后一条用户消息
        last_message = "无消息"
        for msg in reversed(messages):
            if msg["role"] == "user":
                last_message = msg["content"]
                break
                
        # 根据不同类型的消息返回不同模拟响应
        if "股票" in last_message or "分析" in last_message:
            return """
【模拟响应】
根据技术分析，该股票目前处于震荡整理阶段：

1. RSI指标(45.74)显示股票既不处于超买也不处于超卖区域
2. MACD指标与信号线交叉向下，可能预示短期动能减弱
3. 均线系统中，MA5低于MA20，表明短期呈现弱势
4. 价格处于布林带中轨附近，波动性正常

建议持有现有仓位，等待更明确的突破信号。如下跌至支撑位附近可考虑分批低吸。
            """
        elif "交易" in last_message or "信号" in last_message:
            return """
【模拟响应】
交易信号：持有
建议仓位：50%
操作理由：技术指标中性，尚无明确方向
止损位：前期低点下方5%
目标价位：前期高点
            """
        elif "量化" in last_message:
            return """
【模拟响应】
量化交易是指使用数学模型和算法来执行交易决策，而非依靠人为判断。

简单例子：均线交叉策略
1. 当5日均线上穿20日均线时买入
2. 当5日均线下穿20日均线时卖出
3. 程序自动监控市场并执行交易

这种方法优势在于消除情绪因素，严格执行纪律，可以同时监控多个市场。
            """
        else:
            return """
【模拟响应】
这是一个自动生成的模拟响应，因为系统当前无法连接到DeepSeek API。请检查您的API设置或网络连接，或继续使用模拟模式进行测试。
            """
    
    def _parse_api_response(self, response_data: Dict[str, Any]) -> Any:
        """解析API响应
        
        Args:
            response_data: API返回的原始JSON数据
            
        Returns:
            解析后的模拟响应对象
        """
        # 获取文本内容
        try:
            content = response_data["choices"][0]["message"]["content"]
            
            # 创建模拟响应对象
            return self._create_mock_response(content, response_data.get("created", None))
        except (KeyError, IndexError):
            logger.error(f"API响应格式不符合预期: {response_data}")
            return self._create_mock_response("API响应格式不符合预期")
    
    def _create_mock_response(self, content: str, created: Optional[int] = None):
        """创建模拟响应对象
        
        Args:
            content: 响应内容
            created: 创建时间戳
            
        Returns:
            模拟的响应对象
        """
        class MockMessage:
            def __init__(self, content):
                self.content = content
                self.role = "assistant"
                
        class MockChoice:
            def __init__(self, message):
                self.message = message
                self.index = 0
                
        class MockResponse:
            def __init__(self, choices, created=None):
                self.choices = choices
                self.created = created or int(datetime.now().timestamp())
                self.model = "mock-model"
                self.id = f"mock-id-{self.created}"
        
        mock_message = MockMessage(content)
        mock_choice = MockChoice(mock_message)
        return MockResponse([mock_choice], created)
    
    def analyze_stock(self, stock_code: str, stock_data: Dict[str, Any]) -> str:
        """分析股票数据并生成分析报告
        
        Args:
            stock_code: 股票代码
            stock_data: 股票历史数据和指标
            
        Returns:
            分析报告文本
        """
        # 获取股票完整名称
        stock_full_name = get_stock_full_name(stock_code)
        
        prompt = self._construct_stock_analysis_prompt(stock_code, stock_full_name, stock_data)
        
        messages = [
            {"role": "system", "content": "你是一位专业的股票分析师，擅长技术分析和基本面分析。请对提供的股票数据进行深入分析，并给出合理的投资建议。"},
            {"role": "user", "content": prompt}
        ]
        
        response = self.chat_completion(messages, temperature=0.3)
        return response.choices[0].message.content
    
    def generate_trading_signal(self, stock_code: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """基于股票分析生成交易信号
        
        Args:
            stock_code: 股票代码
            analysis: 股票分析数据
            
        Returns:
            交易信号字典，包含操作建议、理由等
        """
        # 获取股票完整名称
        stock_full_name = get_stock_full_name(stock_code)
        
        prompt = self._construct_trading_signal_prompt(stock_code, stock_full_name, analysis)
        
        messages = [
            {"role": "system", "content": "你是一位专业的量化交易策略师，你需要基于技术指标和市场分析给出明确的交易信号，包括买入、卖出或持有的建议，以及对应的置信度和理由。"},
            {"role": "user", "content": prompt}
        ]
        
        response = self.chat_completion(messages, temperature=0.2)
        
        # 解析响应内容为结构化的交易信号
        signal_text = response.choices[0].message.content
        
        # 简单解析示例，实际应用中可以要求模型返回JSON格式或使用更复杂的解析逻辑
        if "买入" in signal_text or "增持" in signal_text:
            action = "买入"
        elif "卖出" in signal_text or "减持" in signal_text:
            action = "卖出"
        else:
            action = "持有"
            
        # 获取股票名称
        stock_name = get_stock_name(stock_code)
            
        return {
            "stock_code": stock_code,
            "stock_name": stock_name,
            "stock_full_name": stock_full_name,
            "action": action,
            "confidence": 0.7,  # 简化处理，实际应从响应中提取
            "reason": signal_text,
            "generated_at": str(response.created)
        }
    
    def _construct_stock_analysis_prompt(self, stock_code: str, stock_full_name: str, stock_data: Dict[str, Any]) -> str:
        """构建股票分析提示
        
        Args:
            stock_code: 股票代码
            stock_full_name: 股票完整名称
            stock_data: 股票数据
            
        Returns:
            格式化的提示文本
        """
        return f"""
请分析以下港股 {stock_full_name} 的数据:

历史价格数据:
{stock_data.get('price_data', '无数据')}

技术指标:
{stock_data.get('technical_indicators', '无数据')}

最新财务数据:
{stock_data.get('fundamental_data', '无数据')}

市场环境:
{stock_data.get('market_environment', '无数据')}

请提供以下分析:
1. 近期价格趋势分析
2. 主要技术指标解读
3. 支撑位和阻力位
4. 财务指标评估
5. 风险因素
6. 总体评级和投资建议

你的分析应该基于数据和市场状况，并给出明确的投资观点。
"""
    
    def _construct_trading_signal_prompt(self, stock_code: str, stock_full_name: str, analysis: Dict[str, Any]) -> str:
        """构建交易信号生成提示
        
        Args:
            stock_code: 股票代码
            stock_full_name: 股票完整名称
            analysis: 分析数据
            
        Returns:
            格式化的提示文本
        """
        # 构建RSI描述
        rsi = analysis.get('RSI')
        rsi_desc = f"{rsi:.2f}" if rsi is not None else "N/A"
        
        # 构建MACD描述
        macd = analysis.get('MACD')
        signal = analysis.get('Signal')
        if macd is not None and signal is not None:
            macd_desc = f"MACD值: {macd:.2f}, 信号线: {signal:.2f}"
        else:
            macd_desc = "N/A"
        
        # 构建均线状态描述
        ma5 = analysis.get('MA5')
        ma20 = analysis.get('MA20')
        if ma5 is not None and ma20 is not None:
            ma_desc = f"MA5: {ma5:.2f}, MA20: {ma20:.2f}"
            if ma5 > ma20:
                ma_desc += " (呈上升趋势)"
            elif ma5 < ma20:
                ma_desc += " (呈下降趋势)"
            else:
                ma_desc += " (趋势不明)"
        else:
            ma_desc = "N/A"
        
        # 构建布林带描述
        upper = analysis.get('Upper_Band')
        lower = analysis.get('Lower_Band')
        close = analysis.get('Close')
        if upper is not None and lower is not None and close is not None:
            bb_position = (close - lower) / (upper - lower) if upper > lower else 0.5
            bb_desc = f"价格位于布林带 {bb_position:.2%} 处"
        else:
            bb_desc = "N/A"
        
        return f"""
基于以下对 {stock_full_name} 的分析数据:

技术指标:
- RSI: {rsi_desc} (超过70视为超买，低于30视为超卖)
- MACD: {macd_desc}
- 布林带位置: {bb_desc}
- 均线状态: {ma_desc}

近期价格:
当前价格: {analysis.get('Close', 'N/A')}
价格变化: {analysis.get('Change', 'N/A')}
趋势判断: {analysis.get('Trend', 'N/A')}

请生成明确的交易信号，包括:
1. 操作建议(买入/卖出/持有)
2. 建议仓位比例(0-100%)
3. 操作理由
4. 止损位建议
5. 目标价位

请确保你的建议考虑了技术面和市场环境，并明确说明交易逻辑。
""" 