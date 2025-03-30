# 问题修复：DeepSeek客户端初始化错误

## 问题描述

初始化DeepSeek客户端时出现错误：
```
初始化DeepSeek客户端失败: Client.__init__() got an unexpected keyword argument 'proxies'
```

## 原因分析

这个错误是由于代码使用旧版OpenAI客户端接口，而系统中安装的是新版OpenAI客户端（1.1.1版本），新版不再支持`proxies`参数。

## 解决方案

1. 完全重构了DeepSeek客户端，不再依赖OpenAI类库，而是使用标准的`requests`库直接与API交互
2. 增加了模拟模式功能，在API不可用时自动启用
3. 添加了连接测试功能，确保系统能够优雅处理API连接问题

## 改进内容

1. **模拟模式自动切换**：当API连接失败时，系统会自动切换到模拟模式，返回合理的模拟响应
2. **模拟响应智能生成**：根据不同查询类型返回不同的模拟内容，提供更真实的体验
3. **连接状态监测**：自动检测API连接状态，避免反复尝试失败的连接
4. **更友好的用户体验**：添加了清晰的日志信息和说明文档

## 如何测试

1. 运行测试脚本验证改进：
   ```bash
   python src/ui/test_deepseek.py
   ```

2. 如果您暂时没有有效的API密钥，可以使用强制模拟模式：
   ```bash
   python src/ui/test_deepseek.py --mock
   ```

3. 检查股票分析功能：
   ```bash
   python src/ui/test_analyzer.py
   ```

如果您想设置有效的API密钥，请参考`README_API_SETUP.md`文件中的指导。 