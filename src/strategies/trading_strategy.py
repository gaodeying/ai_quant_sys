import pandas as pd
import numpy as np
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union, Any
from datetime import datetime, timedelta

from src.utils.logger import logger
from configs.config import BOLLINGER_PERIOD, RSI_PERIOD, MACD_FAST, MACD_SLOW, MACD_SIGNAL

class BaseStrategy(ABC):
    """交易策略基类"""
    
    def __init__(self, name: str = "BaseStrategy"):
        """初始化策略基类
        
        Args:
            name: 策略名称
        """
        self.name = name
        logger.info(f"策略初始化: {self.name}")
    
    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """生成交易信号
        
        Args:
            data: 历史价格数据，包含技术指标
            
        Returns:
            添加了信号列的DataFrame
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
        portfolio['signal'] = signals['signal']
        portfolio['price'] = signals['Close']
        
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
    """布林带交易策略"""
    
    def __init__(self, period: int = BOLLINGER_PERIOD, num_std: float = 2.0):
        """初始化布林带策略
        
        Args:
            period: 移动平均窗口期
            num_std: 标准差倍数
        """
        super().__init__(name="BollingerBands")
        self.period = period
        self.num_std = num_std
        
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """生成布林带交易信号
        
        Args:
            data: 历史价格数据
            
        Returns:
            添加了信号列的DataFrame
        """
        df = data.copy()
        
        # 如果数据不包含布林带，则计算
        if 'SMA20' not in df.columns or 'Upper_Band' not in df.columns or 'Lower_Band' not in df.columns:
            df['SMA20'] = df['Close'].rolling(window=self.period).mean()
            df['STDEV'] = df['Close'].rolling(window=self.period).std()
            df['Upper_Band'] = df['SMA20'] + (df['STDEV'] * self.num_std)
            df['Lower_Band'] = df['SMA20'] - (df['STDEV'] * self.num_std)
            
        # 生成信号: 1代表做多，-1代表做空，0代表不操作
        df['signal'] = 0
        
        # 当价格突破下轨时买入
        df.loc[df['Close'] < df['Lower_Band'], 'signal'] = 1
        
        # 当价格突破上轨时卖出
        df.loc[df['Close'] > df['Upper_Band'], 'signal'] = -1
            
        return df


class RSIStrategy(BaseStrategy):
    """RSI交易策略"""
    
    def __init__(self, period: int = RSI_PERIOD, overbought: float = 70, oversold: float = 30):
        """初始化RSI策略
        
        Args:
            period: RSI计算周期
            overbought: 超买阈值
            oversold: 超卖阈值
        """
        super().__init__(name="RSI")
        self.period = period
        self.overbought = overbought
        self.oversold = oversold
        
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """生成RSI交易信号
        
        Args:
            data: 历史价格数据
            
        Returns:
            添加了信号列的DataFrame
        """
        df = data.copy()
        
        # 如果数据不包含RSI，则计算
        if 'RSI' not in df.columns:
            delta = df['Close'].diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            
            avg_gain = gain.rolling(window=self.period).mean()
            avg_loss = loss.rolling(window=self.period).mean()
            
            rs = avg_gain / avg_loss
            df['RSI'] = 100 - (100 / (1 + rs))
        
        # 生成信号
        df['signal'] = 0
        
        # 当RSI低于超卖线时买入
        df.loc[df['RSI'] < self.oversold, 'signal'] = 1
        
        # 当RSI高于超买线时卖出
        df.loc[df['RSI'] > self.overbought, 'signal'] = -1
        
        return df


class MACDStrategy(BaseStrategy):
    """MACD交易策略"""
    
    def __init__(self, fast: int = MACD_FAST, slow: int = MACD_SLOW, signal: int = MACD_SIGNAL):
        """初始化MACD策略
        
        Args:
            fast: 短期EMA周期
            slow: 长期EMA周期
            signal: 信号线周期
        """
        super().__init__(name="MACD")
        self.fast = fast
        self.slow = slow
        self.signal = signal
        
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """生成MACD交易信号
        
        Args:
            data: 历史价格数据
            
        Returns:
            添加了信号列的DataFrame
        """
        df = data.copy()
        
        # 如果数据不包含MACD相关指标，则计算
        if 'MACD' not in df.columns or 'Signal' not in df.columns:
            df['EMA_fast'] = df['Close'].ewm(span=self.fast, adjust=False).mean()
            df['EMA_slow'] = df['Close'].ewm(span=self.slow, adjust=False).mean()
            df['MACD'] = df['EMA_fast'] - df['EMA_slow']
            df['Signal'] = df['MACD'].ewm(span=self.signal, adjust=False).mean()
            df['Histogram'] = df['MACD'] - df['Signal']
        
        # 生成信号
        df['signal'] = 0
        
        # MACD金叉买入信号
        df.loc[(df['MACD'] > df['Signal']) & (df['MACD'].shift(1) <= df['Signal'].shift(1)), 'signal'] = 1
        
        # MACD死叉卖出信号
        df.loc[(df['MACD'] < df['Signal']) & (df['MACD'].shift(1) >= df['Signal'].shift(1)), 'signal'] = -1
        
        return df


class CombinedStrategy(BaseStrategy):
    """组合策略：结合多个技术指标"""
    
    def __init__(self):
        """初始化组合策略"""
        super().__init__(name="Combined")
        self.bb_strategy = BollingerBandsStrategy()
        self.rsi_strategy = RSIStrategy()
        self.macd_strategy = MACDStrategy()
        
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """生成组合策略交易信号
        
        Args:
            data: 历史价格数据
            
        Returns:
            添加了信号列的DataFrame
        """
        df = data.copy()
        
        # 获取各个策略的信号
        bb_signals = self.bb_strategy.generate_signals(df)['signal']
        rsi_signals = self.rsi_strategy.generate_signals(df)['signal']
        macd_signals = self.macd_strategy.generate_signals(df)['signal']
        
        # 组合信号：使用多数决策规则
        df['signal'] = 0
        
        # 至少两个策略给出买入信号时买入
        df.loc[(bb_signals + rsi_signals + macd_signals) >= 2, 'signal'] = 1
        
        # 至少两个策略给出卖出信号时卖出
        df.loc[(bb_signals + rsi_signals + macd_signals) <= -2, 'signal'] = -1
        
        return df


class AIEnhancedStrategy(BaseStrategy):
    """AI增强策略：结合大模型信号和技术指标"""
    
    def __init__(self, ai_signals: Dict[str, str]):
        """初始化AI增强策略
        
        Args:
            ai_signals: AI生成的交易信号，格式为{日期: 信号}
        """
        super().__init__(name="AIEnhanced")
        self.ai_signals = ai_signals
        self.combined_strategy = CombinedStrategy()
        
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """生成AI增强策略交易信号
        
        Args:
            data: 历史价格数据
            
        Returns:
            添加了信号列的DataFrame
        """
        df = data.copy()
        
        # 获取技术指标组合策略信号
        tech_signals = self.combined_strategy.generate_signals(df)['signal']
        
        # 添加AI信号
        df['ai_signal'] = 0
        
        # 将AI信号转换为数值
        for date, signal in self.ai_signals.items():
            if date in df.index:
                if signal.lower() in ['买入', 'buy', 'long']:
                    df.loc[date, 'ai_signal'] = 1
                elif signal.lower() in ['卖出', 'sell', 'short']:
                    df.loc[date, 'ai_signal'] = -1
        
        # 组合技术指标信号和AI信号
        # AI信号权重更高
        df['signal'] = 0
        
        # 如果AI信号和技术信号一致，则跟随信号
        df.loc[(df['ai_signal'] == 1) & (tech_signals >= 0), 'signal'] = 1
        df.loc[(df['ai_signal'] == -1) & (tech_signals <= 0), 'signal'] = -1
        
        # 如果AI信号强烈（例如，连续两天相同信号），则忽略技术信号
        df.loc[df['ai_signal'] == 1, 'signal'] = 1
        df.loc[df['ai_signal'] == -1, 'signal'] = -1
        
        return df


class StrategyFactory:
    """策略工厂：用于创建和管理不同的交易策略"""
    
    @staticmethod
    def create_strategy(strategy_name: str, **kwargs) -> BaseStrategy:
        """创建策略实例
        
        Args:
            strategy_name: 策略名称
            **kwargs: 策略参数
            
        Returns:
            策略实例
        """
        strategies = {
            'bollinger': BollingerBandsStrategy,
            'rsi': RSIStrategy,
            'macd': MACDStrategy,
            'combined': CombinedStrategy,
            'ai_enhanced': AIEnhancedStrategy
        }
        
        if strategy_name.lower() not in strategies:
            logger.error(f"未知策略: {strategy_name}")
            raise ValueError(f"未知策略: {strategy_name}")
        
        strategy_class = strategies[strategy_name.lower()]
        return strategy_class(**kwargs)
    
    @staticmethod
    def get_available_strategies() -> List[str]:
        """获取可用策略列表
        
        Returns:
            策略名称列表
        """
        return ['bollinger', 'rsi', 'macd', 'combined', 'ai_enhanced'] 