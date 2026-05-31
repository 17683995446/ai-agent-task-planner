"""
第四层：分段校验收敛层 - 统一全局异常捕获与分发机制
基于第一性原理的AI Agent任务规划系统

核心功能：
- 全局异常捕获和分类
- 异常分发和处理
- 异常日志记录
- 错误恢复策略
"""

import traceback
import threading
from typing import Optional, Dict, Any, List, Callable, Type, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from functools import wraps

from .logger_manager import get_logger, LogLevel
from .trace_logger import get_trace_logger, LayerType, OperationType, TraceLevel
from .progress_monitor import get_progress_monitor, TaskStatus

logger = get_logger('exception_handler')


class ErrorCode(Enum):
    """错误码枚举"""
    # 通用错误
    UNKNOWN_ERROR = "E001"
    INVALID_INPUT = "E002"
    OPERATION_FAILED = "E003"
    
    # 建模层错误
    MODELING_ERROR = "E101"
    TARGET_EXTRACTION_FAILED = "E102"
    CONDITION_EXTRACTION_FAILED = "E103"
    BOUNDARY_EXTRACTION_FAILED = "E104"
    END_RULE_EXTRACTION_FAILED = "E105"
    TASK_VALIDATION_FAILED = "E106"
    
    # 拓扑层错误
    TOPOLOGY_ERROR = "E201"
    DECOMPOSITION_FAILED = "E202"
    DEPENDENCY_CALCULATION_FAILED = "E203"
    DAG_GENERATION_FAILED = "E204"
    CIRCULAR_DEPENDENCY = "E205"
    INVALID_TOPOLOGY = "E206"
    
    # 原子层错误
    ATOMIC_ERROR = "E301"
    ACTION_SPLIT_FAILED = "E302"
    ATOMIC_VALIDATION_FAILED = "E303"
    QUEUE_GENERATION_FAILED = "E304"
    
    # 验证层错误
    VALIDATION_ERROR = "E401"
    SEGMENT_VALIDATION_FAILED = "E402"
    TARGET_ALIGNMENT_FAILED = "E403"
    PERFORMANCE_MONITORING_ERROR = "E404"
    
    # 系统错误
    SYSTEM_ERROR = "E901"
    CONFIGURATION_ERROR = "E902"
    RESOURCE_ERROR = "E903"
    TIMEOUT_ERROR = "E904"


