"""
重试策略模块
基于第一性原理的AI Agent任务规划系统

核心功能：
- 失败重试次数可配置化
- 支持多种重试策略（固定间隔、指数退避、线性退避）
- 可配置重试条件
- 防止无限重试
"""

import time
import random
from typing import Dict, Any, List, Optional, Callable, Type
from dataclasses import dataclass, field
from enum import Enum


class RetryStrategy(Enum):
    """重试策略"""
    FIXED = "fixed"              # 固定间隔
    EXPONENTIAL = "exponential"  # 指数退避
    LINEAR = "linear"            # 线性退避
    RANDOM = "random"            # 随机间隔


class RetryCondition(Enum):
    """重试条件"""
    ALL = "all"                  # 所有异常
    TIMEOUT = "timeout"          # 超时异常
    NETWORK = "network"          # 网络异常
    VALIDATION = "validation"    # 验证失败
    CUSTOM = "custom"            # 自定义


@dataclass
class RetryConfig:
    """重试配置"""
    max_retries: int = 3                    # 最大重试次数
    retry_strategy: RetryStrategy = RetryStrategy.EXPONENTIAL  # 重试策略
    base_delay: float = 1.0                 # 基础延迟（秒）
    max_delay: float = 60.0                 # 最大延迟（秒）
    retry_conditions: List[RetryCondition] = field(default_factory=lambda: [RetryCondition.ALL])  # 重试条件
    retryable_exceptions: List[Type[Exception]] = field(default_factory=list)  # 可重试异常类型
    on_retry_callback: Optional[Callable[[int, Exception, float], None]] = None  # 重试回调
    on_failure_callback: Optional[Callable[[Exception], None]] = None  # 失败回调
    jitter: bool = True                     # 是否添加随机抖动
    jitter_max: float = 0.5                 # 最大抖动幅度
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_retries": self.max_retries,
            "retry_strategy": self.retry_strategy.value,
            "base_delay": self.base_delay,
            "max_delay": self.max_delay,
            "retry_conditions": [c.value for c in self.retry_conditions],
            "jitter": self.jitter,
            "jitter_max": self.jitter_max
        }


class RetryPolicy:
    """
    重试策略执行器
    
    功能：
    - 执行带重试的函数
    - 支持多种重试策略
    - 可配置重试条件
    - 防止无限重试
    """
    
    def __init__(self, config: Optional[RetryConfig] = None):
        """
        初始化重试策略
        
        Args:
            config: 重试配置，None则使用默认配置
        """
        self.config = config or RetryConfig()
    
    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """
        执行带重试的函数
        
        Args:
            func: 要执行的函数
            *args: 函数参数
            **kwargs: 函数关键字参数
            
        Returns:
            函数返回值
            
        Raises:
            Exception: 重试耗尽后仍失败
        """
        last_exception = None
        
        for attempt in range(self.config.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                # 检查是否应该重试
                if not self._should_retry(e, attempt):
                    raise
                
                # 计算延迟
                delay = self._calculate_delay(attempt)
                
                # 调用重试回调
                if self.config.on_retry_callback:
                    try:
                        self.config.on_retry_callback(attempt + 1, e, delay)
                    except Exception:
                        pass
                
                # 延迟后重试
                if delay > 0:
                    time.sleep(delay)
        
        # 重试耗尽
        if self.config.on_failure_callback:
            try:
                self.config.on_failure_callback(last_exception)
            except Exception:
                pass
        
        raise last_exception
    
    def _should_retry(self, exception: Exception, attempt: int) -> bool:
        """
        检查是否应该重试
        
        Args:
            exception: 异常对象
            attempt: 当前尝试次数
            
        Returns:
            bool: 是否应该重试
        """
        # 检查是否达到最大重试次数
        if attempt >= self.config.max_retries:
            return False
        
        # 检查异常类型
        if self.config.retryable_exceptions:
            if not any(isinstance(exception, exc_type) for exc_type in self.config.retryable_exceptions):
                return False
        
        # 检查重试条件
        if RetryCondition.ALL in self.config.retry_conditions:
            return True
        
        # 检查超时异常
        if RetryCondition.TIMEOUT in self.config.retry_conditions:
            if isinstance(exception, TimeoutError):
                return True
        
        # 检查网络异常
        if RetryCondition.NETWORK in self.config.retry_conditions:
            network_exceptions = (ConnectionError, ConnectionRefusedError, ConnectionResetError)
            if isinstance(exception, network_exceptions):
                return True
        
        # 检查验证异常
        if RetryCondition.VALIDATION in self.config.retry_conditions:
            if "validation" in str(exception).lower() or "valid" in str(exception).lower():
                return True
        
        return False
    
    def _calculate_delay(self, attempt: int) -> float:
        """
        计算重试延迟
        
        Args:
            attempt: 当前尝试次数
            
        Returns:
            float: 延迟时间（秒）
        """
        delay = 0.0
        
        if self.config.retry_strategy == RetryStrategy.FIXED:
            # 固定间隔
            delay = self.config.base_delay
        
        elif self.config.retry_strategy == RetryStrategy.EXPONENTIAL:
            # 指数退避: base_delay * 2^attempt
            delay = self.config.base_delay * (2 ** attempt)
        
        elif self.config.retry_strategy == RetryStrategy.LINEAR:
            # 线性退避: base_delay * (attempt + 1)
            delay = self.config.base_delay * (attempt + 1)
        
        elif self.config.retry_strategy == RetryStrategy.RANDOM:
            # 随机间隔: base_delay 到 max_delay 之间
            delay = random.uniform(self.config.base_delay, self.config.max_delay)
        
        # 限制最大延迟
        delay = min(delay, self.config.max_delay)
        
        # 添加抖动
        if self.config.jitter:
            jitter = random.uniform(0, self.config.jitter_max)
            delay += jitter
        
        return delay
    
    def get_config(self) -> RetryConfig:
        """获取当前配置"""
        return self.config
    
    def update_config(self, **kwargs) -> None:
        """
        更新配置
        
        Args:
            **kwargs: 配置参数
        """
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)


