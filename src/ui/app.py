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

# 设置Matplotlib字体配置，支持中文显示
matplotlib.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans', 'Bitstream Vera Sans']
matplotlib.rcParams['font.family'] = 'sans-serif'
matplotlib.rcParams['axes.unicode_minus'] = False  # 确保负号正确显示
matplotlib.rcParams['figure.autolayout'] = True  # 自动调整布局，避免标签被截断

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
        try:
            logger.info(f"UI请求: 分析股票 {stock_code}, 天数: {days}")
            
            # 从选择的文本中提取纯股票代码（从"9618.HK (京东集团-SW)"提取"9618.HK"）
            pure_stock_code = stock_code.split(" ")[0] if " " in stock_code else stock_code
            logger.info(f"提取纯股票代码: {pure_stock_code}")
            
            # 获取分析结果
            analysis = self.stock_analyzer.analyze_stock(pure_stock_code, days)
            
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
            figure = self._plot_stock_data(pure_stock_code, days)
            
            return summary, df, figure
        
        except Exception as e:
            logger.error(f"分析股票失败: {str(e)}")
            return f"分析过程中出错: {str(e)}", pd.DataFrame(), plt.Figure()
    
    def run_backtest(self, stock_code: str, strategy_name: str, 
                    start_date: str, end_date: str) -> Tuple[Dict[str, Any], plt.Figure, plt.Figure]:
        """运行策略回测
        
        Args:
            stock_code: 股票代码
            strategy_name: 策略名称
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            回测结果字典、净值曲线图和回撤曲线图
        """
        try:
            logger.info(f"UI请求: 回测 {stock_code}, 策略: {strategy_name}, 日期范围: {start_date} 至 {end_date}")
            
            # 从选择的文本中提取纯股票代码
            pure_stock_code = stock_code.split(" ")[0] if " " in stock_code else stock_code
            logger.info(f"提取纯股票代码: {pure_stock_code}")
            
            # 创建策略实例
            strategy_params = self._get_strategy_params(strategy_name)
            strategy = StrategyFactory.create_strategy(strategy_name, **strategy_params)
            
            # 运行回测
            result = self.backtester.run_backtest(
                strategy, 
                pure_stock_code, 
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
        """比较多个策略在一只股票上的表现
        
        Args:
            stock_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            比较结果文本、净值曲线图和回撤曲线图
        """
        try:
            logger.info(f"UI请求: 策略比较, 股票: {stock_code}, 日期范围: {start_date} 至 {end_date}")
            
            # 从选择的文本中提取纯股票代码
            pure_stock_code = stock_code.split(" ")[0] if " " in stock_code else stock_code
            logger.info(f"提取纯股票代码: {pure_stock_code}")
            
            # 创建所有策略实例
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
                        pure_stock_code, 
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
        """绘制股票数据图表
        
        Args:
            stock_code: 股票代码
            days: 天数
            
        Returns:
            股价图表
        """
        plt.figure(figsize=(12, 8))
        
        try:
            # 获取股票数据
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            stock_data = self.data_loader.get_stock_data(stock_code, start_date, end_date)
            
            if stock_data.empty:
                plt.title(f"无法获取股票数据: {stock_code}", fontsize=14, pad=20)
                return plt.gcf()
            
            # 绘制股价
            ax1 = plt.subplot(2, 1, 1)
            ax1.plot(stock_data.index, stock_data['close'], label='收盘价', linewidth=2)
            ax1.set_title(f"{stock_code} 股价走势 ({start_date} 至 {end_date})", fontsize=16, pad=20)
            ax1.set_ylabel('价格', fontsize=12)
            ax1.grid(True)
            ax1.legend(loc='best', fontsize=10)
            
            # 绘制成交量
            ax2 = plt.subplot(2, 1, 2, sharex=ax1)
            ax2.bar(stock_data.index, stock_data['volume'], label='成交量', alpha=0.7)
            ax2.set_ylabel('成交量', fontsize=12)
            ax2.set_xlabel('日期', fontsize=12)
            ax2.grid(True)
            ax2.legend(loc='best', fontsize=10)
            
            plt.tight_layout()
            return plt.gcf()
        except Exception as e:
            logger.error(f"绘制股票图表时出错: {str(e)}")
            plt.title(f"生成图表时出错: {str(e)}", fontsize=14, pad=20)
            return plt.gcf()
    
    def _plot_equity_curve(self, backtest_result: Dict[str, Any]) -> plt.Figure:
        """绘制净值曲线
        
        Args:
            backtest_result: 回测结果
            
        Returns:
            净值曲线图
        """
        plt.figure(figsize=(12, 8))
        
        if 'equity_curve' in backtest_result and not isinstance(backtest_result['equity_curve'], str) and not backtest_result['equity_curve'].empty:
            equity = backtest_result['equity_curve']
            plt.plot(equity, linewidth=2)
            
            strategy_name = backtest_result.get('strategy_name', '未知策略')
            stock_code = backtest_result.get('stock_code', '未知股票')
            total_return = backtest_result.get('total_return', 0) * 100
            
            plt.title(f"{strategy_name} - {stock_code} 净值曲线 (总收益: {total_return:.2f}%)", fontsize=16, pad=20)
            plt.xlabel('日期', fontsize=12)
            plt.ylabel('净值', fontsize=12)
            plt.grid(True)
            
            # 添加初始投资水平线
            plt.axhline(y=1.0, color='r', linestyle='--', alpha=0.3)
            
            return plt.gcf()
        else:
            plt.title('无净值曲线数据', fontsize=14, pad=20)
            return plt.gcf()
    
    def _plot_drawdown(self, backtest_result: Dict[str, Any]) -> plt.Figure:
        """绘制回撤曲线
        
        Args:
            backtest_result: 回测结果
            
        Returns:
            回撤曲线图
        """
        plt.figure(figsize=(12, 8))
        
        if 'equity_curve' in backtest_result and not isinstance(backtest_result['equity_curve'], str) and not backtest_result['equity_curve'].empty:
            equity = backtest_result['equity_curve']
            drawdown = (equity.cummax() - equity) / equity.cummax()
            plt.plot(drawdown, color='red', linewidth=2)
            
            strategy_name = backtest_result.get('strategy_name', '未知策略')
            stock_code = backtest_result.get('stock_code', '未知股票')
            max_dd = backtest_result.get('max_drawdown', 0) * 100
            
            plt.title(f"{strategy_name} - {stock_code} 回撤曲线 (最大回撤: {max_dd:.2f}%)", fontsize=16, pad=20)
            plt.xlabel('日期', fontsize=12)
            plt.ylabel('回撤比例', fontsize=12)
            plt.grid(True)
            
            return plt.gcf()
        else:
            plt.title('无回撤数据', fontsize=14, pad=20)
            return plt.gcf()
    
    def _get_strategy_params(self, strategy_name: str) -> Dict[str, Any]:
        """获取策略参数
        
        Args:
            strategy_name: 策略名称
            
        Returns:
            策略参数字典
        """
        strategy_params = {}
        if strategy_name == "bollinger":
            strategy_params = {"period": 20, "num_std": 2.0}
        elif strategy_name == "rsi":
            strategy_params = {"period": 14, "overbought": 70, "oversold": 30}
        elif strategy_name == "macd":
            strategy_params = {"fast_period": 12, "slow_period": 26, "signal_period": 9}
        
        return strategy_params
    
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