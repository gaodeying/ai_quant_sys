# AI 量化交易系统

基于DeepSeek大语言模型的轻量级量化交易系统，用于港股恒生科技指数下的股票分析和投资。

## 系统功能

- 数据获取与处理：自动从多个数据源获取港股数据，计算常用技术指标
- 智能分析：利用DeepSeek大模型对股票进行智能分析和预测
- 交易策略：内置多种交易策略，包括技术指标策略和AI增强策略
- 回测系统：对交易策略进行历史回测，评估策略表现
- Web界面：友好的图形用户界面，轻松操作和查看结果
- API服务：提供RESTful API接口，便于与其他系统集成
- 自动化任务：定时获取数据和运行策略分析

## 系统架构

```
ai_quant_sys/
├── configs/            # 配置文件
├── data/               # 数据目录
├── logs/               # 日志目录
├── src/
│   ├── api/            # API服务
│   ├── backtest/       # 回测引擎
│   ├── data/           # 数据处理
│   ├── models/         # 分析模型
│   ├── strategies/     # 交易策略
│   ├── ui/             # 用户界面
│   └── utils/          # 工具函数
├── .env                # 环境变量配置
├── main.py             # 主程序入口
├── requirements.txt    # 依赖包列表
└── README.md           # 项目说明
```

## 安装指南

### 系统要求

- Python 3.9+ (已在Python 3.9和3.11上测试)
- MacOS, Linux 或 Windows
- 最小8GB内存，推荐16GB以上
- 稳定的网络连接

### 安装步骤

1. 克隆或下载本项目：

```bash
git clone <repository-url>
cd ai_quant_sys
```

2. 创建虚拟环境：

```bash
python -m venv venv
```

3. 激活虚拟环境：

在 MacOS/Linux 上：
```bash
source venv/bin/activate
```

在 Windows 上：
```bash
venv\Scripts\activate
```

4. 安装依赖包：

```bash
pip install -r requirements.txt
```

> **注意**：某些依赖项可能需要系统级的支持库。如果安装过程中遇到问题，请参考每个库的官方文档。

5. 配置环境变量：

编辑 `.env` 文件，填入相关API密钥：

```
# OpenAI API配置（用于调用DeepSeek模型）
OPENAI_API_KEY=your_openai_api_key
DEEPSEEK_API_BASE=https://api.deepseek.com/v1

# Tushare API配置
TUSHARE_TOKEN=your_tushare_token

# 日志配置
LOG_LEVEL=INFO
```

## 使用指南

### 启动系统

启动完整系统（API和UI）：

```bash
python main.py
```

仅启动API服务：

```bash
python main.py --api-only
```

仅启动UI界面：

```bash
python main.py --ui-only
```

不启动定时任务：

```bash
python main.py --no-scheduler
```

调试模式启动：

```bash
python main.py --debug
```

### 使用Web界面

启动后，可以通过浏览器访问系统Web界面：

```
http://127.0.0.1:7860/
```

Web界面具有三个主要标签页：

1. **股票分析**：选择股票和分析天数，获取AI分析、技术指标和价格图表
2. **策略回测**：选择股票、策略和日期范围，进行回测并查看结果
3. **投资组合**：分析股票池中所有股票，获取排名和推荐

### 使用API

系统提供RESTful API接口，可通过以下地址访问：

```
http://127.0.0.1:8080/
```

主要API端点：

- `GET /api/stocks`：获取股票池列表
- `GET /api/stock/{stock_code}`：获取指定股票的数据
- `POST /api/analyze`：分析指定的股票
- `POST /api/backtest`：运行策略回测
- `GET /api/strategies`：获取可用策略列表
- `POST /api/compare_strategies`：比较多个策略
- `GET /api/portfolio_analysis`：分析投资组合

完整API文档可通过访问以下地址获取：

```
http://127.0.0.1:8080/docs
```

## 内置策略

系统内置以下交易策略：