# 便捷装饰器
def with_retry(
    max_retries: int = 3,
    retry_strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    retryable_exceptions: Optional[List[Type[Exception]]] = None
):
    """
    重试装饰器
    
    Args:
        max_retries: 最大重试次数
        retry_strategy: 重试策略
        base_delay: 基础延迟
        max_delay: 最大延迟
        retryable_exceptions: 可重试异常类型
    """
    def decorator(func):
        config = RetryConfig(
            max_retries=max_retries,
            retry_strategy=retry_strategy,
            base_delay=base_delay,
            max_delay=max_delay,
            retryable_exceptions=retryable_exceptions or []
        )
        policy = RetryPolicy(config)
        
        def wrapper(*args, **kwargs):
            return policy.execute(func, *args, **kwargs)
        
        return wrapper
    return decorator


# 使用示例
if __name__ == "__main__":
    print("=" * 60)
    print("重试策略模块 - 使用示例")
    print("=" * 60)
    
    # 1. 基本重试
    print("\n1. 基本重试示例:")
    
    attempt_count = 0
    
    def unstable_function():
        global attempt_count
        attempt_count += 1
        if attempt_count < 3:
            raise ConnectionError(f"模拟网络错误 (尝试 {attempt_count})")
        return "成功！"
    
    policy = RetryPolicy(RetryConfig(
        max_retries=3,
        retry_strategy=RetryStrategy.FIXED,
        base_delay=0.1
    ))
    
    try:
        result = policy.execute(unstable_function)
        print(f"   结果: {result}")
        print(f"   总尝试次数: {attempt_count}")
    except Exception as e:
        print(f"   最终失败: {e}")
    
    # 2. 指数退避
    print("\n2. 指数退避示例:")
    
    attempt_count = 0
    
    def failing_function():
        global attempt_count
        attempt_count += 1
        raise ValueError(f"模拟错误 (尝试 {attempt_count})")
    
    policy = RetryPolicy(RetryConfig(
        max_retries=3,
        retry_strategy=RetryStrategy.EXPONENTIAL,
        base_delay=0.1,
        max_delay=1.0
    ))
    
    try:
        result = policy.execute(failing_function)
    except Exception as e:
        print(f"   最终失败: {e}")
        print(f"   总尝试次数: {attempt_count}")
    
    # 3. 装饰器用法
    print("\n3. 装饰器用法示例:")
    
    @with_retry(max_retries=2, base_delay=0.1)
    def decorated_function():
        import random
        if random.random() < 0.5:
            raise RuntimeError("随机错误")
        return "装饰器成功！"
    
    try:
        result = decorated_function()
        print(f"   结果: {result}")
    except Exception as e:
        print(f"   失败: {e}")
    
    print("\n" + "=" * 60)
    print("重试策略模块 - 示例完成")
    print("=" * 60)
