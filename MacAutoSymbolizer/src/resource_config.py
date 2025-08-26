"""
资源管理配置
用于控制符号化过程中的资源使用，防止"Too many open files"错误
"""

import os
import resource
import logging

logger = logging.getLogger(__name__)


class ResourceConfig:
    """资源管理配置类"""
    
    def __init__(self):
        # 默认配置
        self.max_concurrent_symbolize = 20      # 最大并发符号化任务数
        self.max_concurrent_file_search = 10    # 最大并发文件搜索数
        self.subprocess_timeout = 30            # 子进程超时时间（秒）
        self.file_search_limit = 5              # 文件搜索结果限制
        
        # 从环境变量读取配置
        self._load_from_env()
        
        # 自动检测并调整配置
        self._auto_adjust_limits()
    
    def _load_from_env(self):
        """从环境变量加载配置"""
        self.max_concurrent_symbolize = int(os.getenv('MAC_SYMBOLIZER_MAX_CONCURRENT', self.max_concurrent_symbolize))
        self.max_concurrent_file_search = int(os.getenv('MAC_SYMBOLIZER_MAX_FILE_SEARCH', self.max_concurrent_file_search))
        self.subprocess_timeout = int(os.getenv('MAC_SYMBOLIZER_SUBPROCESS_TIMEOUT', self.subprocess_timeout))
        self.file_search_limit = int(os.getenv('MAC_SYMBOLIZER_FILE_SEARCH_LIMIT', self.file_search_limit))
    
    def _auto_adjust_limits(self):
        """根据系统资源自动调整限制"""
        try:
            # 获取系统文件描述符限制
            soft_limit, hard_limit = resource.getrlimit(resource.RLIMIT_NOFILE)
            
            logger.info(f"系统文件描述符限制: soft={soft_limit}, hard={hard_limit}")
            
            # 如果软限制较低，自动降低并发数
            if soft_limit < 1024:
                logger.warning(f"系统文件描述符限制较低 ({soft_limit})，自动降低并发数")
                self.max_concurrent_symbolize = min(self.max_concurrent_symbolize, 10)
                self.max_concurrent_file_search = min(self.max_concurrent_file_search, 5)
            elif soft_limit < 4096:
                logger.info(f"系统文件描述符限制中等 ({soft_limit})，使用适中的并发数")
                self.max_concurrent_symbolize = min(self.max_concurrent_symbolize, 15)
                self.max_concurrent_file_search = min(self.max_concurrent_file_search, 8)
            
            # 尝试增加软限制（在权限允许的情况下）
            if soft_limit < hard_limit and soft_limit < 4096:
                try:
                    new_soft_limit = min(hard_limit, 4096)
                    resource.setrlimit(resource.RLIMIT_NOFILE, (new_soft_limit, hard_limit))
                    logger.info(f"已将文件描述符软限制从 {soft_limit} 增加到 {new_soft_limit}")
                except (ValueError, OSError) as e:
                    logger.warning(f"无法增加文件描述符限制: {e}")
            
        except Exception as e:
            logger.warning(f"获取系统资源信息失败: {e}")
    
    def get_config_summary(self) -> str:
        """获取配置摘要"""
        return f"""
当前资源配置:
- 最大并发符号化任务: {self.max_concurrent_symbolize}
- 最大并发文件搜索: {self.max_concurrent_file_search}
- 子进程超时时间: {self.subprocess_timeout}秒
- 文件搜索结果限制: {self.file_search_limit}

环境变量配置:
- MAC_SYMBOLIZER_MAX_CONCURRENT: 最大并发符号化任务数
- MAC_SYMBOLIZER_MAX_FILE_SEARCH: 最大并发文件搜索数  
- MAC_SYMBOLIZER_SUBPROCESS_TIMEOUT: 子进程超时时间
- MAC_SYMBOLIZER_FILE_SEARCH_LIMIT: 文件搜索结果限制
"""

    @staticmethod
    def check_system_resources():
        """检查系统资源状态"""
        try:
            # 检查文件描述符使用情况
            import psutil
            process = psutil.Process()
            open_files = len(process.open_files())
            
            soft_limit, hard_limit = resource.getrlimit(resource.RLIMIT_NOFILE)
            usage_percent = (open_files / soft_limit) * 100
            
            logger.info(f"当前打开文件数: {open_files}/{soft_limit} ({usage_percent:.1f}%)")
            
            if usage_percent > 80:
                logger.warning(f"文件描述符使用率过高: {usage_percent:.1f}%")
                return False
            
            return True
        
        except ImportError:
            logger.warning("psutil未安装，无法检查系统资源")
            return True
        except Exception as e:
            logger.warning(f"检查系统资源失败: {e}")
            return True


# 全局配置实例
resource_config = ResourceConfig()
