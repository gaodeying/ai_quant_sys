import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any, Tuple
import json
from loguru import logger

# 获取项目根目录
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT_DIR)

from src.utils.logger import logger
from src.data.data_loader import DataLoader
from src.utils.deepseek_client import DeepSeekClient
from configs.config import STOCK_POOL, HSTECH_INDEX_CODE
from configs.stock_info import get_stock_name, get_stock_full_name

class StockAnalyzer:
    """股票分析器，使用AI模型分析股票数据并生成交易信号"""
    
    def __init__(self, data_loader=None):
        """初始化股票分析器
        
        Args:
            data_loader: 数据加载器，如果为None则创建新实例
        """
        from src.utils.deepseek_client import DeepSeekClient
        
        if data_loader is None:
            from src.data.data_loader import DataLoader
            self.data_loader = DataLoader()
        else:
            self.data_loader = data_loader
            
        try:
            # 初始化AI客户端，默认启用模拟模式以避免API连接问题
            self.ai_client = DeepSeekClient(mock_mode=True)
            logger.info("DeepSeek客户端初始化成功，使用模拟模式")
            
            # 尝试进行连接测试
            connection_test = self.ai_client.test_connection()
            if connection_test["status"] == "success":
                # 如果连接成功，禁用模拟模式
                self.ai_client.mock_mode = False
                logger.info("DeepSeek API连接测试成功，已切换到API模式")
            else:
                logger.warning(f"DeepSeek API连接测试失败: {connection_test['message']}，将使用模拟模式")
                
        except Exception as e:
            logger.error(f"初始化DeepSeek客户端失败: {str(e)}")
            self.ai_client = None
    
    def analyze_stock_pool(self, days: int = 90) -> Dict[str, Dict]:
        """分析股票池中的所有股票
        
        Args:
            days: 分析的历史数据天数
            
        Returns:
            分析结果字典，格式为 {stock_code: analysis_data}
        """
        logger.info(f"开始分析股票池，共{len(STOCK_POOL)}支股票")
        results = {}
        
        for stock_code in STOCK_POOL:
            try:
                # 获取股票完整名称
                stock_full_name = get_stock_full_name(stock_code)
                logger.info(f"分析股票: {stock_full_name}")
                
                # 获取股票数据
                stock_data = self._prepare_stock_data(stock_code, days)
                
                # 计算基本技术指标
                analysis = self._calculate_technical_indicators(stock_data)
                
                # 添加股票名称信息
                analysis['stock_name'] = get_stock_name(stock_code)
                analysis['stock_full_name'] = stock_full_name
                
                # 使用AI模型生成深度分析
                if self.ai_client:
                    try:
                        ai_analysis = self.ai_client.analyze_stock(stock_code, stock_data)
                        analysis['ai_analysis'] = ai_analysis
                    except Exception as e:
                        logger.error(f"AI分析股票{stock_full_name}失败: {str(e)}")
                        analysis['ai_analysis'] = "分析失败"
                
                results[stock_code] = analysis
                logger.info(f"股票{stock_full_name}分析完成")
            except Exception as e:
                logger.error(f"分析股票{stock_code}时出错: {str(e)}")
        
        logger.info(f"股票池分析完成，成功分析{len(results)}/{len(STOCK_POOL)}支股票")
        return results
    
    def rank_stocks(self, analysis_results: Dict[str, Dict]) -> List[Dict[str, Any]]:
        """根据分析结果对股票进行排名
        
        Args:
            analysis_results: 分析结果字典
            
        Returns:
            股票排名列表，包含股票代码、行动建议和评分
        """
        logger.info("开始对股票进行排名")
        ranked_stocks = []
        
        for stock_code, analysis in analysis_results.items():
            try:
                # 生成交易信号
                if self.ai_client:
                    try:
                        signal = self.ai_client.generate_trading_signal(stock_code, analysis)
                    except Exception as e:
                        logger.error(f"生成股票{stock_code}交易信号失败: {str(e)}")
                        signal = {
                            "stock_code": stock_code,
                            "action": "持有",
                            "confidence": 0.5,
                            "reason": "AI分析失败，默认建议持有",
                            "generated_at": ""
                        }
                else:
                    # 如果AI客户端不可用，使用简单规则
                    signal = self._generate_simple_signal(stock_code, analysis)
                
                # 计算排名分数 (示例: 买入=1, 持有=0, 卖出=-1) * 置信度
                action_score = {"买入": 1, "持有": 0, "卖出": -1}.get(signal["action"], 0)
                rank_score = action_score * signal["confidence"]
                
                # 添加到排名列表
                ranked_stocks.append({
                    "stock_code": stock_code,
                    "action": signal["action"],
                    "rank_score": rank_score,
                    "confidence": signal["confidence"],
                    "reason": signal["reason"]
                })
            except Exception as e:
                logger.error(f"对股票{stock_code}排名时出错: {str(e)}")
        
        # 按排名分数排序（降序）
        ranked_stocks.sort(key=lambda x: x["rank_score"], reverse=True)
        logger.info(f"股票排名完成，共{len(ranked_stocks)}支股票")
        
        return ranked_stocks
    
    def _prepare_stock_data(self, stock_code: str, days: int) -> Dict[str, Any]:
        """准备用于分析的股票数据
        
        Args:
            stock_code: 股票代码
            days: 历史数据天数
            
        Returns:
            处理后的股票数据字典
        """
        # 获取股票名称
        stock_name = get_stock_name(stock_code)
        stock_full_name = get_stock_full_name(stock_code)
        
        # 从数据加载器获取数据
        today = self.data_loader.get_latest_trading_day()
        start_date = self.data_loader.get_previous_trading_day(today, days)
        
        # 获取历史价格数据
        price_data = self.data_loader.get_stock_data(stock_code, start_date, today)
        
        # 计算基本技术指标
        if not price_data.empty:
            price_data_with_indicators = self.data_loader.calculate_technical_indicators(price_data)
        else:
            price_data_with_indicators = price_data
            
        # 获取基本面数据
        try:
            fundamental_data = self.data_loader.get_stock_fundamentals(stock_code)
        except:
            fundamental_data = "暂无基本面数据"
        
        return {
            "stock_code": stock_code,
            "stock_name": stock_name,
            "stock_full_name": stock_full_name,
            "price_data": price_data_with_indicators,
            "technical_indicators": {},  # 将在_calculate_technical_indicators中填充
            "fundamental_data": fundamental_data,
            "market_sentiment": "暂无市场情绪数据"  # 示例
        }
    
    def _calculate_technical_indicators(self, stock_data: Dict[str, Any]) -> Dict[str, Any]:
        """计算技术指标
        
        Args:
            stock_data: 股票数据
            
        Returns:
            包含技术指标的分析结果
        """
        # 这里应该实现技术指标的计算逻辑
        # 示例：简单的移动平均线、RSI、MACD等
        
        # 简化示例 - 实际实现应该计算真实指标
        analysis = {
            "rsi": "计算RSI",
            "macd": "计算MACD",
            "bollinger": "计算布林带",
            "moving_averages": "计算移动平均线",
            "recent_performance": "分析近期表现",
            "market_environment": "分析市场环境"
        }
        
        return analysis
    
    def _generate_simple_signal(self, stock_code: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """基于简单规则生成交易信号
        
        Args:
            stock_code: 股票代码
            analysis: 分析数据
            
        Returns:
            交易信号字典
        """
        # 简单规则示例 - 实际应用应实现更复杂的规则
        return {
            "stock_code": stock_code,
            "action": "持有",  # 默认建议持有
            "confidence": 0.5,
            "reason": "基于简单规则生成的默认信号",
            "generated_at": ""
        }

    def analyze_stock(self, stock_code: str, days: int = 90) -> Dict[str, Any]:
        """分析单个股票
        
        Args:
            stock_code: 股票代码
            days: 分析的历史天数
            
        Returns:
            分析结果字典
        """
        # 获取股票名称信息
        stock_name = get_stock_name(stock_code)
        stock_full_name = get_stock_full_name(stock_code)
        
        logger.info(f"开始分析股票: {stock_full_name}, 天数: {days}")
        
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        try:
            # 获取股票数据
            stock_data = self.data_loader.get_stock_data(stock_code, start_date, end_date)
            if stock_data.empty:
                logger.error(f"无法获取股票数据: {stock_full_name}")
                return {"error": f"无法获取股票数据: {stock_full_name}"}
            
            # 计算技术指标
            stock_with_indicators = self.data_loader.calculate_technical_indicators(stock_data)
            
            # 获取市场环境数据（指数）
            try:
                index_data = self.data_loader.get_index_data(HSTECH_INDEX_CODE, start_date, end_date)
                index_with_indicators = self.data_loader.calculate_technical_indicators(index_data)
                market_env = self._analyze_market_environment(index_with_indicators)
            except Exception as e:
                logger.error(f"获取市场环境数据失败: {str(e)}")
                market_env = {"error": str(e)}
            
            # 提取技术指标数据
            recent_indicators = self._extract_recent_indicators(stock_with_indicators)
            
            # 获取基本面数据
            fundamental_data = self.data_loader.get_stock_fundamentals(stock_code)
            
            # 汇总分析数据
            analysis_data = {
                "stock_code": stock_code,
                "stock_name": stock_name,
                "stock_full_name": stock_full_name,
                "analysis_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "period": f"{start_date} 至 {end_date}",
                "price_data": self._format_price_data(stock_with_indicators.tail(10)),
                "technical_indicators": recent_indicators,
                "fundamental_data": fundamental_data,
                "market_environment": market_env
            }
            
            # 使用DeepSeek模型生成分析（如果可用）
            if self.ai_client is not None:
                try:
                    analysis_text = self.ai_client.analyze_stock(stock_code, analysis_data)
                    analysis_data["ai_analysis"] = analysis_text
                    
                    # 生成交易信号
                    signal = self.ai_client.generate_trading_signal(stock_code, recent_indicators)
                    analysis_data["trading_signal"] = signal
                except Exception as e:
                    logger.error(f"生成AI分析失败: {str(e)}")
                    analysis_data["ai_analysis"] = f"AI分析生成失败: {str(e)}"
                    analysis_data["trading_signal"] = {"action": "未知", "confidence": 0, "reason": f"信号生成失败: {str(e)}"}
            else:
                # 使用简单的规则生成交易信号
                signal = self._generate_basic_signal(recent_indicators)
                analysis_data["trading_signal"] = signal
                analysis_data["ai_analysis"] = "AI分析模型不可用，使用基本技术指标分析"
            
            return analysis_data
            
        except Exception as e:
            logger.error(f"分析股票失败: {stock_full_name}, 错误: {str(e)}")
            return {"error": str(e)}
    
    def _analyze_market_environment(self, index_df: pd.DataFrame) -> Dict[str, Any]:
        """分析市场环境
        
        Args:
            index_df: 指数数据DataFrame
            
        Returns:
            市场环境分析结果
        """
        if index_df.empty:
            return {"status": "未知", "description": "无法获取指数数据"}
            
        try:
            # 提取最近数据
            recent_df = index_df.tail(60)  # 最近60个交易日
            
            # 计算近期趋势
            close_prices = recent_df["Close"].values
            if len(close_prices) >= 20:
                trend_20d = np.polyfit(range(20), close_prices[-20:], 1)[0]
                trend_direction = "上升" if trend_20d > 0 else "下降" if trend_20d < 0 else "横盘"
            else:
                trend_direction = "未知"
                
            # 计算波动性
            if len(recent_df) >= 20:
                volatility = recent_df["Close"].pct_change().std() * np.sqrt(252) * 100  # 年化波动率
            else:
                volatility = 0
                
            # 计算市场状态
            latest = recent_df.iloc[-1]
            rsi = latest.get("RSI", 50)
            
            if rsi > 70:
                market_status = "超买"
            elif rsi < 30:
                market_status = "超卖"
            else:
                if trend_direction == "上升":
                    market_status = "看涨"
                elif trend_direction == "下降":
                    market_status = "看跌"
                else:
                    market_status = "中性"
            
            # 构建描述
            description = f"市场处于{market_status}状态，近期趋势{trend_direction}，"
            description += f"波动率{volatility:.2f}%。"
            
            if "MACD" in latest and "Signal" in latest:
                macd = latest["MACD"]
                signal = latest["Signal"]
                if macd > signal:
                    description += "MACD指标显示看涨信号。"
                else:
                    description += "MACD指标显示看跌信号。"
            
            # 近期表现
            if len(recent_df) >= 5:
                change_5d = (latest["Close"] / recent_df.iloc[-6]["Close"] - 1) * 100
                description += f"过去5个交易日，指数变化了{change_5d:.2f}%。"
            
            return {
                "status": market_status,
                "trend": trend_direction,
                "volatility": float(volatility),
                "description": description,
                "rsi": float(rsi) if not np.isnan(rsi) else 50,
                "index_value": float(latest["Close"]),
                "index_code": HSTECH_INDEX_CODE
            }
            
        except Exception as e:
            logger.error(f"分析市场环境失败: {str(e)}")
            return {"status": "未知", "description": f"分析失败: {str(e)}"}
    
    def _format_price_data(self, df: pd.DataFrame) -> str:
        """格式化价格数据为字符串
        
        Args:
            df: 价格数据DataFrame
            
        Returns:
            格式化的字符串
        """
        if df.empty:
            return "无价格数据"
            
        result = []
        for idx, row in df.iterrows():
            date = idx.strftime('%Y-%m-%d') if hasattr(idx, 'strftime') else str(idx)
            line = f"{date}: 开盘={row.get('Open', 0):.2f}, "
            line += f"最高={row.get('High', 0):.2f}, "
            line += f"最低={row.get('Low', 0):.2f}, "
            line += f"收盘={row.get('Close', 0):.2f}, "
            line += f"成交量={int(row.get('Volume', 0))}"
            result.append(line)
            
        return "\n".join(result)

    def _generate_basic_signal(self, indicators: Dict[str, Any]) -> Dict[str, Any]:
        """生成基本的交易信号
        
        Args:
            indicators: 技术指标字典
            
        Returns:
            交易信号字典
        """
        # 获取股票代码和名称（如果有）
        stock_code = indicators.get("stock_code", "")
        stock_name = indicators.get("stock_name", "")
        stock_full_name = indicators.get("stock_full_name", stock_code)
        
        # 默认为持有
        signal = {
            "stock_code": stock_code,
            "stock_name": stock_name,
            "stock_full_name": stock_full_name,
            "action": "持有",
            "confidence": 0.5,
            "reason": "基于技术指标的综合判断",
            "generated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        buy_signals = 0
        sell_signals = 0
        
        # RSI信号
        rsi = indicators.get("RSI", 50)
        if rsi < 30:  # 超卖
            buy_signals += 1
        elif rsi > 70:  # 超买
            sell_signals += 1
        
        # MACD信号
        macd = indicators.get("MACD", 0)
        signal_line = indicators.get("Signal", 0)
        if macd > signal_line:  # 金叉
            buy_signals += 1
        elif macd < signal_line:  # 死叉
            sell_signals += 1
        
        # 布林带信号
        close = indicators.get("Close", 0)
        upper = indicators.get("Upper_Band", 0)
        lower = indicators.get("Lower_Band", 0)
        
        if close < lower:  # 价格低于下轨
            buy_signals += 1
        elif close > upper:  # 价格高于上轨
            sell_signals += 1
        
        # 均线信号
        ma5 = indicators.get("MA5", 0)
        ma20 = indicators.get("MA20", 0)
        
        if ma5 > ma20 and close > ma5:  # 多头排列
            buy_signals += 1
        elif ma5 < ma20 and close < ma5:  # 空头排列
            sell_signals += 1
        
        # 根据买卖信号确定操作
        if buy_signals >= 2 and buy_signals > sell_signals:
            signal["action"] = "买入"
            signal["confidence"] = min(0.8, 0.5 + 0.1 * buy_signals)
            signal["reason"] = f"多个技术指标显示买入信号，包括：" + \
                              (f"RSI={rsi:.2f}超卖；" if rsi < 30 else "") + \
                              (f"MACD金叉；" if macd > signal_line else "") + \
                              (f"价格突破布林带下轨；" if close < lower else "") + \
                              (f"均线多头排列；" if ma5 > ma20 and close > ma5 else "")
        elif sell_signals >= 2 and sell_signals > buy_signals:
            signal["action"] = "卖出"
            signal["confidence"] = min(0.8, 0.5 + 0.1 * sell_signals)
            signal["reason"] = f"多个技术指标显示卖出信号，包括：" + \
                              (f"RSI={rsi:.2f}超买；" if rsi > 70 else "") + \
                              (f"MACD死叉；" if macd < signal_line else "") + \
                              (f"价格突破布林带上轨；" if close > upper else "") + \
                              (f"均线空头排列；" if ma5 < ma20 and close < ma5 else "")
        else:
            signal["reason"] = "技术指标没有给出明确的交易信号，建议持有观望"
        
        return signal

    def _extract_recent_indicators(self, df: pd.DataFrame) -> Dict[str, Any]:
        """提取最近的技术指标
        
        Args:
            df: 带有技术指标的DataFrame
            
        Returns:
            包含最近技术指标的字典
        """
        if df.empty:
            return {}
        
        # 获取最近数据点
        latest = df.iloc[-1]
        
        # 整理指标数据
        indicators = {}
        
        # 基本价格信息
        indicators["Date"] = str(latest.name)
        indicators["Close"] = float(latest.get("Close", 0))
        
        # 如果有前一天的数据，计算变动百分比
        if len(df) > 1:
            prev_close = df.iloc[-2].get("Close", 0)
            if prev_close > 0:
                change_pct = (latest.get("Close", 0) / prev_close - 1) * 100
                indicators["Change"] = f"{change_pct:.2f}%"
            else:
                indicators["Change"] = "0.00%"
        else:
            indicators["Change"] = "N/A"
        
        # 技术指标
        for indicator in ["RSI", "MACD", "Signal", "K", "D", "J"]:
            if indicator in latest:
                value = latest[indicator]
                indicators[indicator] = float(value) if not pd.isna(value) else None
        
        # 移动平均线
        for ma in ["MA5", "MA10", "MA20", "MA60"]:
            if ma in latest:
                value = latest[ma]
                indicators[ma] = float(value) if not pd.isna(value) else None
        
        # 布林带
        for band in ["Upper_Band", "Lower_Band"]:
            if band in latest:
                value = latest[band]
                indicators[band] = float(value) if not pd.isna(value) else None
        
        # 趋势判断
        if all(col in df.columns for col in ["MA5", "MA20"]):
            if latest["MA5"] > latest["MA20"]:
                indicators["Trend"] = "上涨"
            elif latest["MA5"] < latest["MA20"]:
                indicators["Trend"] = "下跌"
            else:
                indicators["Trend"] = "横盘"
        else:
            # 使用简单方法判断趋势
            if len(df) >= 20:
                recent_prices = df["Close"].tail(20)
                slope = np.polyfit(range(len(recent_prices)), recent_prices, 1)[0]
                if slope > 0:
                    indicators["Trend"] = "上涨"
                elif slope < 0:
                    indicators["Trend"] = "下跌"
                else:
                    indicators["Trend"] = "横盘"
            else:
                indicators["Trend"] = "未知"
        
        return indicators 