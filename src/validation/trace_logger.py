"""
第四层：分段校验收敛层 - 全流程日志追踪系统
基于第一性原理的AI Agent任务规划系统

核心功能：
- 全链路任务追踪（TaskID关联）
- 四层架构每一层操作记录
- 结构化追踪数据存储
- 可审计、可追溯的完整日志
- 支持查询和导出
"""

import uuid
import time
import json
import os
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime
from collections import deque
import threading


class TraceLevel(Enum):
    """追踪级别"""
    TASK = "task"          # 任务级
    LAYER = "layer"        # 层级
    OPERATION = "operation"  # 操作级
    DETAIL = "detail"      # 详情级


class LayerType(Enum):
    """四层架构类型"""
    MODELING = "modeling"      # 第一层：任务归一建模层
    TOPOLOGY = "topology"      # 第二层：拓扑依赖拆解层
    ATOMIC = "atomic"          # 第三层：原子动作收敛层
    VALIDATION = "validation"  # 第四层：分段校验收敛层


class OperationType(Enum):
    """操作类型"""
    START = "start"
    INPUT = "input"
    PROCESS = "process"
    OUTPUT = "output"
    VALIDATE = "validate"
    ERROR = "error"
    COMPLETE = "complete"


@dataclass
class TraceRecord:
    """追踪记录"""
    trace_id: str
    task_id: str
    parent_trace_id: Optional[str]
    timestamp: float
    level: TraceLevel
    layer: Optional[LayerType]
    operation: OperationType
    operation_name: str
    message: str
    data: Dict[str, Any] = field(default_factory=dict)
    duration: Optional[float] = None
    success: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "task_id": self.task_id,
            "parent_trace_id": self.parent_trace_id,
            "timestamp": self.timestamp,
            "datetime": datetime.fromtimestamp(self.timestamp).isoformat(),
            "level": self.level.value,
            "layer": self.layer.value if self.layer else None,
            "operation": self.operation.value,
            "operation_name": self.operation_name,
            "message": self.message,
            "data": self.data,
            "duration": self.duration,
            "success": self.success
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)


@dataclass
class TaskTrace:
    """任务完整追踪"""
    task_id: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    records: List[TraceRecord] = field(default_factory=list)
    status: str = "running"
    result: Optional[Any] = None
    
    def add_record(self, record: TraceRecord):
        self.records.append(record)
    
    def complete(self, success: bool = True, result: Any = None):
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        self.status = "completed" if success else "failed"
        self.result = result


