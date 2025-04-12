import pandas as pd
import numpy as np
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union, Any
from datetime import datetime, timedelta

from loguru import logger
from configs.config import TECHNICAL_PARAMS

class BaseStrategy(ABC):
    """交易策略基类"""
    
    def __init__(self, name: str):
        """初始化策略
        
        Args:
            name: 策略名称
        """
        self.name = name
        logger.info(f"初始化策略: {name}")
    
    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """生成交易信号
        
        Args:
            data: 股票数据，包含技术指标
            
        Returns:
            交易信号序列，1表示买入，-1表示卖出，0表示持有
        """
        pass
    
    def evaluate(self, data: pd.DataFrame, initial_capital: float = 100000.0) -> Dict[str, Any]:
        """评估策略表现
        
        Args:
            data: 包含交易信号的DataFrame
            initial_capital: 初始资金
            
        Returns:
            策略评估结果字典
        """
        signals = self.generate_signals(data)
        
        # 创建一个DataFrame进行回测
        portfolio = pd.DataFrame(index=signals.index)
        portfolio['signal'] = signals
        portfolio['price'] = data['Close']
        
        # 计算每日回报
        portfolio['returns'] = portfolio['price'].pct_change()
        
        # 计算策略回报，根据前一天的信号计算当天的策略回报
        portfolio['strategy_returns'] = portfolio['returns'] * portfolio['signal'].shift(1)
        
        # 计算策略价值
        portfolio['equity_curve'] = (1.0 + portfolio['strategy_returns']).cumprod() * initial_capital
        
        # 计算最大回撤
        portfolio['cummax'] = portfolio['equity_curve'].cummax()
        portfolio['drawdown'] = portfolio['cummax'] - portfolio['equity_curve']
        portfolio['drawdown_pct'] = portfolio['drawdown'] / portfolio['cummax']
        
        # 计算各种指标
        total_return = portfolio['equity_curve'].iloc[-1] / initial_capital - 1.0
        annualized_return = (1 + total_return) ** (252 / len(portfolio)) - 1
        max_drawdown = portfolio['drawdown_pct'].max()
        sharpe_ratio = np.sqrt(252) * portfolio['strategy_returns'].mean() / portfolio['strategy_returns'].std()
        
        trades = portfolio['signal'].diff().fillna(0) != 0
        num_trades = trades.sum()
        
        # 计算胜率
        if num_trades > 0:
            winning_trades = (portfolio['strategy_returns'][trades] > 0).sum()
            win_rate = winning_trades / num_trades
        else:
            win_rate = 0
        
        return {
            'strategy': self.name,
            'total_return': total_return,
            'annualized_return': annualized_return,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'num_trades': num_trades,
            'win_rate': win_rate,
            'equity_curve': portfolio['equity_curve']
        }
        

class BollingerBandsStrategy(BaseStrategy):
    """布林带策略"""
    
    def __init__(self, period: Optional[int] = None, num_std: float = 2.0):
        """初始化布林带策略
        
        Args:
            period: 移动平均周期
            num_std: 标准差倍数
        """
        super().__init__("布林带策略")
        self.period = period or TECHNICAL_PARAMS["BB_PERIOD"]
        self.num_std = num_std
        
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """生成布林带交易信号"""
        if data.empty:
            return pd.Series()
            
        # 计算布林带
        ma = data["Close"].rolling(window=self.period).mean()
        std = data["Close"].rolling(window=self.period).std()
        upper = ma + self.num_std * std
        lower = ma - self.num_std * std
        
        # 生成信号
        signals = pd.Series(0, index=data.index)
        signals[data["Close"] <= lower] = 1  # 买入信号
        signals[data["Close"] >= upper] = -1  # 卖出信号
        
        return signals