class ErrorSeverity(Enum):
    """错误严重程度"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    FATAL = "fatal"


@dataclass
class ExceptionInfo:
    """异常信息"""
    error_code: ErrorCode
    severity: ErrorSeverity
    message: str
    layer: Optional[LayerType] = None
    task_id: Optional[str] = None
    timestamp: float = field(default_factory=datetime.now().timestamp)
    exception_type: Optional[str] = None
    stack_trace: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    recoverable: bool = True
    retry_count: int = 0
    max_retries: int = 3
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "error_code": self.error_code.value,
            "severity": self.severity.value,
            "message": self.message,
            "layer": self.layer.value if self.layer else None,
            "task_id": self.task_id,
            "timestamp": self.timestamp,
            "datetime": datetime.fromtimestamp(self.timestamp).isoformat(),
            "exception_type": self.exception_type,
            "stack_trace": self.stack_trace,
            "details": self.details,
            "recoverable": self.recoverable,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries
        }


class TaskPlanningException(Exception):
    """任务规划异常基类"""
    
    def __init__(
        self,
        error_code: ErrorCode,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        layer: Optional[LayerType] = None,
        task_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        recoverable: bool = True
    ):
        self.error_code = error_code
        self.severity = severity
        self.layer = layer
        self.task_id = task_id
        self.details = details or {}
        self.recoverable = recoverable
        super().__init__(message)
    
    def to_exception_info(self) -> ExceptionInfo:
        return ExceptionInfo(
            error_code=self.error_code,
            severity=self.severity,
            message=str(self),
            layer=self.layer,
            task_id=self.task_id,
            details=self.details,
            recoverable=self.recoverable
        )


class ModelingException(TaskPlanningException):
    """建模层异常"""
    
    def __init__(
        self,
        error_code: ErrorCode,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        task_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        recoverable: bool = True
    ):
        super().__init__(
            error_code=error_code,
            message=message,
            severity=severity,
            layer=LayerType.MODELING,
            task_id=task_id,
            details=details,
            recoverable=recoverable
        )


class TopologyException(TaskPlanningException):
    """拓扑层异常"""
    
    def __init__(
        self,
        error_code: ErrorCode,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        task_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        recoverable: bool = True
    ):
        super().__init__(
            error_code=error_code,
            message=message,
            severity=severity,
            layer=LayerType.TOPOLOGY,
            task_id=task_id,
            details=details,
            recoverable=recoverable
        )


class AtomicException(TaskPlanningException):
    """原子层异常"""
    
    def __init__(
        self,
        error_code: ErrorCode,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        task_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        recoverable: bool = True
    ):
        super().__init__(
            error_code=error_code,
            message=message,
            severity=severity,
            layer=LayerType.ATOMIC,
            task_id=task_id,
            details=details,
            recoverable=recoverable
        )


class ValidationException(TaskPlanningException):
    """验证层异常"""
    
    def __init__(
        self,
        error_code: ErrorCode,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        task_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        recoverable: bool = True
    ):
        super().__init__(
            error_code=error_code,
            message=message,
            severity=severity,
            layer=LayerType.VALIDATION,
            task_id=task_id,
            details=details,
            recoverable=recoverable
        )


class ExceptionHandler:
    """
    全局异常处理器
    
    功能：
    - 统一异常捕获和分类
    - 异常分发和处理
    - 异常日志记录
    - 错误恢复策略
    - 回调通知机制
    """
    
    def __init__(self):
        """初始化异常处理器"""
        self._exception_history: List[ExceptionInfo] = []
        self._handlers: Dict[Type[Exception], List[Callable[[ExceptionInfo], bool]]] = {}
        self._listeners: List[Callable[[ExceptionInfo], None]] = []
        self._lock = threading.RLock()
        self._trace_logger = get_trace_logger()
        self._progress_monitor = get_progress_monitor()
    
    def register_handler(
        self,
        exception_type: Type[Exception],
        handler: Callable[[ExceptionInfo], bool]
    ) -> None:
        """
        注册异常处理器
        
        Args:
            exception_type: 异常类型
            handler: 处理函数，返回True表示已处理
        """
        with self._lock:
            if exception_type not in self._handlers:
                self._handlers[exception_type] = []
            self._handlers[exception_type].append(handler)
    
    def unregister_handler(
        self,
        exception_type: Type[Exception],
        handler: Callable[[ExceptionInfo], bool]
    ) -> None:
        """注销异常处理器"""
        with self._lock:
            if exception_type in self._handlers:
                if handler in self._handlers[exception_type]:
                    self._handlers[exception_type].remove(handler)
    
    def register_listener(
        self,
        listener: Callable[[ExceptionInfo], None]
    ) -> None:
        """注册异常监听器"""
        with self._lock:
            if listener not in self._listeners:
                self._listeners.append(listener)
    
    def unregister_listener(
        self,
        listener: Callable[[ExceptionInfo], None]
    ) -> None:
        """注销异常监听器"""
        with self._lock:
            if listener in self._listeners:
                self._listeners.remove(listener)
    
    def handle_exception(
        self,
        exception: Exception,
        task_id: Optional[str] = None,
        layer: Optional[LayerType] = None
    ) -> ExceptionInfo:
        """
        处理异常
        
        Args:
            exception: 异常对象
            task_id: 任务ID
            layer: 层级
            
        Returns:
            异常信息
        """
        with self._lock:
            # 创建异常信息
            if isinstance(exception, TaskPlanningException):
                exception_info = exception.to_exception_info()
                exception_info.stack_trace = traceback.format_exc()
                exception_info.exception_type = type(exception).__name__
            else:
                exception_info = ExceptionInfo(
                    error_code=ErrorCode.UNKNOWN_ERROR,
                    severity=ErrorSeverity.ERROR,
                    message=str(exception),
                    layer=layer,
                    task_id=task_id,
                    exception_type=type(exception).__name__,
                    stack_trace=traceback.format_exc()
                )
            
            # 记录到历史
            self._exception_history.append(exception_info)
            
            # 记录日志
            self._log_exception(exception_info)
            
            # 记录到追踪系统
            self._trace_exception(exception_info)
            
            # 更新任务状态
            if task_id:
                self._update_task_status(task_id, exception_info)
            
            # 分发到处理器
            handled = self._dispatch_to_handlers(exception, exception_info)
            
            # 通知监听器
            self._notify_listeners(exception_info)
            
            return exception_info
    
    def _log_exception(self, exception_info: ExceptionInfo) -> None:
        """记录异常日志"""
        log_level_map = {
            ErrorSeverity.INFO: LogLevel.INFO,
            ErrorSeverity.WARNING: LogLevel.WARNING,
            ErrorSeverity.ERROR: LogLevel.ERROR,
            ErrorSeverity.CRITICAL: LogLevel.CRITICAL,
            ErrorSeverity.FATAL: LogLevel.CRITICAL
        }
        
        log_level = log_level_map.get(exception_info.severity, LogLevel.ERROR)
        
        log_msg = (
            f"[{exception_info.error_code.value}] {exception_info.message}"
        )
        if exception_info.task_id:
            log_msg = f"[Task {exception_info.task_id}] {log_msg}"
        if exception_info.layer:
            log_msg = f"[{exception_info.layer.value}] {log_msg}"
        
        logger.log(log_level.value, log_msg)
        
        if exception_info.stack_trace:
            logger.debug(exception_info.stack_trace)
    
    def _trace_exception(self, exception_info: ExceptionInfo) -> None:
        """记录到追踪系统"""
        if exception_info.task_id:
            try:
                self._trace_logger.log(
                    task_id=exception_info.task_id,
                    level=TraceLevel.OPERATION,
                    layer=exception_info.layer,
                    operation=OperationType.ERROR,
                    operation_name="exception_occurred",
                    message=exception_info.message,
                    data=exception_info.details
                )
            except Exception:
                pass
    
    def _update_task_status(self, task_id: str, exception_info: ExceptionInfo) -> None:
        """更新任务状态"""
        try:
            if exception_info.severity in [ErrorSeverity.CRITICAL, ErrorSeverity.FATAL]:
                self._progress_monitor.set_task_status(
                    task_id=task_id,
                    status=TaskStatus.FAILED,
                    message=exception_info.message
                )
        except Exception:
            pass
    
    def _dispatch_to_handlers(
        self,
        exception: Exception,
        exception_info: ExceptionInfo
    ) -> bool:
        """分发到处理器"""
        handled = False
        
        # 查找匹配的处理器
        for exc_type, handlers in self._handlers.items():
            if isinstance(exception, exc_type):
                for handler in handlers:
                    try:
                        if handler(exception_info):
                            handled = True
                    except Exception as e:
                        logger.error(f"Exception handler failed: {e}")
        
        return handled
    
    def _notify_listeners(self, exception_info: ExceptionInfo) -> None:
        """通知监听器"""
        for listener in self._listeners:
            try:
                listener(exception_info)
            except Exception as e:
                logger.error(f"Exception listener failed: {e}")
    
    def get_exception_history(
        self,
        task_id: Optional[str] = None,
        layer: Optional[LayerType] = None,
        error_code: Optional[ErrorCode] = None,
        limit: int = 100
    ) -> List[ExceptionInfo]:
        """
        获取异常历史
        
        Args:
            task_id: 任务ID过滤
            layer: 层级过滤
            error_code: 错误码过滤
            limit: 返回数量限制
            
        Returns:
            异常信息列表
        """
        with self._lock:
            results = []
            for exc_info in reversed(self._exception_history):
                if task_id and exc_info.task_id != task_id:
                    continue
                if layer and exc_info.layer != layer:
                    continue
                if error_code and exc_info.error_code != error_code:
                    continue
                results.append(exc_info)
                if len(results) >= limit:
                    break
            return results
    
    def get_statistics(
        self,
        task_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取异常统计
        
        Args:
            task_id: 任务ID过滤
            
        Returns:
            统计信息
        """
        with self._lock:
            stats = {
                "total_exceptions": 0,
                "by_severity": {},
                "by_layer": {},
                "by_error_code": {},
                "recent_errors": []
            }
            
            filtered_history = self._exception_history
            if task_id:
                filtered_history = [e for e in filtered_history if e.task_id == task_id]
            
            stats["total_exceptions"] = len(filtered_history)
            
            for exc_info in filtered_history:
                # 按严重程度统计
                sev = exc_info.severity.value
                stats["by_severity"][sev] = stats["by_severity"].get(sev, 0) + 1
                
                # 按层级统计
                if exc_info.layer:
                    layer = exc_info.layer.value
                    stats["by_layer"][layer] = stats["by_layer"].get(layer, 0) + 1
                
                # 按错误码统计
                code = exc_info.error_code.value
                stats["by_error_code"][code] = stats["by_error_code"].get(code, 0) + 1
            
            # 最近错误
            stats["recent_errors"] = [
                e.to_dict() for e in filtered_history[-10:]
            ]
            
            return stats


