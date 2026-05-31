"""
第四层：分段校验收敛层 - 日志系统管理
基于第一性原理的AI Agent任务规划系统

核心功能：
- 统一日志级别管理
- 生产/开发环境切换
- 控制台/文件输出控制
- 性能标记和监控
"""

import logging
import logging.handlers
import os
import time
import sys
from typing import Optional, Dict, Any
from enum import Enum
from dataclasses import dataclass, field
from contextlib import contextmanager


class LogLevel(Enum):
    """日志级别"""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL
    OFF = 60  # 关闭所有日志


class Environment(Enum):
    """运行环境"""
    DEVELOPMENT = "development"  # 开发环境
    PRODUCTION = "production"    # 生产环境
    TESTING = "testing"          # 测试环境


@dataclass
class PerformanceMetric:
    """性能指标"""
    name: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    memory_usage: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class LoggerManager:
    """
    统一日志管理器
    
    功能：
    - 集中管理所有验证模块的日志
    - 支持运行时动态调整日志级别
    - 支持多种输出渠道
    - 性能标记和监控
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._loggers: Dict[str, logging.Logger] = {}
        self._current_level: LogLevel = LogLevel.INFO
        self._current_env: Environment = Environment.PRODUCTION
        self._file_handlers: Dict[str, logging.handlers.RotatingFileHandler] = {}
        self._console_handler: Optional[logging.StreamHandler] = None
        self._performance_metrics: Dict[str, PerformanceMetric] = {}
        self._initialized = True
        
        # 初始化根日志
        self._init_root_logger()
    
    def _init_root_logger(self):
        """初始化根日志"""
        root_logger = logging.getLogger()
        root_logger.setLevel(self._current_level.value)
        
        # 清除默认处理器
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
            
        # 设置格式化器
        self._formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 生产环境默认只输出WARNING及以上到控制台
        self._console_enabled = True
        self._add_console_handler()
        
    def _add_console_handler(self):
        """添加控制台处理器"""
        if self._console_handler:
            return
            
        self._console_handler = logging.StreamHandler(sys.stdout)
        self._console_handler.setFormatter(self._formatter)
        logging.getLogger().addHandler(self._console_handler)
        
    def _remove_console_handler(self):
        """移除控制台处理器"""
        if self._console_handler:
            logging.getLogger().removeHandler(self._console_handler)
            self._console_handler = None
    
    def _add_file_handler(self, name: str, filename: str, max_bytes: int = 10 * 1024 * 1024, backup_count: int = 5):
        """添加文件处理器（支持日志轮转）"""
        if name in self._file_handlers:
            return
            
        # 确保目录存在
        log_dir = os.path.dirname(filename)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
            
        file_handler = logging.handlers.RotatingFileHandler(
            filename,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(self._formatter)
        logging.getLogger().addHandler(file_handler)
        self._file_handlers[name] = file_handler
        
    def get_logger(self, name: str) -> logging.Logger:
        """
        获取日志记录器
        
        Args:
            name: 日志记录器名称
            
        Returns:
            logging.Logger: 日志记录器
        """
        if name not in self._loggers:
            logger = logging.getLogger(name)
            logger.setLevel(self._current_level.value)
            self._loggers[name] = logger
        return self._loggers[name]
    
    def set_level(self, level: LogLevel):
        """
        设置日志级别
        
        Args:
            level: 日志级别
        """
        self._current_level = level
        
        # 更新所有日志记录器的级别
        for logger in self._loggers.values():
            logger.setLevel(level.value)
        
        # 更新根日志记录器级别
        logging.getLogger().setLevel(level.value)
        
    def get_level(self) -> LogLevel:
        """获取当前日志级别"""
        return self._current_level
    
    def set_environment(self, env: Environment):
        """
        设置运行环境
        
        Args:
            env: 运行环境
        """
        self._current_env = env
        
        # 根据环境自动设置默认级别
        if env == Environment.PRODUCTION:
            self.set_level(LogLevel.WARNING)
        elif env == Environment.DEVELOPMENT:
            self.set_level(LogLevel.DEBUG)
        elif env == Environment.TESTING:
            self.set_level(LogLevel.INFO)
            
    def get_environment(self) -> Environment:
        """获取当前运行环境"""
        return self._current_env
    
    def enable_console_output(self, enable: bool):
        """
        启用/禁用控制台输出
        
        Args:
            enable: 是否启用
        """
        self._console_enabled = enable
        if enable:
            self._add_console_handler()
        else:
            self._remove_console_handler()
            
    def enable_file_output(self, name: str, filename: str, max_bytes: int = 10 * 1024 * 1024, backup_count: int = 5):
        """
        启用文件输出（支持日志轮转）
        
        Args:
            name: 输出标识名称
            filename: 输出文件路径
            max_bytes: 单个日志文件最大大小
            backup_count: 保留备份数量
        """
        self._add_file_handler(name, filename, max_bytes, backup_count)
        
    def disable_file_output(self, name: str):
        """
        禁用文件输出
        
        Args:
            name: 输出标识名称
        """
        if name in self._file_handlers:
            handler = self._file_handlers[name]
            logging.getLogger().removeHandler(handler)
            handler.close()
            del self._file_handlers[name]
    
    @contextmanager
    def performance_trace(self, name: str, **metadata):
        """
        性能追踪上下文管理器
        
        Args:
            name: 追踪名称
            **metadata: 附加元数据
        """
        metric = PerformanceMetric(
            name=name,
            start_time=time.time(),
            metadata=metadata
        )
        self._performance_metrics[name] = metric
        
        try:
            yield
        finally:
            metric.end_time = time.time()
            metric.duration = metric.end_time - metric.start_time
            
            # 记录性能日志
            logger = self.get_logger('performance')
            logger.info(f"[PERFORMANCE] {name} - Duration: {metric.duration:.4f}s")
            if metadata:
                logger.debug(f"[PERFORMANCE] {name} - Metadata: {metadata}")
    
    def start_performance_trace(self, name: str, **metadata) -> str:
        """
        开始性能追踪
        
        Args:
            name: 追踪名称
            **metadata: 附加元数据
            
        Returns:
            str: 追踪ID
        """
        trace_id = f"{name}_{int(time.time())}"
        metric = PerformanceMetric(
            name=name,
            start_time=time.time(),
            metadata=metadata
        )
        self._performance_metrics[trace_id] = metric
        
        logger = self.get_logger('performance')
        logger.debug(f"[PERFORMANCE_START] {name}")
        
        return trace_id
        
    def end_performance_trace(self, trace_id: str):
        """
        结束性能追踪
        
        Args:
            trace_id: 追踪ID
        """
        if trace_id not in self._performance_metrics:
            return
            
        metric = self._performance_metrics[trace_id]
        metric.end_time = time.time()
        metric.duration = metric.end_time - metric.start_time
        
        logger = self.get_logger('performance')
        logger.info(f"[PERFORMANCE_END] {metric.name} - Duration: {metric.duration:.4f}s")
        
        return metric
    
    def get_performance_metrics(self) -> Dict[str, PerformanceMetric]:
        """获取所有性能指标"""
        return self._performance_metrics.copy()
    
    def clear_performance_metrics(self):
        """清除所有性能指标"""
        self._performance_metrics.clear()


# 便捷函数
def get_logger(name: str) -> logging.Logger:
    """
    便捷函数：获取日志记录器
    
    Args:
        name: 日志记录器名称
        
    Returns:
        logging.Logger: 日志记录器
    """
    return LoggerManager().get_logger(name)


def set_log_level(level: LogLevel):
    """
    便捷函数：设置日志级别
    
    Args:
        level: 日志级别
    """
    LoggerManager().set_level(level)


def set_environment(env: Environment):
    """
    便捷函数：设置运行环境
    
    Args:
        env: 运行环境
    """
    LoggerManager().set_environment(env)


@contextmanager
def performance_trace(name: str, **metadata):
    """
    便捷函数：性能追踪上下文管理器
    
    Args:
        name: 追踪名称
        **metadata: 附加元数据
    """
    with LoggerManager().performance_trace(name, **metadata):
        yield


# 使用示例
if __name__ == "__main__":
    print("=" * 60)
    print("日志系统管理 - 使用示例")
    print("=" * 60)
    
    # 1. 获取日志管理器
    manager = LoggerManager()
    
    # 2. 设置开发环境（DEBUG级别）
    print("\n1. 设置开发环境:")
    manager.set_environment(Environment.DEVELOPMENT)
    print(f"   环境: {manager.get_environment().value}")
    print(f"   日志级别: {manager.get_level().name}")
    
    # 3. 获取并使用日志记录器
    print("\n2. 使用日志记录器:")
    logger = get_logger('test_module')
    logger.debug("这是调试信息")
    logger.info("这是普通信息")
    logger.warning("这是警告信息")
    logger.error("这是错误信息")
    
    # 4. 测试性能追踪
    print("\n3. 性能追踪测试:")
    with performance_trace('example_operation', category='test'):
        time.sleep(0.1)
        print("   操作完成")
    
    # 5. 切换到生产环境
    print("\n4. 切换到生产环境:")
    manager.set_environment(Environment.PRODUCTION)
    print(f"   环境: {manager.get_environment().value}")
    print(f"   日志级别: {manager.get_level().name}")
    
    # 生产环境下debug日志不会输出
    logger.debug("这个debug信息不会输出")
    logger.warning("生产环境的警告信息")
    
    # 6. 启用文件输出
    print("\n5. 启用文件输出:")
    manager.enable_file_output('app_logs', '/tmp/app.log', max_bytes=1024*1024, backup_count=3)
    logger.info("这条信息会同时输出到控制台和文件")
    print("   日志文件已启用")
    
    # 7. 关闭控制台输出（仅文件）
    print("\n6. 关闭控制台输出:")
    manager.enable_console_output(False)
    logger.info("这条信息只会输出到文件")
    manager.enable_console_output(True)
    
    # 8. 清理并显示性能指标
    print("\n7. 性能指标:")
    metrics = manager.get_performance_metrics()
    for name, metric in metrics.items():
        if metric.duration:
            print(f"   {metric.name}: {metric.duration:.4f}s")
    
    print("\n" + "=" * 60)
    print("日志系统管理 - 示例完成")
    print("=" * 60)