class TraceLogger:
    """
    全流程日志追踪器
    
    功能：
    - 生成唯一TaskID和TraceID
    - 记录四层架构每一层的操作
    - 支持父子追踪关联
    - 结构化数据存储
    - 可查询、可审计、可追溯
    """
    
    def __init__(self, max_records: int = 10000, storage_path: Optional[str] = None):
        """
        初始化追踪器
        
        Args:
            max_records: 内存中保留的最大记录数
            storage_path: 持久化存储路径
        """
        self.max_records = max_records
        self.storage_path = storage_path
        
        # 任务追踪存储
        self.task_traces: Dict[str, TaskTrace] = {}
        
        # 记录队列
        self.records: deque = deque(maxlen=max_records)
        
        # 当前活动追踪
        self.active_traces: Dict[str, Dict[str, Any]] = {}
        
        # 锁
        self._lock = threading.RLock()
        
        # 初始化存储目录
        if storage_path:
            os.makedirs(storage_path, exist_ok=True)
    
    def create_task(self, task_description: str, initial_data: Optional[Dict[str, Any]] = None) -> str:
        """
        创建新任务追踪
        
        Args:
            task_description: 任务描述
            initial_data: 初始数据
            
        Returns:
            str: 任务ID
        """
        with self._lock:
            task_id = str(uuid.uuid4())
            task_trace = TaskTrace(
                task_id=task_id,
                start_time=time.time()
            )
            
            # 记录任务开始
            record = TraceRecord(
                trace_id=str(uuid.uuid4()),
                task_id=task_id,
                parent_trace_id=None,
                timestamp=time.time(),
                level=TraceLevel.TASK,
                layer=None,
                operation=OperationType.START,
                operation_name="task_start",
                message=f"任务开始: {task_description}",
                data=initial_data or {}
            )
            
            task_trace.add_record(record)
            self.records.append(record)
            self.task_traces[task_id] = task_trace
            
            return task_id
    
    def _create_trace_id(self) -> str:
        """生成追踪ID"""
        return str(uuid.uuid4())
    
    def log(
        self,
        task_id: str,
        level: TraceLevel,
        layer: Optional[LayerType],
        operation: OperationType,
        operation_name: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        parent_trace_id: Optional[str] = None
    ) -> str:
        """
        记录追踪日志
        
        Args:
            task_id: 任务ID
            level: 追踪级别
            layer: 层级
            operation: 操作类型
            operation_name: 操作名称
            message: 消息
            data: 附加数据
            parent_trace_id: 父追踪ID
            
        Returns:
            str: 追踪ID
        """
        with self._lock:
            if task_id not in self.task_traces:
                # 如果任务不存在，自动创建
                self.task_traces[task_id] = TaskTrace(
                    task_id=task_id,
                    start_time=time.time()
                )
            
            trace_id = self._create_trace_id()
            record = TraceRecord(
                trace_id=trace_id,
                task_id=task_id,
                parent_trace_id=parent_trace_id,
                timestamp=time.time(),
                level=level,
                layer=layer,
                operation=operation,
                operation_name=operation_name,
                message=message,
                data=data or {}
            )
            
            self.task_traces[task_id].add_record(record)
            self.records.append(record)
            
            # 持久化
            self._persist_record(record)
            
            return trace_id
    
    def log_layer_operation(
        self,
        task_id: str,
        layer: LayerType,
        operation: OperationType,
        operation_name: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        parent_trace_id: Optional[str] = None
    ) -> str:
        """
        记录层级操作日志（便捷方法）
        
        Args:
            task_id: 任务ID
            layer: 层级
            operation: 操作类型
            operation_name: 操作名称
            message: 消息
            data: 附加数据
            parent_trace_id: 父追踪ID
            
        Returns:
            str: 追踪ID
        """
        return self.log(
            task_id=task_id,
            level=TraceLevel.LAYER,
            layer=layer,
            operation=operation,
            operation_name=operation_name,
            message=message,
            data=data,
            parent_trace_id=parent_trace_id
        )
    
    def start_operation(
        self,
        task_id: str,
        layer: Optional[LayerType],
        operation_name: str,
        message: str,
        data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        开始操作追踪
        
        Args:
            task_id: 任务ID
            layer: 层级
            operation_name: 操作名称
            message: 消息
            data: 附加数据
            
        Returns:
            str: 追踪ID
        """
        with self._lock:
            trace_id = self._create_trace_id()
            start_time = time.time()
            
            # 记录开始
            record = TraceRecord(
                trace_id=trace_id,
                task_id=task_id,
                parent_trace_id=None,
                timestamp=start_time,
                level=TraceLevel.OPERATION,
                layer=layer,
                operation=OperationType.START,
                operation_name=operation_name,
                message=message,
                data=data or {}
            )
            
            self.active_traces[trace_id] = {
                "start_time": start_time,
                "task_id": task_id,
                "layer": layer,
                "operation_name": operation_name
            }
            
            if task_id in self.task_traces:
                self.task_traces[task_id].add_record(record)
            self.records.append(record)
            self._persist_record(record)
            
            return trace_id
    
    def end_operation(
        self,
        trace_id: str,
        success: bool = True,
        result_data: Optional[Dict[str, Any]] = None,
        message: Optional[str] = None
    ) -> Optional[TraceRecord]:
        """
        结束操作追踪
        
        Args:
            trace_id: 追踪ID
            success: 是否成功
            result_data: 结果数据
            message: 消息
            
        Returns:
            TraceRecord: 结束记录
        """
        with self._lock:
            if trace_id not in self.active_traces:
                return None
            
            active_trace = self.active_traces.pop(trace_id)
            end_time = time.time()
            duration = end_time - active_trace["start_time"]
            
            record = TraceRecord(
                trace_id=str(uuid.uuid4()),
                task_id=active_trace["task_id"],
                parent_trace_id=trace_id,
                timestamp=end_time,
                level=TraceLevel.OPERATION,
                layer=active_trace["layer"],
                operation=OperationType.COMPLETE,
                operation_name=active_trace["operation_name"],
                message=message or f"操作完成: {active_trace['operation_name']}",
                data=result_data or {},
                duration=duration,
                success=success
            )
            
            task_id = active_trace["task_id"]
            if task_id in self.task_traces:
                self.task_traces[task_id].add_record(record)
            self.records.append(record)
            self._persist_record(record)
            
            return record
    
    def complete_task(
        self,
        task_id: str,
        success: bool = True,
        result: Any = None,
        message: Optional[str] = None
    ) -> Optional[TaskTrace]:
        """
        完成任务追踪
        
        Args:
            task_id: 任务ID
            success: 是否成功
            result: 结果
            message: 消息
            
        Returns:
            TaskTrace: 任务追踪
        """
        with self._lock:
            if task_id not in self.task_traces:
                return None
            
            task_trace = self.task_traces[task_id]
            
            # 记录任务完成
            record = TraceRecord(
                trace_id=str(uuid.uuid4()),
                task_id=task_id,
                parent_trace_id=None,
                timestamp=time.time(),
                level=TraceLevel.TASK,
                layer=None,
                operation=OperationType.COMPLETE,
                operation_name="task_complete",
                message=message or ("任务成功完成" if success else "任务执行失败"),
                data={"result": str(result) if result else None},
                success=success
            )
            
            task_trace.add_record(record)
            task_trace.complete(success=success, result=result)
            self.records.append(record)
            self._persist_record(record)
            
            # 持久化完整任务
            self._persist_task_trace(task_trace)
            
            return task_trace
    
    def get_task_trace(self, task_id: str) -> Optional[TaskTrace]:
        """获取任务完整追踪"""
        with self._lock:
            return self.task_traces.get(task_id)
    
    def get_task_records(self, task_id: str) -> List[TraceRecord]:
        """获取任务的所有记录"""
        with self._lock:
            if task_id in self.task_traces:
                return self.task_traces[task_id].records.copy()
            return []
    
    def query_records(
        self,
        task_id: Optional[str] = None,
        layer: Optional[LayerType] = None,
        level: Optional[TraceLevel] = None,
        operation: Optional[OperationType] = None,
        limit: int = 100
    ) -> List[TraceRecord]:
        """
        查询追踪记录
        
        Args:
            task_id: 任务ID过滤
            layer: 层级过滤
            level: 级别过滤
            operation: 操作类型过滤
            limit: 返回数量限制
            
        Returns:
            List[TraceRecord]: 匹配的记录
        """
        with self._lock:
            results = []
            for record in reversed(self.records):
                if task_id and record.task_id != task_id:
                    continue
                if layer and record.layer != layer:
                    continue
                if level and record.level != level:
                    continue
                if operation and record.operation != operation:
                    continue
                results.append(record)
                if len(results) >= limit:
                    break
            return list(reversed(results))
    
    def export_task_trace(self, task_id: str, format: str = "json") -> Optional[str]:
        """
        导出任务追踪
        
        Args:
            task_id: 任务ID
            format: 导出格式 (json)
            
        Returns:
            str: 导出内容
        """
        with self._lock:
            task_trace = self.task_traces.get(task_id)
            if not task_trace:
                return None
            
            if format == "json":
                export_data = {
                    "task_id": task_trace.task_id,
                    "start_time": task_trace.start_time,
                    "start_datetime": datetime.fromtimestamp(task_trace.start_time).isoformat(),
                    "end_time": task_trace.end_time,
                    "end_datetime": datetime.fromtimestamp(task_trace.end_time).isoformat() if task_trace.end_time else None,
                    "duration": task_trace.duration,
                    "status": task_trace.status,
                    "result": str(task_trace.result),
                    "records": [r.to_dict() for r in task_trace.records]
                }
                return json.dumps(export_data, ensure_ascii=False, indent=2)
            
            return None
    
    def _persist_record(self, record: TraceRecord):
        """持久化单条记录"""
        if not self.storage_path:
            return
        
        log_file = os.path.join(self.storage_path, f"trace_{datetime.now().strftime('%Y%m%d')}.log")
        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(record.to_json() + '\n')
        except Exception:
            pass
    
    def _persist_task_trace(self, task_trace: TaskTrace):
        """持久化完整任务追踪"""
        if not self.storage_path:
            return
        
        task_file = os.path.join(self.storage_path, f"task_{task_trace.task_id}.json")
        try:
            export_data = {
                "task_id": task_trace.task_id,
                "start_time": task_trace.start_time,
                "end_time": task_trace.end_time,
                "duration": task_trace.duration,
                "status": task_trace.status,
                "records": [r.to_dict() for r in task_trace.records]
            }
            with open(task_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    
    def get_statistics(self, task_id: Optional[str] = None) -> Dict[str, Any]:
        """
        获取统计信息
        
        Args:
            task_id: 任务ID，None则获取全局统计
            
        Returns:
            Dict[str, Any]: 统计信息
        """
        with self._lock:
            if task_id:
                task_trace = self.task_traces.get(task_id)
                if not task_trace:
                    return {}
                
                layer_stats = {}
                for layer in LayerType:
                    layer_records = [r for r in task_trace.records if r.layer == layer]
                    layer_stats[layer.value] = {
                        "count": len(layer_records),
                        "success_count": sum(1 for r in layer_records if r.success),
                        "total_duration": sum(r.duration or 0 for r in layer_records)
                    }
                
                return {
                    "task_id": task_id,
                    "total_records": len(task_trace.records),
                    "status": task_trace.status,
                    "duration": task_trace.duration,
                    "layer_stats": layer_stats
                }
            else:
                # 全局统计
                return {
                    "total_tasks": len(self.task_traces),
                    "completed_tasks": sum(1 for t in self.task_traces.values() if t.status == "completed"),
                    "failed_tasks": sum(1 for t in self.task_traces.values() if t.status == "failed"),
                    "total_records": len(self.records)
                }


# 全局单例
_trace_logger_instance: Optional[TraceLogger] = None


def get_trace_logger(storage_path: Optional[str] = None) -> TraceLogger:
    """
    获取追踪日志器单例
    
    Args:
        storage_path: 存储路径（仅首次调用有效）
        
    Returns:
        TraceLogger: 追踪日志器
    """
    global _trace_logger_instance
    if _trace_logger_instance is None:
        _trace_logger_instance = TraceLogger(storage_path=storage_path)
    return _trace_logger_instance


# 便捷装饰器
def trace_operation(layer: Optional[LayerType] = None, operation_name: Optional[str] = None):
    """
    操作追踪装饰器
    
    Args:
        layer: 层级
        operation_name: 操作名称
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # 尝试从kwargs或args中获取task_id
            task_id = kwargs.get('task_id')
            if not task_id and len(args) > 0:
                # 尝试从第一个参数获取
                first_arg = args[0]
                if isinstance(first_arg, str) and len(first_arg) > 20:
                    task_id = first_arg
            
            if not task_id:
                # 如果没有task_id，不追踪
                return func(*args, **kwargs)
            
            tracer = get_trace_logger()
            name = operation_name or func.__name__
            trace_id = tracer.start_operation(
                task_id=task_id,
                layer=layer,
                operation_name=name,
                message=f"开始执行: {name}",
                data={"args": str(args), "kwargs": str(kwargs)}
            )
            
            try:
                result = func(*args, **kwargs)
                tracer.end_operation(
                    trace_id=trace_id,
                    success=True,
                    result_data={"result": str(result)},
                    message=f"执行成功: {name}"
                )
                return result
            except Exception as e:
                tracer.end_operation(
                    trace_id=trace_id,
                    success=False,
                    result_data={"error": str(e)},
                    message=f"执行失败: {name} - {str(e)}"
                )
                raise
        
        return wrapper
    return decorator


# 使用示例
if __name__ == "__main__":
    print("=" * 60)
    print("全流程日志追踪系统 - 使用示例")
    print("=" * 60)
    
    # 1. 获取追踪器
    tracer = get_trace_logger(storage_path="/tmp/trace_logs")
    
    # 2. 创建任务
    print("\n1. 创建任务:")
    task_id = tracer.create_task(
        task_description="示例任务规划",
        initial_data={"input": "用户需求"}
    )
    print(f"   任务ID: {task_id}")
    
    # 3. 记录各层操作
    print("\n2. 记录四层架构操作:")
    
    # 第一层：建模层
    tracer.log_layer_operation(
        task_id=task_id,
        layer=LayerType.MODELING,
        operation=OperationType.INPUT,
        operation_name="parse_requirement",
        message="解析用户需求",
        data={"requirement": "创建一个网站"}
    )
    
    tracer.log_layer_operation(
        task_id=task_id,
        layer=LayerType.MODELING,
        operation=OperationType.PROCESS,
        operation_name="extract_target",
        message="提取任务目标",
        data={"target": "创建网站"}
    )
    
    tracer.log_layer_operation(
        task_id=task_id,
        layer=LayerType.MODELING,
        operation=OperationType.OUTPUT,
        operation_name="model_complete",
        message="建模完成",
        data={"task_quad": "(Target, Condition, Boundary, EndRule)"}
    )
    
    # 第二层：拓扑层
    tracer.log_layer_operation(
        task_id=task_id,
        layer=LayerType.TOPOLOGY,
        operation=OperationType.PROCESS,
        operation_name="decompose_task",
        message="分解任务拓扑",
        data={"subtasks": 3}
    )
    
    # 第三层：原子层
    tracer.log_layer_operation(
        task_id=task_id,
        layer=LayerType.ATOMIC,
        operation=OperationType.PROCESS,
        operation_name="atomic_split",
        message="拆分原子动作",
        data={"atomic_actions": 8}
    )
    
    # 第四层：验证层
    tracer.log_layer_operation(
        task_id=task_id,
        layer=LayerType.VALIDATION,
        operation=OperationType.VALIDATE,
        operation_name="validate_plan",
        message="验证规划结果",
        data={"valid": True}
    )
    
    # 4. 使用操作追踪
    print("\n3. 操作追踪示例:")
    
    @trace_operation(layer=LayerType.VALIDATION, operation_name="final_check")
    def final_check(task_id: str, data: dict) -> bool:
        time.sleep(0.1)
        return True
    
    result = final_check(task_id, {"some": "data"})
    print(f"   操作结果: {result}")
    
    # 5. 完成任务
    print("\n4. 完成任务:")
    task_trace = tracer.complete_task(
        task_id=task_id,
        success=True,
        result={"plan": "完整规划"},
        message="任务成功完成"
    )
    
    # 6. 查询和导出
    print("\n5. 查询任务记录:")
    records = tracer.get_task_records(task_id)
    print(f"   共 {len(records)} 条记录")
    
    print("\n6. 任务统计:")
    stats = tracer.get_statistics(task_id=task_id)
    print(f"   状态: {stats['status']}")
    print(f"   总记录: {stats['total_records']}")
    
    print("\n7. 导出追踪:")
    export_data = tracer.export_task_trace(task_id)
    print(f"   导出成功，JSON长度: {len(export_data)}")
    
    print("\n" + "=" * 60)
    print("全流程日志追踪系统 - 示例完成")
    print("=" * 60)
