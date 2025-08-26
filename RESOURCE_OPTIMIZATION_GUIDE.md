# MacAutoSymbolizer 资源优化指南

## 问题描述

当运行符号化任务时，您可能遇到 `[Errno 24] Too many open files` 错误。这是因为程序同时打开了太多文件描述符，超过了系统限制。

## 🔧 已实现的修复

### 1. 事件循环资源管理
- **问题**: `scanner.py` 中的事件循环没有正确关闭
- **修复**: 添加了 `try-finally` 块确保事件循环正确关闭

### 2. 并发控制
- **问题**: 无限制的并发任务创建大量文件句柄
- **修复**: 添加信号量控制最大并发数量

### 3. 子进程超时管理
- **问题**: 子进程可能挂起导致资源泄漏
- **修复**: 添加超时控制和强制清理机制

### 4. 文件搜索优化
- **问题**: 文件搜索可能同时打开大量文件
- **修复**: 限制搜索结果数量，使用生成器减少内存使用

### 5. 智能资源配置
- **新功能**: 自动检测系统限制并调整并发参数

## 🚀 使用方法

### 基本使用（推荐）
```python
from MacAutoSymbolizer.src.symbolizer import Symbolizer

# 使用默认的优化配置
symbolizer = Symbolizer()
result = symbolizer.symbolize(crash_content, version, arch)
```

### 自定义并发限制
```python
# 保守设置（低资源系统）
symbolizer = Symbolizer(max_concurrent_symbolize=5)

# 激进设置（高性能系统）
symbolizer = Symbolizer(max_concurrent_symbolize=30)
```

### 环境变量配置
```bash
# 设置最大并发符号化任务数
export MAC_SYMBOLIZER_MAX_CONCURRENT=15

# 设置最大并发文件搜索数
export MAC_SYMBOLIZER_MAX_FILE_SEARCH=8

# 设置子进程超时时间（秒）
export MAC_SYMBOLIZER_SUBPROCESS_TIMEOUT=60

# 设置文件搜索结果限制
export MAC_SYMBOLIZER_FILE_SEARCH_LIMIT=5
```

## 🔍 资源监控

### 检查系统资源
```python
from MacAutoSymbolizer.src.resource_config import ResourceConfig

# 检查当前资源使用情况
ResourceConfig.check_system_resources()

# 查看配置摘要
config = ResourceConfig()
print(config.get_config_summary())
```

### 运行监控示例
```bash
cd examples
python resource_monitoring_example.py
```

## ⚙️ 系统优化建议

### 1. 增加文件描述符限制
```bash
# 临时增加限制
ulimit -n 4096

# 永久设置（macOS）
echo "ulimit -n 4096" >> ~/.bashrc
echo "ulimit -n 4096" >> ~/.zshrc
```

### 2. 监控资源使用
```bash
# 安装监控工具
pip install psutil

# 检查当前打开的文件数
lsof -p $$ | wc -l
```

### 3. 根据系统配置调整
- **低配置系统**: 设置 `MAC_SYMBOLIZER_MAX_CONCURRENT=5`
- **中等配置系统**: 设置 `MAC_SYMBOLIZER_MAX_CONCURRENT=15`
- **高配置系统**: 设置 `MAC_SYMBOLIZER_MAX_CONCURRENT=25`

## 🐛 故障排除

### 问题1: 仍然出现 "Too many open files"
**解决方案**:
1. 降低并发数: `export MAC_SYMBOLIZER_MAX_CONCURRENT=5`
2. 检查系统限制: `ulimit -n`
3. 运行资源监控脚本

### 问题2: 符号化速度变慢
**解决方案**:
1. 逐步增加并发数测试
2. 监控系统资源使用情况
3. 平衡速度和稳定性

### 问题3: 子进程超时
**解决方案**:
1. 增加超时时间: `export MAC_SYMBOLIZER_SUBPROCESS_TIMEOUT=120`
2. 检查网络连接和符号文件可用性

## 📝 最佳实践

1. **启动前检查**: 总是在开始大批量符号化前检查系统资源
2. **渐进调优**: 从保守设置开始，逐步增加并发数
3. **监控运行**: 在长时间运行时定期检查资源使用
4. **环境隔离**: 在生产环境中使用环境变量配置
5. **日志监控**: 关注日志中的资源警告信息

## 🔗 相关文件

- `MacAutoSymbolizer/src/resource_config.py` - 资源配置管理
- `MacAutoSymbolizer/src/symbolizer.py` - 主要符号化逻辑  
- `MacAutoSymbolizer/src/scanner.py` - 崩溃日志扫描
- `MacAutoSymbolizer/src/subprocess_cmd.py` - 子进程管理
- `examples/resource_monitoring_example.py` - 使用示例

通过这些优化，您应该能够避免 "Too many open files" 错误，并获得更稳定的符号化性能。
