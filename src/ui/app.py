import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any, Tuple
import gradio as gr
from pathlib import Path

# Set Matplotlib to use a font that supports Chinese characters
matplotlib.rcParams['font.sans-serif'] = ['SimHei']  # Use SimHei for Chinese support
matplotlib.rcParams['axes.unicode_minus'] = False  # Ensure minus signs are displayed correctly

# 获取项目根目录
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT_DIR)

try:
    from src.utils.logger import logger
    from src.data.data_loader import DataLoader
    from configs.config import STOCK_POOL, BACKTEST_START, BACKTEST_END
except ImportError as e:
    print(f"导入错误: {e}")
    print(f"当前Python路径: {sys.path}")
    raise

# 尝试导入模型模块
try:
    from src.models.stock_analyzer import StockAnalyzer
except ImportError:
    try:
        from src.models.stock_analyzer import StockAnalyzer
    except ImportError:
        print("无法导入StockAnalyzer模块，UI的分析功能将不可用")
        
        # 创建简单的替代类
        class StockAnalyzer:
            def __init__(self, *args, **kwargs):
                print("警告: 使用替代的StockAnalyzer模块")
            
            def analyze_stock(self, stock_code, days=90):
                return {"error": "分析模块不可用"}
                
            def analyze_stock_pool(self, *args, **kwargs):
                return {"error": "分析模块不可用"}

from src.strategies.trading_strategy import StrategyFactory
from src.backtest.backtester import Backtester

# 禁用matplotlib的交互模式
plt.ioff()

