import os
import sys
from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json

# 获取项目根目录
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT_DIR)

try:
    from src.utils.logger import logger
    from src.data.data_loader import DataLoader
    from configs.config import APP_HOST, APP_PORT, STOCK_POOL, BACKTEST_START, BACKTEST_END
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
        print("无法导入StockAnalyzer模块")
        # 创建一个简单的替代模块
        class StockAnalyzer:
            def __init__(self, *args, **kwargs):
                print("警告: 使用替代的StockAnalyzer模块")
            
            def analyze_stock(self, *args, **kwargs):
                return {"error": "StockAnalyzer模块不可用"}

from src.strategies.trading_strategy import StrategyFactory
from src.backtest.backtester import Backtester

# 创建FastAPI应用
app = FastAPI(
    title="AI量化交易系统API",
    description="基于DeepSeek大语言模型的港股量化交易系统API",
    version="0.1.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建共享的实例
data_loader = DataLoader()
stock_analyzer = StockAnalyzer(data_loader)
backtester = Backtester(data_loader)

# 请求模型
class BacktestRequest(BaseModel):
    """回测请求模型"""
    stock_code: str
    strategy_name: str
    start_date: Optional[str] = BACKTEST_START
    end_date: Optional[str] = BACKTEST_END
    initial_capital: Optional[float] = 100000.0
    
class AnalysisRequest(BaseModel):
    """分析请求模型"""
    stock_code: str
    days: Optional[int] = 90

class StrategyRequest(BaseModel):
    """策略参数请求模型"""
    strategy_name: str
    period: Optional[int] = None
    fast: Optional[int] = None
    slow: Optional[int] = None
    signal: Optional[int] = None
    overbought: Optional[float] = None
    oversold: Optional[float] = None

# API路由
@app.get("/")
async def root():
    """API根路径"""
    return {"message": "AI量化交易系统API", "version": "0.1.0"}

@app.get("/api/stocks")
async def get_stocks():
    """获取系统中配置的股票池"""
    return {"stocks": [{"code": code, "name": name} for code, name in STOCK_POOL.items()]}

@app.get("/api/stock/{stock_code}")
async def get_stock_data(stock_code: str, days: int = 90):
    """获取指定股票的历史数据和技术指标"""
    try:
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        # 获取股票数据
        stock_data = data_loader.get_stock_data(stock_code, start_date, end_date)
        if stock_data.empty:
            raise HTTPException(status_code=404, detail=f"无法获取股票数据: {stock_code}")
        
        # 计算技术指标
        stock_data_with_indicators = data_loader.calculate_technical_indicators(stock_data)
        
        # 转换为JSON可序列化格式
        result = {
            "stock_code": stock_code,
            "start_date": start_date,
            "end_date": end_date,
            "data": stock_data_with_indicators.reset_index().to_dict(orient="records")
        }
        
        return result
    except Exception as e:
        logger.error(f"获取股票数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze")
async def analyze_stock(request: AnalysisRequest):
    """分析股票并生成交易建议"""
    try:
        analysis = stock_analyzer.analyze_stock(request.stock_code, request.days)
        
        if "error" in analysis:
            raise HTTPException(status_code=404, detail=analysis["error"])
        
        # 处理不可序列化的对象
        if "technical_indicators" in analysis and isinstance(analysis["technical_indicators"], dict):
            for key, value in analysis["technical_indicators"].items():
                if hasattr(value, "to_dict"):
                    analysis["technical_indicators"][key] = value.to_dict()
            
        return analysis
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"分析股票失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/backtest")
async def run_backtest(request: BacktestRequest):
    """运行策略回测"""
    try:
        # 创建策略实例
        strategy_params = {}
        if request.strategy_name == "bollinger":
            strategy_params = {"period": 20, "num_std": 2.0}
        elif request.strategy_name == "rsi":
            strategy_params = {"period": 14, "overbought": 70, "oversold": 30}
        elif request.strategy_name == "macd":
            strategy_params = {"fast": 12, "slow": 26, "signal": 9}
            
        strategy = StrategyFactory.create_strategy(request.strategy_name, **strategy_params)
        
        # 运行回测
        result = backtester.run_backtest(
            strategy, 
            request.stock_code, 
            request.start_date, 
            request.end_date
        )
        
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
            
        # 处理结果中的pandas对象
        if "equity_curve" in result and hasattr(result["equity_curve"], "to_dict"):
            result["equity_curve"] = result["equity_curve"].to_dict()
            
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"回测失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/strategies")
async def get_strategies():
    """获取可用的交易策略列表"""
    return {"strategies": StrategyFactory.get_available_strategies()}

@app.post("/api/compare_strategies")
async def compare_strategies(background_tasks: BackgroundTasks, stock_code: str):
    """比较多个交易策略在单只股票上的表现"""
    try:
        # 创建不同策略实例
        strategies = [
            StrategyFactory.create_strategy("bollinger"),
            StrategyFactory.create_strategy("rsi"),
            StrategyFactory.create_strategy("macd"),
            StrategyFactory.create_strategy("combined")
        ]
        
        # 在后台任务中执行比较
        background_tasks.add_task(
            backtester.compare_strategies,
            stock_code,
            strategies,
            BACKTEST_START,
            BACKTEST_END
        )
        
        return {"message": f"策略比较任务已启动，对比 {len(strategies)} 个策略在 {stock_code} 上的表现"}
    except Exception as e:
        logger.error(f"策略比较失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/portfolio_analysis")
async def portfolio_analysis(background_tasks: BackgroundTasks, days: int = 90):
    """分析股票池中所有股票"""
    try:
        background_tasks.add_task(
            stock_analyzer.analyze_stock_pool,
            None,  # 使用默认股票池
            days
        )
        
        return {"message": f"股票池分析任务已启动，分析 {len(STOCK_POOL)} 只股票"}
    except Exception as e:
        logger.error(f"股票池分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def start_api_server():
    """启动API服务器"""
    import uvicorn
    try:
        logger.info(f"启动API服务器: {APP_HOST}:{APP_PORT}")
        uvicorn.run(app, host=APP_HOST, port=APP_PORT)
    except Exception as e:
        logger.error(f"启动API服务器失败: {str(e)}")
        print(f"启动API服务器失败: {str(e)}")

if __name__ == "__main__":
    start_api_server()