class RSIStrategy(BaseStrategy):
    """RSI策略"""
    
    def __init__(self, period: Optional[int] = None, overbought: float = 70, oversold: float = 30):
        """初始化RSI策略
        
        Args:
            period: RSI周期
            overbought: 超买阈值
            oversold: 超卖阈值
        """
        super().__init__("RSI策略")
        self.period = period or TECHNICAL_PARAMS["RSI_PERIOD"]
        self.overbought = overbought
        self.oversold = oversold
        
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """生成RSI交易信号"""
        if data.empty:
            return pd.Series()
            
        # 计算RSI
        delta = data["Close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        # 生成信号
        signals = pd.Series(0, index=data.index)
        signals[rsi <= self.oversold] = 1  # 买入信号
        signals[rsi >= self.overbought] = -1  # 卖出信号
        
        return signals


class MACDStrategy(BaseStrategy):
    """MACD策略"""
    
    def __init__(
        self, 
        fast_period: Optional[int] = None,
        slow_period: Optional[int] = None,
        signal_period: Optional[int] = None
    ):
        """初始化MACD策略
        
        Args:
            fast_period: 快线周期
            slow_period: 慢线周期
            signal_period: 信号线周期
        """
        super().__init__("MACD策略")
        self.fast_period = fast_period if fast_period is not None else TECHNICAL_PARAMS["MACD_FAST"]
        self.slow_period = slow_period if slow_period is not None else TECHNICAL_PARAMS["MACD_SLOW"]
        self.signal_period = signal_period if signal_period is not None else TECHNICAL_PARAMS["MACD_SIGNAL"]
        
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """生成MACD交易信号"""
        if data.empty:
            return pd.Series()
            
        # 计算MACD
        exp1 = data["Close"].ewm(span=self.fast_period, adjust=False).mean()
        exp2 = data["Close"].ewm(span=self.slow_period, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=self.signal_period, adjust=False).mean()
        hist = macd - signal
        
        # 生成信号
        signals = pd.Series(0, index=data.index)
        signals[hist > 0] = 1  # 买入信号
        signals[hist < 0] = -1  # 卖出信号
        
        return signals


class CombinedStrategy(BaseStrategy):
    """组合策略"""
    
    def __init__(self):
        """初始化组合策略"""
        super().__init__("组合策略")
        self.strategies = [
            BollingerBandsStrategy(),
            RSIStrategy(),
            MACDStrategy()
        ]
        
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """生成组合策略信号"""
        if data.empty:
            return pd.Series()
            
        # 获取各个策略的信号
        signals = []
        for strategy in self.strategies:
            signals.append(strategy.generate_signals(data))
            
        # 组合信号（简单投票机制）
        combined = sum(signals)
        final_signals = pd.Series(0, index=data.index)
        final_signals[combined > 1] = 1  # 多数策略看多
        final_signals[combined < -1] = -1  # 多数策略看空
        
        return final_signals


class StrategyFactory:
    """策略工厂类"""
    
    _strategies = {
        "bollinger": BollingerBandsStrategy,
        "rsi": RSIStrategy,
        "macd": MACDStrategy,
        "combined": CombinedStrategy
    }
    
    _param_mappings = {
        "macd": {
            "fast_period": "fast_period",
            "slow_period": "slow_period",
            "signal_period": "signal_period"
        },
        "bollinger": {
            "period": "period",
            "std": "num_std"
        },
        "rsi": {
            "period": "period",
            "overbought": "overbought",
            "oversold": "oversold"
        }
    }
    
    @classmethod
    def create_strategy(cls, strategy_name: str, **kwargs) -> BaseStrategy:
        """创建策略实例
        
        Args:
            strategy_name: 策略名称
            **kwargs: 策略参数
        """
        if strategy_name not in cls._strategies:
            raise ValueError(f"不支持的策略类型: {strategy_name}")
            
        # 如果存在参数映射，进行转换
        if strategy_name in cls._param_mappings:
            mapped_kwargs = {}
            for api_param, strat_param in cls._param_mappings[strategy_name].items():
                if api_param in kwargs:
                    mapped_kwargs[strat_param] = kwargs[api_param]
            kwargs = mapped_kwargs
            
        return cls._strategies[strategy_name](**kwargs)
    
    @classmethod
    def get_available_strategies(cls) -> List[str]:
        """获取可用的策略列表"""
        return list(cls._strategies.keys()) 