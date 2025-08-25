# MacCrash Auto Symbolizer Web Interface

基于FastAPI构建的MacCrash Auto Symbolizer Web界面，提供用户友好的崩溃日志符号化服务。

## 功能特性

- **现代化Web界面**: 响应式设计，支持移动端和桌面端
- **多种输入方式**: 支持文本输入和文件上传两种方式
- **实时日志显示**: 符号化过程中的实时日志输出
- **进度指示**: 直观的处理进度显示
- **结果管理**: 支持复制和下载处理结果
- **文件拖拽**: 支持拖拽上传崩溃文件

## 页面组件

### 输入参数
1. **版本号 (version)** - 必填项，例如: 45.8.0.32875
2. **架构 (arch)** - 必选项，支持 ARM64 和 x86_64
3. **NDI模式 (isNDI)** - 可选项，启用备份模式
4. **输入方式** - 二选一：
   - 文本输入：直接粘贴Stack堆栈内容
   - 文件上传：上传.ips、.diag、.txt等格式的崩溃文件

### 输出结果
- **符号化结果**: 处理后的符号化堆栈跟踪
- **执行日志**: 详细的处理过程日志
- **操作功能**: 复制到剪贴板、下载结果文件

## 技术栈

- **后端**: FastAPI + Python
- **前端**: HTML5 + CSS3 + JavaScript (Vanilla)
- **样式**: 自定义CSS，现代化UI设计
- **图标**: Font Awesome 6.0

## 安装和运行

### 1. 安装依赖

```bash
cd webPage
pip install -r requirements.txt
```

### 2. 启动服务

```bash
python app.py
```

或使用uvicorn:

```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

### 3. 访问界面

打开浏览器访问: http://localhost:8000

## API接口

### POST /symbolize
符号化处理接口

**参数:**
- `version`: 版本号 (必填)
- `arch`: 架构 (必填，arm64或x86)
- `isNDI`: NDI模式 (可选，默认False)
- `stack_content`: Stack内容 (可选，与crash_file二选一)
- `crash_file`: 崩溃文件 (可选，与stack_content二选一)

**响应:**
```json
{
    "success": true,
    "output": "符号化结果...",
    "error": null,
    "logs": ["日志信息..."]
}
```

### GET /logs
获取当前日志

**响应:**
```json
{
    "logs": ["日志信息..."]
}
```

### POST /clear-logs
清空日志

## 项目结构

```
webPage/
├── app.py                 # FastAPI主应用
├── requirements.txt       # Python依赖
├── README.md             # 项目说明
├── templates/            # HTML模板
│   └── index.html       # 主页面
└── static/              # 静态资源
    ├── css/
    │   └── style.css    # 样式文件
    └── js/
        └── app.js       # JavaScript逻辑
```

## 使用说明

1. **输入版本号**: 在版本号输入框中输入Webex的版本号
2. **选择架构**: 从下拉菜单中选择对应的处理器架构
3. **选择输入方式**:
   - **文本输入**: 直接粘贴崩溃日志的堆栈信息
   - **文件上传**: 点击或拖拽上传崩溃文件
4. **开始处理**: 点击"开始符号化"按钮
5. **查看结果**: 在输出区域查看符号化结果和执行日志
6. **导出结果**: 使用复制或下载功能保存结果

## 注意事项

- 确保已正确安装MacAutoSymbolizer模块
- 版本号格式必须为: x.x.x.x (例如: 45.8.0.32875)
- 文件上传和文本输入只能选择其中一种方式
- 符号化过程可能需要一些时间，请耐心等待
- 如果出现错误，请查看执行日志了解详细信息

## 故障排除

### 常见问题

1. **模块导入错误**: 确保MacAutoSymbolizer已正确安装并且Python路径配置正确
2. **符号文件下载失败**: 检查网络连接和Maven认证配置
3. **版本号不匹配**: 确保输入的版本号与实际崩溃日志匹配
4. **架构选择错误**: 根据崩溃设备的处理器类型选择正确的架构

### 日志分析

- 查看"执行日志"选项卡了解详细的处理过程
- 错误信息会显示在日志和结果区域中
- 网络相关问题通常在日志中有详细描述
