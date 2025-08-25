#!/usr/bin/env python3
"""
MacCrash Auto Symbolizer Web 启动脚本
直接使用uvicorn命令行启动应用以避免路径问题
"""

import os
import sys
import subprocess

def main():
    # 获取项目路径
    webPage_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(webPage_dir)
    
    print("=== MacCrash Auto Symbolizer Web Server ===")
    print(f"webPage目录: {webPage_dir}")
    print(f"项目根目录: {project_root}")
    
    # 检查必要的文件和目录
    app_file = os.path.join(webPage_dir, "app.py")
    static_dir = os.path.join(webPage_dir, "static")
    templates_dir = os.path.join(webPage_dir, "templates")
    
    print(f"检查应用文件: {app_file} - {'✓' if os.path.exists(app_file) else '✗'}")
    print(f"检查静态文件目录: {static_dir} - {'✓' if os.path.exists(static_dir) else '✗'}")
    print(f"检查模板目录: {templates_dir} - {'✓' if os.path.exists(templates_dir) else '✗'}")
    
    # 设置环境变量
    env = os.environ.copy()
    env['PYTHONPATH'] = project_root
    
    # 切换到项目根目录
    os.chdir(project_root)
    print(f"切换工作目录到: {os.getcwd()}")
    
    # 使用uvicorn命令行启动
    cmd = [
        sys.executable, "-m", "uvicorn",
        "webPage.app:app",
        "--host", "0.0.0.0",
        "--port", "5001",
        "--reload", 
        "--reload-dir", webPage_dir
    ]
    
    print("启动命令:", " ".join(cmd))
    print("服务器将在 http://localhost:8080 启动")
    print("按 Ctrl+C 停止服务器")
    print("=" * 50)
    
    try:
        subprocess.run(cmd, env=env, check=True)
    except KeyboardInterrupt:
        print("\n服务器已停止")
    except subprocess.CalledProcessError as e:
        print(f"启动失败: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
