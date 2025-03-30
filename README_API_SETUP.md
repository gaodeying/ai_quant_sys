# AI量化系统 API 设置指南

本文档将指导您如何正确设置 DeepSeek API，以便系统能够正常使用 AI 分析功能。

## DeepSeek API 设置步骤

### 1. 注册 DeepSeek 账号

首先，您需要注册一个 DeepSeek 账号：

1. 访问 [DeepSeek 官网](https://deepseek.com/)
2. 点击"注册"或"Sign Up"
3. 按照提示完成注册流程

### 2. 获取 API 密钥

登录账号后，获取您的 API 密钥：

1. 在个人账户页面，找到"API Keys"或"API 密钥"选项
2. 创建一个新的 API 密钥
3. 复制生成的密钥（通常以 `sk-` 开头）

### 3. 设置 API 密钥

您有两种方式设置 API 密钥：

#### 方式一：更新 .env 文件（推荐）

1. 在项目根目录找到 `.env` 文件
2. 更新以下配置项：
   ```
   OPENAI_API_KEY=你的DeepSeek密钥
   DEEPSEEK_API_BASE=https://api.deepseek.com/v1
   ```

#### 方式二：设置环境变量

在终端中运行：

```bash
export OPENAI_API_KEY=你的DeepSeek密钥
export DEEPSEEK_API_BASE=https://api.deepseek.com/v1
```

### 4. 验证 API 设置

运行测试脚本，验证 API 设置是否正确：

```bash
python src/ui/test_deepseek.py
```

如果设置正确，您将看到类似以下输出：

```
✅ API连接成功: API连接正常
可用模型列表:
  - deepseek-chat
  - deepseek-llm
  - ...
```

## 模拟模式

系统支持在API不可用时使用模拟模式，可以帮助您在无法连接API的情况下测试系统功能。

### 自动模拟模式

当API密钥未设置或API连接失败时，系统会自动切换到模拟模式，并生成模拟的AI分析结果。您会在日志中看到如下提示：

```
WARNING: DeepSeek客户端运行在模拟模式，将返回模拟响应
```

### 强制使用模拟模式

如果您想强制使用模拟模式，可以使用以下命令：

```bash
python src/ui/test_deepseek.py --mock
```

### 模拟模式的限制

模拟模式提供的是预设的回复，不具备真正的AI分析能力，主要用于以下场景：

1. 开发和测试系统功能
2. 展示系统的基本工作流程
3. 在API不可用时提供基本的应急方案

请注意，在生产环境中，建议使用真实的API以获取准确的分析结果。

## 常见问题

### API 密钥无效

如果您看到以下错误：

```
❌ API连接失败: API连接失败，状态码: 401, 错误信息: {'message': 'Authentication Fails, Your api key is invalid'}
```

请检查：
1. API 密钥是否正确复制（不包含额外空格）
2. 账户余额是否充足
3. API 密钥是否已激活

### 网络连接问题

如果您看到连接超时错误，可能是网络问题。请确保：
1. 您的网络连接正常
2. 如果使用代理，请确保代理设置正确

## 使用其他兼容的 API 服务

本系统使用 OpenAI 兼容接口，您也可以使用其他兼容 OpenAI 接口的 API 服务，如：

1. Azure OpenAI
2. Claude AI
3. 其他兼容 OpenAI 接口的模型服务

只需更改 `DEEPSEEK_API_BASE` 和 `OPENAI_API_KEY` 为相应服务的 API 地址和密钥即可。 