# 全局单例
_exception_handler_instance: Optional[ExceptionHandler] = None


def get_exception_handler() -> ExceptionHandler:
    """
    获取异常处理器单例
    
    Returns:
        ExceptionHandler: 异常处理器
    """
    global _exception_handler_instance
    if _exception_handler_instance is None:
        _exception_handler_instance = ExceptionHandler()
    return _exception_handler_instance


def handle_exception(
    exception: Exception,
    task_id: Optional[str] = None,
    layer: Optional[LayerType] = None
) -> ExceptionInfo:
    """
    便捷函数：处理异常
    
    Args:
        exception: 异常对象
        task_id: 任务ID
        layer: 层级
        
    Returns:
        异常信息
    """
    return get_exception_handler().handle_exception(
        exception, task_id, layer
    )


def catch_exceptions(
    task_id_param: Optional[str] = None,
    layer: Optional[LayerType] = None,
    reraise: bool = True,
    default_return: Any = None
):
    """
    异常捕获装饰器
    
    Args:
        task_id_param: 任务ID参数名
        layer: 层级
        reraise: 是否重新抛出异常
        default_return: 异常时返回的默认值
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            task_id = kwargs.get(task_id_param) if task_id_param else None
            if not task_id and len(args) > 0 and isinstance(args[0], str):
                task_id = args[0]
            
            try:
                return func(*args, **kwargs)
            except Exception as e:
                handle_exception(e, task_id, layer)
                if reraise:
                    raise
                return default_return
        return wrapper
    return decorator


# 使用示例
if __name__ == "__main__":
    print("=" * 60)
    print("统一全局异常捕获与分发机制 - 使用示例")
    print("=" * 60)
    
    # 获取异常处理器
    handler = get_exception_handler()
    
    # 注册监听器
    def on_exception(exc_info: ExceptionInfo):
        print(f"  捕获异常: [{exc_info.error_code.value}] {exc_info.message}")
    
    handler.register_listener(on_exception)
    
    # 注册处理器
    def handle_modeling_exception(exc_info: ExceptionInfo) -> bool:
        print(f"  处理建模层异常: {exc_info.message}")
        return True
    
    handler.register_handler(ModelingException, handle_modeling_exception)
    
    # 测试异常
    print("\n1. 测试异常捕获:")
    
    try:
        raise ModelingException(
            error_code=ErrorCode.TARGET_EXTRACTION_FAILED,
            message="无法从用户需求中提取目标",
            task_id="test_task_001",
            details={"requirement": "测试需求"}
        )
    except Exception as e:
        exc_info = handle_exception(e, task_id="test_task_001")
    
    # 测试未知异常
    print("\n2. 测试未知异常:")
    try:
        1 / 0
    except Exception as e:
        exc_info = handle_exception(e, task_id="test_task_001")
    
    # 获取统计
    print("\n3. 异常统计:")
    stats = handler.get_statistics()
    print(f"   总异常数: {stats['total_exceptions']}")
    print(f"   按严重程度: {stats['by_severity']}")
    print(f"   按错误码: {stats['by_error_code']}")
    
    # 获取历史
    print("\n4. 异常历史:")
    history = handler.get_exception_history()
    for exc in history:
        print(f"   [{exc.error_code.value}] {exc.message}")
    
    print("\n" + "=" * 60)
    print("统一全局异常捕获与分发机制 - 示例完成")
    print("=" * 60)
