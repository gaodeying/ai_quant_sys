import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple
import json
import os
from pathlib import Path

from src.utils.logger import logger
from src.data.data_loader import DataLoader
from src.strategies.trading_strategy import BaseStrategy, StrategyFactory
from configs.config import DATA_DIR, INITIAL_CAPITAL

class Backtester:
    """回测引擎：用于评估交易策略的历史表现"""
    
    def __init__(self, 
                 data_loader: Optional[DataLoader] = None, 
                 initial_capital: float = INITIAL_CAPITAL):
        """初始化回测引擎
        
        Args:
            data_loader: 数据加载器，如未提供则创建新实例
            initial_capital: 初始资金
        """
        self.data_loader = data_loader or DataLoader()
        self.initial_capital = initial_capital
        self.results_dir = DATA_DIR / "backtest_results"
        os.makedirs(self.results_dir, exist_ok=True)
        logger.info(f"回测引擎初始化完成，初始资金: {self.initial_capital:.2f}")
        
    def run_backtest(self, 
                     strategy: BaseStrategy, 
                     stock_code: str, 
                     start_date: str, 
                     end_date: str,
                     initial_capital: Optional[float] = None,
                     use_cache: bool = True,
                     save_result: bool = True) -> Dict[str, Any]:
        """运行单个股票的回测
        
        Args:
            strategy: 交易策略实例
            stock_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            initial_capital: 初始资金，如果未提供则使用默认值
            use_cache: 是否使用缓存数据
            save_result: 是否保存回测结果
            
        Returns:
            回测结果字典
        """
        logger.info(f"开始回测: 股票={stock_code}, 策略={strategy.name}, 日期范围: {start_date} 至 {end_date}")
        
        # 获取股票数据
        stock_data = self.data_loader.get_stock_data(stock_code, start_date, end_date, use_cache)
        if stock_data.empty:
            logger.error(f"无法获取股票数据: {stock_code}")
            return {"error": f"无法获取股票数据: {stock_code}"}
        
        # 计算技术指标
        stock_data_with_indicators = self.data_loader.calculate_technical_indicators(stock_data)
        
        # 运行策略评估
        backtest_result = strategy.evaluate(stock_data_with_indicators, initial_capital or self.initial_capital)
        
        # 添加回测元信息
        backtest_result.update({
            'stock_code': stock_code,
            'start_date': start_date,
            'end_date': end_date,
            'strategy_name': strategy.name,
            'initial_capital': initial_capital or self.initial_capital,
            'backtest_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
        # 保存回测结果
        if save_result:
            try:
                self._save_backtest_result(backtest_result, stock_code, strategy.name)
            except Exception as e:
                logger.error(f"保存回测结果失败: {str(e)}")
        
        logger.info(f"回测完成: {stock_code}, 总回报率: {backtest_result['total_return']:.2%}")
        return backtest_result
    
    def run_multi_stock_backtest(self, 
                                strategy: BaseStrategy, 
                                stock_codes: List[str], 
                                start_date: str, 
                                end_date: str,
                                use_cache: bool = True) -> Dict[str, Dict[str, Any]]:
        """运行多个股票的回测
        
        Args:
            strategy: 交易策略实例
            stock_codes: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            use_cache: 是否使用缓存数据
            
        Returns:
            字典，键为股票代码，值为回测结果
        """
        results = {}
        
        for code in stock_codes:
            try:
                result = self.run_backtest(strategy, code, start_date, end_date, use_cache)
                results[code] = result
            except Exception as e:
                logger.error(f"回测失败: {code}, 错误: {str(e)}")
                results[code] = {"error": str(e)}
        
        # 计算组合表现
        self._calculate_portfolio_performance(results)
        
        return results
    
    def compare_strategies(self, 
                          stock_code: str, 
                          strategies: List[BaseStrategy], 
                          start_date: str, 
                          end_date: str,
                          use_cache: bool = True) -> List[Dict[str, Any]]:
        """比较多个策略在单个股票上的表现
        
        Args:
            stock_code: 股票代码
            strategies: 策略实例列表
            start_date: 开始日期
            end_date: 结束日期
            use_cache: 是否使用缓存数据
            
        Returns:
            回测结果列表
        """
        results = []
        
        for strategy in strategies:
            try:
                result = self.run_backtest(strategy, stock_code, start_date, end_date, use_cache)
                results.append(result)
            except Exception as e:
                logger.error(f"策略 {strategy.name} 回测失败: {str(e)}")
                results.append({"strategy": strategy.name, "error": str(e)})
        
        # 生成比较报告
        self._generate_strategy_comparison_report(results, stock_code)
        
        return results
    
    def plot_equity_curves(self, backtest_results: List[Dict[str, Any]], title: str = "策略净值曲线对比") -> plt.Figure:
        """绘制策略净值曲线
        
        Args:
            backtest_results: 回测结果列表
            title: 图表标题
            
        Returns:
            matplotlib图表对象
        """
        plt.figure(figsize=(12, 6))
        
        for result in backtest_results:
            if 'equity_curve' in result and not isinstance(result['equity_curve'], str):
                plt.plot(result['equity_curve'], label=f"{result['strategy']} ({result.get('stock_code', '')})")
        
        plt.title(title)
        plt.xlabel('日期')
        plt.ylabel('策略净值')
        plt.legend()
        plt.grid(True)
        
        # 保存图表
        fig_path = self.results_dir / f"equity_curves_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(fig_path)
        logger.info(f"策略净值曲线已保存: {fig_path}")
        
        return plt.gcf()
    
    def plot_drawdowns(self, backtest_results: List[Dict[str, Any]], title: str = "策略回撤对比") -> plt.Figure:
        """绘制策略回撤曲线
        
        Args:
            backtest_results: 回测结果列表
            title: 图表标题
            
        Returns:
            matplotlib图表对象
        """
        plt.figure(figsize=(12, 6))
        
        for result in backtest_results:
            if 'equity_curve' in result and not isinstance(result['equity_curve'], str):
                # 计算回撤
                equity = result['equity_curve']
                drawdown = (equity.cummax() - equity) / equity.cummax()
                plt.plot(drawdown, label=f"{result['strategy']} ({result.get('stock_code', '')})")
        
        plt.title(title)
        plt.xlabel('日期')
        plt.ylabel('回撤比例')
        plt.legend()
        plt.grid(True)
        
        # 保存图表
        fig_path = self.results_dir / f"drawdowns_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(fig_path)
        logger.info(f"策略回撤曲线已保存: {fig_path}")
        
        return plt.gcf()
    
    def _prepare_result_for_json(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """准备回测结果以进行JSON序列化
        
        Args:
            result: 原始回测结果字典
            
        Returns:
            处理后的可JSON序列化的字典
        """
        result_copy = result.copy()
        
        # 处理pandas Series和DataFrame
        if 'equity_curve' in result_copy and isinstance(result_copy['equity_curve'], (pd.Series, pd.DataFrame)):
            # 将索引转换为字符串
            equity_curve_dict = {}
            for date, value in result_copy['equity_curve'].items():
                equity_curve_dict[str(date)] = value
            result_copy['equity_curve'] = equity_curve_dict
            
        # 处理numpy数值类型
        for key, value in result_copy.items():
            if isinstance(value, (np.int64, np.float64)):
                result_copy[key] = float(value)
            elif isinstance(value, np.ndarray):
                result_copy[key] = value.tolist()
            elif isinstance(value, pd.Timestamp):
                result_copy[key] = str(value)
                
        return result_copy
        
    def _save_backtest_result(self, result: Dict[str, Any], stock_code: str, strategy_name: str):
        """保存回测结果
        
        Args:
            result: 回测结果字典
            stock_code: 股票代码
            strategy_name: 策略名称
        """
        try:
            # 准备结果进行JSON序列化
            result_copy = self._prepare_result_for_json(result)
            
            # 生成文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{stock_code}_{strategy_name}_{timestamp}.json"
            filepath = self.results_dir / filename
            
            # 保存结果
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(result_copy, f, ensure_ascii=False, indent=4)
                
            logger.info(f"回测结果已保存: {filepath}")
            
        except Exception as e:
            logger.error(f"保存回测结果失败: {str(e)}")
    
    def _calculate_portfolio_performance(self, results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """计算投资组合整体表现
        
        Args:
            results: 回测结果字典，键为股票代码
            
        Returns:
            投资组合表现指标
        """
        # 过滤出有效的回测结果
        valid_results = {k: v for k, v in results.items() if 'error' not in v}
        
        if not valid_results:
            logger.warning("没有有效的回测结果，无法计算组合表现")
            return {"error": "没有有效的回测结果"}
        
        # 计算平均指标
        total_returns = [result['total_return'] for result in valid_results.values()]
        annualized_returns = [result['annualized_return'] for result in valid_results.values()]
        max_drawdowns = [result['max_drawdown'] for result in valid_results.values()]
        sharpe_ratios = [result['sharpe_ratio'] for result in valid_results.values()]
        
        portfolio_metrics = {
            'strategy': valid_results[list(valid_results.keys())[0]]['strategy_name'],
            'num_stocks': len(valid_results),
            'avg_total_return': np.mean(total_returns),
            'avg_annualized_return': np.mean(annualized_returns),
            'avg_max_drawdown': np.mean(max_drawdowns),
            'avg_sharpe_ratio': np.mean(sharpe_ratios),
            'best_stock': max(valid_results.keys(), key=lambda k: valid_results[k]['total_return']),
            'worst_stock': min(valid_results.keys(), key=lambda k: valid_results[k]['total_return']),
            'best_return': max(total_returns),
            'worst_return': min(total_returns),
        }
        
        # 保存组合表现
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_name = f"portfolio_{portfolio_metrics['strategy']}_{timestamp}.json"
        file_path = self.results_dir / file_name
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(portfolio_metrics, f, ensure_ascii=False, indent=4)
        
        logger.info(f"组合表现已保存: {file_path}")
        return portfolio_metrics
    
    def _generate_strategy_comparison_report(self, results: List[Dict[str, Any]], stock_code: str) -> str:
        """生成策略比较报告
        
        Args:
            results: 回测结果列表
            stock_code: 股票代码
            
        Returns:
            报告文件路径
        """
        # 过滤出有效的回测结果
        valid_results = [r for r in results if 'error' not in r]
        
        if not valid_results:
            logger.warning("没有有效的回测结果，无法生成比较报告")
            return ""
        
        # 创建比较报告
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_name = f"strategy_comparison_{stock_code}_{timestamp}.txt"
        file_path = self.results_dir / file_name
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"策略比较报告 - {stock_code}\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"回测区间: {valid_results[0]['start_date']} 至 {valid_results[0]['end_date']}\n")
            f.write(f"初始资金: {valid_results[0]['initial_capital']:.2f}\n\n")
            
            f.write("策略表现对比:\n")
            f.write("-" * 80 + "\n")
            f.write(f"{'策略名称':<15}{'总回报':<12}{'年化回报':<12}{'最大回撤':<12}{'夏普比率':<12}{'交易次数':<12}{'胜率':<12}\n")
            f.write("-" * 80 + "\n")
            
            for result in valid_results:
                f.write(f"{result['strategy']:<15}")
                f.write(f"{result['total_return']:.2%:<12}")
                f.write(f"{result['annualized_return']:.2%:<12}")
                f.write(f"{result['max_drawdown']:.2%:<12}")
                f.write(f"{result['sharpe_ratio']:.2f:<12}")
                f.write(f"{int(result['num_trades']):<12}")
                f.write(f"{result['win_rate']:.2%:<12}\n")
            
            f.write("-" * 80 + "\n\n")
            f.write("总结:\n")
            
            # 找出最佳策略
            best_strategy = max(valid_results, key=lambda x: x['total_return'])
            f.write(f"最佳策略: {best_strategy['strategy']}, 总回报: {best_strategy['total_return']:.2%}\n")
            
            # 找出夏普比率最高的策略
            best_sharpe = max(valid_results, key=lambda x: x['sharpe_ratio'])
            f.write(f"风险调整收益最佳策略: {best_sharpe['strategy']}, 夏普比率: {best_sharpe['sharpe_ratio']:.2f}\n")
            
            # 找出回撤最小的策略
            min_drawdown = min(valid_results, key=lambda x: x['max_drawdown'])
            f.write(f"最小回撤策略: {min_drawdown['strategy']}, 最大回撤: {min_drawdown['max_drawdown']:.2%}\n")
            
        logger.info(f"策略比较报告已生成: {file_path}")
        return str(file_path) 