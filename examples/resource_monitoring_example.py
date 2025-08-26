#!/usr/bin/env python3
"""
资源监控和优化使用示例
演示如何使用改进的MacAutoSymbolizer来避免"Too many open files"错误
"""

import os
import sys
import time
import logging
from pathlib import Path

# 添加项目路径到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from MacAutoSymbolizer.src.symbolizer import Symbolizer
from MacAutoSymbolizer.src.resource_config import ResourceConfig, resource_config
from MacAutoSymbolizer.src.utilities import Arch

# 配置日志
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_system_before_symbolization():
    """在符号化前检查系统资源"""
    logger.info("=== 系统资源检查 ===")
    
    # 检查并显示当前配置
    config = ResourceConfig()
    
    # 检查系统资源
    if not ResourceConfig.check_system_resources():
        logger.warning("系统资源使用率较高，建议降低并发设置")
        return False
    
    return True


def demonstrate_optimized_symbolization():
    """演示优化的符号化过程"""
    logger.info("=== 开始优化的符号化演示 ===")
    
    # 1. 检查系统资源
    if not check_system_before_symbolization():
        logger.warning("继续执行，但请注意监控资源使用")
    
    # 2. 创建符号化器实例（使用默认的优化配置）
    symbolizer = Symbolizer()
    
    # 3. 演示使用不同的并发设置
    crash_content = """
Application Specific Information:
Webex version 45.6.0.32215

Thread 0 Crashed:
0   com.apple.CoreFoundation    0x000000019a123456 CFStringGetLength + 0
1   Cisco Webex Meetings        0x0000000104567890 -[Something doWork] + 123
2   UIKitCore                   0x00000001a9876543 UIApplicationMain + 456
"""
    
    try:
        # 使用示例内容进行符号化
        logger.info("开始符号化处理...")
        start_time = time.time()
        
        # 这里会使用优化的并发控制
        result = symbolizer.symbolize(
            content_or_path=crash_content,
            version="45.6.0.32215",
            arch="arm64"
        )
        
        end_time = time.time()
        logger.info(f"符号化完成，耗时: {end_time - start_time:.2f} 秒")
        
        if result:
            logger.info(f"处理了 {len(result)} 个线程块")
        
    except Exception as e:
        logger.error(f"符号化过程出错: {e}")


def demonstrate_custom_resource_limits():
    """演示自定义资源限制"""
    logger.info("=== 演示自定义资源限制 ===")
    
    # 创建一个低并发设置的符号化器实例
    conservative_symbolizer = Symbolizer(max_concurrent_symbolize=5)
    logger.info("创建了保守的符号化器实例 (并发数=5)")
    
    # 创建一个高并发设置的符号化器实例（如果系统资源允许）
    if resource_config.max_concurrent_symbolize > 15:
        aggressive_symbolizer = Symbolizer(max_concurrent_symbolize=30)
        logger.info("创建了激进的符号化器实例 (并发数=30)")
    else:
        logger.info("系统资源限制，跳过高并发示例")


def monitor_resources_during_operation():
    """在操作过程中监控资源使用"""
    logger.info("=== 资源监控演示 ===")
    
    try:
        import psutil
        import resource
        
        # 获取当前进程
        process = psutil.Process()
        
        # 监控开始时的资源状态
        initial_files = len(process.open_files())
        soft_limit, hard_limit = resource.getrlimit(resource.RLIMIT_NOFILE)
        
        logger.info(f"监控开始:")
        logger.info(f"  当前打开文件数: {initial_files}")
        logger.info(f"  文件描述符限制: {soft_limit}")
        logger.info(f"  使用率: {(initial_files/soft_limit)*100:.1f}%")
        
        # 模拟一些操作
        logger.info("模拟符号化操作...")
        time.sleep(2)
        
        # 检查结束时的资源状态
        final_files = len(process.open_files())
        logger.info(f"监控结束:")
        logger.info(f"  当前打开文件数: {final_files}")
        logger.info(f"  文件数变化: {final_files - initial_files}")
        
    except ImportError:
        logger.warning("psutil未安装，无法进行详细的资源监控")
        logger.info("建议安装psutil: pip install psutil")


def show_environment_variables_usage():
    
    # 显示当前环境变量设置
    env_vars = [
        'MAC_SYMBOLIZER_MAX_CONCURRENT',
        'MAC_SYMBOLIZER_MAX_FILE_SEARCH', 
        'MAC_SYMBOLIZER_SUBPROCESS_TIMEOUT',
        'MAC_SYMBOLIZER_FILE_SEARCH_LIMIT'
    ]
    
    logger.info("当前环境变量设置:")
    for var in env_vars:
        value = os.getenv(var, "未设置")
        logger.info(f"  {var}: {value}")


def main():
    """主函数"""
    logger.info("开始MacAutoSymbolizer资源优化演示")
    
    try:
        # 1. 系统资源检查
        check_system_before_symbolization()
        
        # 2. 环境变量使用说明
        show_environment_variables_usage()
        
        # 3. 演示优化的符号化
        demonstrate_optimized_symbolization()
        
        # 4. 演示自定义资源限制
        demonstrate_custom_resource_limits()
        
        # 5. 资源监控
        monitor_resources_during_operation()
        
        logger.info("演示完成！")
        
    except KeyboardInterrupt:
        logger.info("用户中断了演示")
    except Exception as e:
        logger.error(f"演示过程中出错: {e}")
    
    # 最终资源检查
    logger.info("\n=== 最终资源状态检查 ===")
    ResourceConfig.check_system_resources()


if __name__ == "__main__":
    main()