1. **布林带策略**：基于布林带指标的均值回归策略
2. **RSI策略**：基于相对强弱指数的超买超卖策略
3. **MACD策略**：基于MACD指标的趋势跟踪策略
4. **组合策略**：结合多个技术指标的综合策略
5. **AI增强策略**：结合DeepSeek大模型和技术指标的智能策略

## 系统优化说明

本系统经过以下优化，以确保可以直接运行：

1. **路径处理优化**：修复了相对路径和导入路径问题，确保在任何位置执行都能正确找到所需模块
2. **错误处理增强**：添加了全面的错误捕获和日志记录，使系统更加健壮
3. **依赖管理改进**：更新了依赖项版本规范，添加了兼容性依赖，减少包冲突
4. **模块结构统一**：解决了模块命名不一致的问题(`models`和`model`)
5. **代码健壮性提升**：添加了各种边界情况检查，即使某些组件不可用也能继续运行
6. **降低启动依赖**：简化了启动过程，即使某些组件不可用也能启动部分功能
7. **目录自动创建**：确保必要的数据和日志目录自动创建
8. **添加缺失组件**：添加了缺失的模块，如StockAnalyzer实现
9. **接口信息改进**：UI界面增加了更多信息提示和错误反馈

## 故障排除

### 常见问题

1. **系统启动失败**
   - 确保所有依赖包都已安装: `pip install -r requirements.txt`
   - 检查 `.env` 文件配置是否正确
   - 查看日志目录下的日志文件获取详细错误信息
   - 尝试单独启动API或UI: `python main.py --api-only` 或 `python main.py --ui-only`

2. **无法获取股票数据**
   - 检查网络连接
   - 确保API密钥配置正确
   - 部分数据源可能有请求限制，尝试减少请求频率
   - 先确保data目录存在并有写入权限

3. **大模型分析失败**
   - 确保OpenAI API密钥配置正确
   - 检查DeepSeek API基础URL配置
   - API调用可能有额度限制，查看API提供商的使用条款
   - 如果模型不可用，系统会自动使用基本技术指标进行分析

4. **回测结果不准确**
   - 调整回测起始和结束日期，确保有足够的历史数据
   - 检查是否有足够的历史数据
   - 考虑使用不同的策略参数
   - 查看日志以获取潜在的数据问题

5. **UI界面加载失败**
   - 确保Gradio库已正确安装: `pip install gradio==3.50.2`
   - 检查是否已有其他服务使用了7860端口
   - 查看控制台输出，寻找潜在错误信息

### 日志文件

系统日志存储在 `logs` 目录中，按日期分类。查看最新的日志文件可以帮助识别和解决问题：

```bash
cat logs/$(date +%Y-%m-%d).log
```

## 自定义配置

系统主要配置在 `configs/config.py` 文件中，你可以修改以下配置：

- 股票池配置: 修改 `STOCK_POOL` 列表
- 回测参数: 修改起始日期、结束日期和初始资金
- 策略参数: 调整各种技术指标的参数
- Web应用配置: 修改主机和端口
- 定时任务配置: 调整数据更新和策略运行的时间
- 日志配置: 修改日志级别和格式

## 扩展与定制

要扩展系统功能，您可以：

1. **添加新策略**: 在 `src/strategies/trading_strategy.py` 中创建新策略类，继承 `BaseStrategy`
2. **添加新数据源**: 在 `src/data/data_loader.py` 中实现新的数据获取方法
3. **自定义UI界面**: 修改 `src/ui/app.py` 中的Gradio界面
4. **添加新API端点**: 在 `src/api/api_server.py` 中添加新的FastAPI路由

## 注意事项

- 本系统仅供学习和研究使用，不构成投资建议
- 实际交易中应谨慎使用算法生成的交易信号
- 系统性能和分析结果取决于数据质量和API可用性
- 大模型生成的分析内容仅供参考，不应作为唯一决策依据

## 许可证

[MIT License](LICENSE) 