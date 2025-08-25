import logging
import os
import tempfile
import asyncio
import concurrent.futures
from datetime import datetime
from typing import Optional, List
from pathlib import Path

from fastapi import FastAPI, Request, Form, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

# 导入MacAutoSymbolizer
import sys
# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 设置工作目录到项目根目录，确保配置文件等能正确找到
original_cwd = os.getcwd()
os.chdir(project_root)

from MacAutoSymbolizer import Symbolizer

app = FastAPI(title="MacCrash Auto Symbolizer Web", version="1.0.0")

# 静态文件和模板设置
webPage_dir = os.path.join(project_root, "webPage")
app.mount("/static", StaticFiles(directory=os.path.join(webPage_dir, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(webPage_dir, "templates"))

# 全局变量存储日志输出
log_output: List[str] = []

class LogOutput(BaseModel):
    logs: List[str]

class SymbolizeResponse(BaseModel):
    success: bool
    output: Optional[str] = None
    error: Optional[str] = None
    logs: List[str]

class CustomLogHandler(logging.Handler):
    """自定义日志处理器，将日志输出到全局变量"""
    def emit(self, record):
        global log_output
        log_msg = self.format(record)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_msg = f"[{timestamp}] {record.levelname}: {log_msg}"
        log_output.append(formatted_msg)
        print(formatted_msg)  # 同时输出到控制台

# 配置日志
def setup_logging():
    """设置日志配置"""
    # 创建自定义处理器
    custom_handler = CustomLogHandler()
    custom_handler.setLevel(logging.DEBUG)
    
    # 设置日志格式
    formatter = logging.Formatter('%(name)s - %(message)s')
    custom_handler.setFormatter(formatter)
    
    # 获取所有相关的logger并添加处理器
    loggers_to_configure = [
        'MacAutoSymbolizer',
        'MacAutoSymbolizer.src.symbolizer',
        'MacAutoSymbolizer.src.scanner',
        'MacAutoSymbolizer.src.advanced_downloader',
        '__main__'
    ]
    
    for logger_name in loggers_to_configure:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)
        logger.addHandler(custom_handler)
        # 防止重复日志
        logger.propagate = False

# 初始化日志
setup_logging()

# 创建线程池执行器
executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)

def run_symbolize_in_thread(content_or_path: str, version: str, arch: str, isBackup: bool = False):
    """在线程中运行符号化，避免事件循环冲突"""
    try:
        # 在新线程中创建新的事件循环
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            symbolizer = Symbolizer()
            result = symbolizer.symbolize(
                content_or_path=content_or_path,
                version=version,
                arch=arch,
                isBackup=isBackup
            )
            return result
        finally:
            # 清理事件循环
            loop.close()
            
    except Exception as e:
        raise e

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """主页面"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/symbolize", response_model=SymbolizeResponse)
async def symbolize_crash(
    version: str = Form(..., description="版本号，必填"),
    arch: str = Form(..., description="架构，arm64或x86"),
    isNDI: bool = Form(False, description="是否启用NDI"),
    stack_content: Optional[str] = Form(None, description="Stack内容"),
    crash_file: Optional[UploadFile] = File(None, description="崩溃文件上传")
):
    """处理符号化请求"""
    global log_output
    
    # 清空之前的日志
    log_output.clear()
    
    try:
        # 验证输入参数
        if not version.strip():
            raise HTTPException(status_code=400, detail="版本号不能为空")
        
        if arch not in ["arm64", "x86"]:
            raise HTTPException(status_code=400, detail="架构必须是 arm64 或 x86")
        
        # 检查是否提供了stack内容或文件
        if not stack_content and not crash_file:
            raise HTTPException(status_code=400, detail="必须提供stack内容或上传文件")
        
        if stack_content and crash_file:
            raise HTTPException(status_code=400, detail="不能同时提供stack内容和文件")
        
        # 添加初始日志
        log_output.append(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] INFO: 开始符号化处理...")
        log_output.append(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] INFO: 版本: {version}")
        log_output.append(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] INFO: 架构: {arch}")
        log_output.append(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] INFO: NDI模式: {isNDI}")
        
        # 准备输入内容
        content_or_path = None
        temp_file_path = None
        
        if stack_content:
            # 使用直接提供的stack内容
            content_or_path = stack_content.strip()
            log_output.append(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] INFO: 使用直接输入的stack内容")
        else:
            # 处理上传的文件
            if crash_file.filename:
                log_output.append(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] INFO: 处理上传文件: {crash_file.filename}")
                
                # 创建临时文件保存上传内容
                temp_dir = tempfile.gettempdir()
                temp_file_path = os.path.join(temp_dir, f"crash_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{crash_file.filename}")
                
                # 读取并保存文件内容
                file_content = await crash_file.read()
                with open(temp_file_path, 'wb') as f:
                    f.write(file_content)
                
                content_or_path = temp_file_path
                log_output.append(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] INFO: 文件已保存到临时位置: {temp_file_path}")
        
        # 执行符号化（在线程池中运行避免事件循环冲突）
        log_output.append(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] INFO: 开始符号化处理...")
        
        # 调整架构格式
        arch_format = "x86_64" if arch == "x86" else arch
        
        # 在线程池中运行符号化，避免事件循环冲突
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            executor,
            run_symbolize_in_thread,
            content_or_path,
            version,
            arch_format,
            isNDI
        )
        
        output_lines = []
        for block in result:
            output_lines.append("-" * 100)
            for line in block:
                output_lines.append(str(line))

        output_result = "\n".join(output_lines)
        
        log_output.append(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] INFO: 符号化处理完成!")
        
        # 清理临时文件
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
                log_output.append(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] INFO: 临时文件已清理")
            except Exception as e:
                log_output.append(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] WARNING: 临时文件清理失败: {str(e)}")
        
        return SymbolizeResponse(
            success=True,
            output=output_result,
            logs=log_output.copy()
        )
        
    except Exception as e:
        error_msg = str(e)
        log_output.append(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ERROR: {error_msg}")
        
        # 清理临时文件
        if 'temp_file_path' in locals() and temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except:
                pass
        
        return SymbolizeResponse(
            success=False,
            error=error_msg,
            logs=log_output.copy()
        )

@app.get("/logs", response_model=LogOutput)
async def get_logs():
    """获取当前日志输出"""
    global log_output
    return LogOutput(logs=log_output.copy())

@app.post("/clear-logs")
async def clear_logs():
    """清空日志"""
    global log_output
    log_output.clear()
    return {"message": "日志已清空"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