class GradioApp:
    """Gradio Web界面应用"""
    
    def __init__(self):
        """初始化Web应用"""
        self.data_loader = DataLoader()
        self.stock_analyzer = StockAnalyzer(self.data_loader)
        self.backtester = Backtester(self.data_loader)
        
        self.interface = self._build_interface()
        logger.info("Web界面应用初始化完成")
    
    def _build_interface(self) -> gr.Blocks:
        """构建Gradio界面
        
        Returns:
            Gradio Blocks界面
        """
        with gr.Blocks(title="AI量化交易系统", theme=gr.themes.Soft()) as interface:
            gr.Markdown("# 🚀 AI量化交易系统")
            gr.Markdown("基于DeepSeek大语言模型的港股量化分析与交易工具")
            
            with gr.Tabs():
                # 股票分析标签页
                with gr.Tab("股票分析"):
                    with gr.Row():
                        with gr.Column(scale=1):
                            stock_code = gr.Dropdown(
                                choices=[f"{code} ({name})" for code, name in STOCK_POOL.items()],
                                label="选择股票",
                                info="选择要分析的股票"
                            )
                            days = gr.Slider(
                                minimum=30, 
                                maximum=365, 
                                value=90, 
                                step=1, 
                                label="分析天数"
                            )
                            analyze_btn = gr.Button("开始分析", variant="primary")
                        
                        with gr.Column(scale=2):
                            analysis_output = gr.Textbox(
                                label="AI分析结果",
                                lines=10,
                                interactive=False
                            )
                    
                    with gr.Row():
                        with gr.Column():
                            indicators_output = gr.DataFrame(
                                label="技术指标",
                                interactive=False
                            )
                        
                        with gr.Column():
                            price_chart = gr.Plot(label="股价走势图")
                            
                    analyze_btn.click(
                        fn=self.analyze_stock,
                        inputs=[stock_code, days],
                        outputs=[analysis_output, indicators_output, price_chart]
                    )
                
                # 策略回测标签页
                with gr.Tab("策略回测"):
                    with gr.Row():
                        with gr.Column():
                            backtest_stock = gr.Dropdown(
                                choices=[f"{code} ({name})" for code, name in STOCK_POOL.items()],
                                label="选择股票",
                                info="选择要回测的股票"
                            )
                            strategy_name = gr.Dropdown(
                                choices=StrategyFactory.get_available_strategies(),
                                label="选择策略",
                                info="选择要使用的交易策略"
                            )
                            with gr.Row():
                                start_date = gr.Textbox(
                                    label="开始日期",
                                    value=BACKTEST_START,
                                    info="格式：YYYY-MM-DD"
                                )
                                end_date = gr.Textbox(
                                    label="结束日期",
                                    value=BACKTEST_END,
                                    info="格式：YYYY-MM-DD"
                                )
                            backtest_btn = gr.Button("开始回测", variant="primary")
                            
                    with gr.Row():
                        backtest_result = gr.JSON(label="回测结果")
                        
                    with gr.Row():
                        with gr.Column():
                            equity_chart = gr.Plot(label="净值曲线")
                        with gr.Column():
                            drawdown_chart = gr.Plot(label="回撤曲线")
                    
                    with gr.Row():
                        compare_btn = gr.Button("比较所有策略", variant="secondary")
                        compare_result = gr.Textbox(
                            label="策略比较结果",
                            lines=10,
                            interactive=False
                        )
                    
                    backtest_btn.click(
                        fn=self.run_backtest,
                        inputs=[backtest_stock, strategy_name, start_date, end_date],
                        outputs=[backtest_result, equity_chart, drawdown_chart]
                    )
                    
                    compare_btn.click(
                        fn=self.compare_strategies,
                        inputs=[backtest_stock, start_date, end_date],
                        outputs=[compare_result, equity_chart, drawdown_chart]
                    )
                
                # 投资组合标签页
                with gr.Tab("投资组合"):
                    with gr.Row():
                        portfolio_days = gr.Slider(
                            minimum=30, 
                            maximum=365, 
                            value=90, 
                            step=1, 
                            label="分析天数"
                        )
                        portfolio_btn = gr.Button("分析股票池", variant="primary")
                    
                    portfolio_result = gr.DataFrame(label="股票池分析结果")
                    
                    portfolio_btn.click(
                        fn=self.analyze_portfolio,
                        inputs=[portfolio_days],
                        outputs=[portfolio_result]
                    )
        
        return interface
    
    def analyze_stock(self, stock_code: str, days: int) -> Tuple[str, pd.DataFrame, plt.Figure]:
        """分析股票
        
        Args:
            stock_code: 股票代码
            days: 分析天数
            
        Returns:
            分析结果文本, 技术指标DataFrame, 股价图表
        """
        logger.info(f"UI请求: 分析股票 {stock_code}, 天数: {days}")
        
        try:
            # 获取分析结果
            analysis = self.stock_analyzer.analyze_stock(stock_code, days)
            
            if "error" in analysis:
                return f"分析错误: {analysis['error']}", pd.DataFrame(), plt.Figure()
            
            # 提取AI分析文本
            ai_analysis = analysis.get("ai_analysis", "AI分析不可用")
            
            # 提取交易信号
            signal = analysis.get("trading_signal", {})
            action = signal.get("action", "未知")
            reason = signal.get("reason", "")
            
            # 生成总结
            summary = f"交易信号: {action}\n\n"
            summary += f"信号理由: {reason}\n\n"
            summary += f"AI分析:\n{ai_analysis}"
            
            # 生成技术指标DataFrame
            indicators = analysis.get("technical_indicators", {})
            if isinstance(indicators, dict):
                # 转换为DataFrame，取有限数量的主要指标
                main_indicators = {k: v for k, v in indicators.items() if k in 
                                ["Date", "Close", "Change", "RSI", "MACD", "MA5", "MA20", "Trend"]}
                df = pd.DataFrame([main_indicators])
            else:
                df = pd.DataFrame()
            
            # 生成股价图表
            figure = self._plot_stock_data(stock_code, days)
            
            return summary, df, figure
        
        except Exception as e:
            logger.error(f"分析股票失败: {str(e)}")
            return f"分析过程中出错: {str(e)}", pd.DataFrame(), plt.Figure()
    
    def run_backtest(self, stock_code: str, strategy_name: str, 
                    start_date: str, end_date: str) -> Tuple[Dict[str, Any], plt.Figure, plt.Figure]:
        """运行回测
        
        Args:
            stock_code: 股票代码
            strategy_name: 策略名称
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            回测结果, 净值曲线图, 回撤曲线图
        """
        logger.info(f"UI请求: 回测 {stock_code}, 策略: {strategy_name}, 日期: {start_date} 至 {end_date}")
        
        try:
            # 创建策略实例
            strategy_params = {}
            if strategy_name == "bollinger":
                strategy_params = {"period": 20, "num_std": 2.0}
            elif strategy_name == "rsi":
                strategy_params = {"period": 14, "overbought": 70, "oversold": 30}
            elif strategy_name == "macd":
                strategy_params = {"fast": 12, "slow": 26, "signal": 9}
                
            strategy = StrategyFactory.create_strategy(strategy_name, **strategy_params)
            
            # 运行回测
            result = self.backtester.run_backtest(
                strategy, 
                stock_code, 
                start_date, 
                end_date
            )
            
            if "error" in result:
                logger.error(f"回测错误: {result['error']}")
                return {"error": result["error"]}, plt.Figure(), plt.Figure()
            
            # 处理回测结果
            result_copy = result.copy()
            
            # 绘制净值曲线
            equity_fig = self._plot_equity_curve(result)
            
            # 绘制回撤曲线
            drawdown_fig = self._plot_drawdown(result)
            
            # 处理不可JSON序列化的对象
            if "equity_curve" in result_copy and hasattr(result_copy["equity_curve"], "to_dict"):
                result_copy["equity_curve"] = "... equity_curve data ..."
            
            # 保留主要的回测指标
            summary = {
                "strategy": result_copy["strategy"],
                "stock_code": result_copy["stock_code"],
                "period": f"{result_copy['start_date']} to {result_copy['end_date']}",
                "total_return": f"{result_copy['total_return']:.2%}",
                "annualized_return": f"{result_copy['annualized_return']:.2%}",
                "max_drawdown": f"{result_copy['max_drawdown']:.2%}",
                "sharpe_ratio": f"{result_copy['sharpe_ratio']:.2f}",
                "num_trades": int(result_copy["num_trades"]),
                "win_rate": f"{result_copy['win_rate']:.2%}"
            }
            
            return summary, equity_fig, drawdown_fig
        
        except Exception as e:
            logger.error(f"回测过程中出错: {str(e)}")
            return {"error": str(e)}, plt.Figure(), plt.Figure()
    
    def compare_strategies(self, stock_code: str, start_date: str, end_date: str) -> Tuple[str, plt.Figure, plt.Figure]:
        """比较不同策略
        
        Args:
            stock_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            比较结果文本, 净值曲线图, 回撤曲线图
        """
        logger.info(f"UI请求: 比较策略, 股票: {stock_code}, 日期: {start_date} 至 {end_date}")
        
        try:
            # 创建不同策略实例
            strategies = [
                StrategyFactory.create_strategy("bollinger"),
                StrategyFactory.create_strategy("rsi"),
                StrategyFactory.create_strategy("macd"),
                StrategyFactory.create_strategy("combined")
            ]
            
            # 运行比较
            results = []
            for strategy in strategies:
                try:
                    result = self.backtester.run_backtest(
                        strategy, 
                        stock_code, 
                        start_date, 
                        end_date
                    )
                    results.append(result)
                except Exception as e:
                    logger.error(f"策略 {strategy.name} 回测失败: {str(e)}")
            
            if not results:
                return "所有策略回测失败", plt.Figure(), plt.Figure()
            
            # 生成比较结果文本
            comparison = f"策略比较结果 - {stock_code} ({start_date} 至 {end_date}):\n\n"
            comparison += f"{'策略名称':<15}{'总回报':<12}{'年化回报':<12}{'最大回撤':<12}{'夏普比率':<12}{'交易次数':<8}{'胜率':<8}\n"
            comparison += "-" * 70 + "\n"
            
            for result in results:
                if "error" in result:
                    continue
                    
                comparison += f"{result['strategy']:<15}"
                comparison += f"{result['total_return']:.2%:<12}"
                comparison += f"{result['annualized_return']:.2%:<12}"
                comparison += f"{result['max_drawdown']:.2%:<12}"
                comparison += f"{result['sharpe_ratio']:.2f:<12}"
                comparison += f"{int(result['num_trades']):<8}"
                comparison += f"{result['win_rate']:.2%:<8}\n"
            
            # 找出最佳策略
            best_strategy = max(results, key=lambda x: x.get('total_return', -999) if "error" not in x else -999)
            comparison += f"\n最佳策略: {best_strategy['strategy']}, 总回报: {best_strategy['total_return']:.2%}"
            
            # 绘制净值曲线比较图
            equity_fig = plt.figure(figsize=(10, 6))
            plt.title(f"净值曲线比较 - {stock_code}")
            plt.xlabel("日期")
            plt.ylabel("策略净值")
            
            for result in results:
                if "error" in result or not hasattr(result['equity_curve'], "plot"):
                    continue
                result['equity_curve'].plot(label=result['strategy'])
            
            plt.legend()
            plt.grid(True)
            
            # 绘制回撤曲线比较图
            drawdown_fig = plt.figure(figsize=(10, 6))
            plt.title(f"回撤曲线比较 - {stock_code}")
            plt.xlabel("日期")
            plt.ylabel("回撤比例")
            
            for result in results:
                if "error" in result or not hasattr(result['equity_curve'], "cummax"):
                    continue
                    
                equity = result['equity_curve']
                drawdown = (equity.cummax() - equity) / equity.cummax()
                drawdown.plot(label=result['strategy'])
            
            plt.legend()
            plt.grid(True)
            
            return comparison, equity_fig, drawdown_fig
            
        except Exception as e:
            logger.error(f"比较策略过程中出错: {str(e)}")
            return f"比较过程中出错: {str(e)}", plt.Figure(), plt.Figure()
    
    def analyze_portfolio(self, days: int) -> pd.DataFrame:
        """分析股票池
        
        Args:
            days: 分析天数
            
        Returns:
            股票池分析结果DataFrame
        """
        logger.info(f"UI请求: 分析股票池, 天数: {days}")
        
        try:
            # Analyze the first 5 stocks from the dictionary
            sample_stocks = list(STOCK_POOL.keys())[:5]
            analyses = {}
            
            for code in sample_stocks:
                try:
                    result = self.stock_analyzer.analyze_stock(code, days)
                    analyses[code] = result
                except Exception as e:
                    logger.error(f"分析股票失败: {code}, 错误: {str(e)}")
            
            # 排名股票
            rankings = self.stock_analyzer.rank_stocks(analyses)
            
            # 转换为DataFrame
            if not rankings:
                return pd.DataFrame({"message": ["无有效分析结果"]})
                
            df = pd.DataFrame(rankings)
            
            # 选择要显示的列
            display_cols = ["rank", "stock_code", "action", "rank_score", "confidence", "reason"]
            df = df[display_cols] if all(col in df.columns for col in display_cols) else df
            
            return df
            
        except Exception as e:
            logger.error(f"分析股票池过程中出错: {str(e)}")
            return pd.DataFrame({"error": [str(e)]})
    
    def _plot_stock_data(self, stock_code: str, days: int) -> plt.Figure:
        """绘制股票数据图表"""
        try:
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

            # 获取股票数据
            stock_data = self.data_loader.get_stock_data(stock_code, start_date, end_date)
            if stock_data.empty:
                # 创建空图表
                fig = plt.figure(figsize=(10, 6))
                plt.title(f"无法获取股票数据: {stock_code}", fontproperties='SimHei')
                return fig

            # 计算技术指标
            data_with_indicators = self.data_loader.calculate_technical_indicators(stock_data)

            # 创建图表
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), gridspec_kw={'height_ratios': [3, 1]})

            # 绘制K线图和均线
            ax1.set_title(f"{stock_code} 股价走势图", fontproperties='SimHei')

            # 绘制收盘价
            ax1.plot(data_with_indicators.index, data_with_indicators['Close'], label='收盘价')

            # 绘制移动平均线
            if 'MA5' in data_with_indicators.columns:
                ax1.plot(data_with_indicators.index, data_with_indicators['MA5'], label='MA5')
            if 'MA20' in data_with_indicators.columns:
                ax1.plot(data_with_indicators.index, data_with_indicators['MA20'], label='MA20')
            if 'MA60' in data_with_indicators.columns:
                ax1.plot(data_with_indicators.index, data_with_indicators['MA60'], label='MA60')

            # 绘制布林带
            if all(col in data_with_indicators.columns for col in ['Upper_Band', 'Lower_Band']):
                ax1.plot(data_with_indicators.index, data_with_indicators['Upper_Band'], 'r--', label='布林上轨')
                ax1.plot(data_with_indicators.index, data_with_indicators['Lower_Band'], 'g--', label='布林下轨')

            ax1.set_ylabel('价格', fontproperties='SimHei')
            ax1.legend(loc='best', prop={'family': 'SimHei'})
            ax1.grid(True)

            # 绘制交易量
            ax2.bar(data_with_indicators.index, data_with_indicators['Volume'])
            ax2.set_ylabel('成交量', fontproperties='SimHei')
            ax2.grid(True)

            plt.tight_layout()
            return fig

        except Exception as e:
            logger.error(f"绘制股票图表失败: {str(e)}")
            # 创建错误信息图表
            fig = plt.figure(figsize=(10, 6))
            plt.title(f"绘制图表出错: {str(e)}", fontproperties='SimHei')
            return fig
    
    def _plot_equity_curve(self, backtest_result: Dict[str, Any]) -> plt.Figure:
        """绘制净值曲线
        
        Args:
            backtest_result: 回测结果字典
            
        Returns:
            matplotlib图表
        """
        fig = plt.figure(figsize=(10, 6))
        
        if "equity_curve" in backtest_result and hasattr(backtest_result["equity_curve"], "plot"):
            equity_curve = backtest_result["equity_curve"]
            equity_curve.plot()
            plt.title(f"策略净值曲线 - {backtest_result.get('strategy', '')} ({backtest_result.get('stock_code', '')})")
            plt.xlabel("日期")
            plt.ylabel("净值")
            plt.grid(True)
        else:
            plt.title("净值曲线不可用")
        
        return fig
    
    def _plot_drawdown(self, backtest_result: Dict[str, Any]) -> plt.Figure:
        """绘制回撤曲线
        
        Args:
            backtest_result: 回测结果字典
            
        Returns:
            matplotlib图表
        """
        fig = plt.figure(figsize=(10, 6))
        
        if "equity_curve" in backtest_result and hasattr(backtest_result["equity_curve"], "cummax"):
            equity = backtest_result["equity_curve"]
            drawdown = (equity.cummax() - equity) / equity.cummax()
            drawdown.plot()
            plt.title(f"策略回撤曲线 - {backtest_result.get('strategy', '')} ({backtest_result.get('stock_code', '')})")
            plt.xlabel("日期")
            plt.ylabel("回撤比例")
            plt.grid(True)
        else:
            plt.title("回撤曲线不可用")
        
        return fig
    
    def launch(self, share: bool = False):
        """启动Web界面
        
        Args:
            share: 是否共享(公开访问)
        """
        logger.info(f"启动Web界面，共享模式: {share}")
        return self.interface.launch(share=share)


def start_ui(share: bool = False):
    """启动UI界面
    
    Args:
        share: 是否共享(公开访问)
    """
    try:
        app = GradioApp()
        app.launch(share=share)
    except Exception as e:
        logger.error(f"启动UI界面失败: {str(e)}")
        print(f"启动UI界面失败: {str(e)}")


if __name__ == "__main__":
    start_ui()