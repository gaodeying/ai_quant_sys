# AI量化交易系统

基于人工智能的港股量化交易系统，集成了数据获取、分析、策略生成和回测功能。

## 功能特点

- 自动获取港股数据（主要关注恒生科技指数成分股）
- 使用DeepSeek AI模型进行智能分析
- 技术指标分析（RSI、MACD、布林带等）
- 自动生成交易信号
- 提供回测功能
- Web界面展示
- RESTful API支持

## 系统要求

- Python 3.8+
- pip包管理器
- 操作系统：Windows/Linux/MacOS

## 安装步骤

1. 克隆项目：
```bash
git clone [项目地址]
cd ai_quant_sys
```

2. 创建并激活虚拟环境：
```bash
python -m venv venv
source venv/bin/activate  # Linux/MacOS
venv\Scripts\activate     # Windows
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

4. 配置环境变量：
- 复制 `.env.example` 到 `.env`
- 填写必要的API密钥和配置

## 使用说明

### 方式一：使用主程序（推荐）

1. 启动完整系统：
```bash
python main.py
```

2. 启动选项：
- `--api-only`: 仅启动API服务
- `--ui-only`: 仅启动UI服务
- `--no-scheduler`: 不启动定时任务
- `--debug`: 启用调试模式

3. 访问Web界面：
- 打开浏览器访问 `http://localhost:7860`

4. API文档：
- 访问 `http://localhost:8000/docs` 查看API文档

### 方式二：仅启动API服务器

如果只需要API功能，可以直接启动API服务器：

```bash
python -m src.api.api_server
```

API服务器默认在8888端口启动。如遇端口冲突，可修改`src/api/api_server.py`中的端口号。

## API使用指南

### 可用API端点

1. 获取可用策略列表
```bash
curl -X GET http://localhost:8888/api/strategies
```

2. 查询股票数据
```bash
curl -X GET http://localhost:8888/api/stock/9988.HK?days=90
```

3. 运行回测
```bash
curl -X POST -H "Content-Type: application/json" -d '{
  "stock_code": "9988.HK", 
  "strategy_name": "macd", 
  "start_date": "2023-01-01", 
  "end_date": "2024-03-14", 
  "fast_period": 12, 
  "slow_period": 26, 
  "signal_period": 9
}' http://localhost:8888/api/backtest
```

4. 股票分析
```bash
curl -X POST -H "Content-Type: application/json" -d '{
  "stock_code": "9988.HK",
  "days": 90
}' http://localhost:8888/api/analyze
```

5. 比较不同策略
```bash
curl -X POST -H "Content-Type: application/json" -d '{
  "stock_code": "9988.HK"
}' http://localhost:8888/api/compare_strategies
```

6. 投资组合分析
```bash
curl -X GET http://localhost:8888/api/portfolio_analysis?days=90
```

### 可用策略

系统目前支持四种策略：
- `bollinger`：布林带策略
- `rsi`：RSI相对强弱指标策略
- `macd`：MACD指标策略
- `combined`：以上三种策略的组合策略

### 策略参数

不同策略支持不同参数：

#### MACD策略参数
- `fast_period`：快线周期（默认12）
- `slow_period`：慢线周期（默认26）
- `signal_period`：信号线周期（默认9）

#### RSI策略参数
- `overbought`：超买阈值（默认70）
- `oversold`：超卖阈值（默认30）

#### 布林带策略参数
- `num_std`：标准差倍数（默认2.0）

### 回测结果说明

回测结果包含以下指标：
- `total_return`：总回报率
- `max_drawdown`：最大回撤
- `sharpe_ratio`：夏普比率
- `num_trades`：交易次数
- `win_rate`：胜率

## 项目结构

```
ai_quant_sys/
├── configs/            # 配置文件
├── data/              # 数据文件
├── logs/              # 日志文件
├── src/               # 源代码
│   ├── api/          # API服务
│   ├── data/         # 数据处理
│   ├── models/       # AI模型
│   ├── strategies/   # 交易策略
│   ├── ui/           # Web界面
│   └── utils/        # 工具函数
├── tests/            # 测试文件
├── .env              # 环境变量
├── main.py           # 主程序
└── requirements.txt  # 依赖包
```

## 配置说明

1. API密钥配置（在 `.env` 文件中）：
- `DEEPSEEK_API_KEY`: DeepSeek API密钥
- `AKSHARE_TOKEN`: AKShare数据源Token
- `TUSHARE_TOKEN`: TuShare数据源Token

2. 股票池配置（在 `configs/config.py` 中）：
- 可以修改 `STOCK_POOL` 字典来自定义关注的股票

3. 交易参数配置：
- 在 `configs/config.py` 中设置各种交易参数
- 包括止损比例、最大持仓等

## 常见问题解决

1. 端口冲突问题
   - API服务器默认使用8888端口，可在 `src/api/api_server.py` 中修改
   - UI服务默认使用7860端口，可在 `configs/config.py` 中修改 `UI_PORT`

2. 数据问题
   - 回测数据存储在 `data/cache` 目录
   - 回测结果保存在 `data/backtest_results` 目录
   - 如遇数据问题，可尝试删除缓存重新获取

3. 日志查看
   - 系统日志存储在 `logs` 目录下
   - 按日期命名，可查看运行记录和错误信息

## 开发说明

1. 添加新的策略：
- 在 `src/strategies/` 下创建新的策略类
- 继承 `BaseStrategy` 类
- 实现必要的方法

2. 自定义技术指标：
- 在 `src/models/technical_indicators.py` 中添加

3. 修改UI：
- UI组件在 `src/ui/` 目录下
- 使用Gradio框架

## 注意事项

1. API限制：
- 注意各数据源的API调用限制
- 建议启用数据缓存

2. 风险提示：
- 本系统仅供学习研究使用
- 实盘交易需自行承担风险

## 贡献指南

欢迎提交Issue和Pull Request来改进系统。

## 许可证

MIT License 