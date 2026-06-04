"""
多任务并发调度器
基于第一性原理的AI Agent任务规划系统

核心功能：
- 多任务并发调度
- 任务队列管理
- 资源限制控制
- 任务状态监控
"""

import uuid
import time
import threading
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue, PriorityQueue

from interfaces.orchestrator_interface import OrchestratorInterface, OrchestratorResult
from validation.trace_logger import get_trace_logger, LayerType, OperationType, TraceLevel
from validation.progress_monitor import get_progress_monitor, TaskStatus, LayerStatus, ProgressPhase
from validation.exception_handler import get_exception_handler, handle_exception


@dataclass
class TaskRequest:
    """任务请求"""
    requirement: str
    priority: int = 5  # 1-10, 数字越小优先级越高
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    callback: Optional[Callable[[OrchestratorResult], None]] = None


@dataclass
class TaskStatusInfo:
    """任务状态信息"""
    task_id: str
    status: str
    progress: float
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    result: Optional[OrchestratorResult] = None
    error_message: str = ""


class ConcurrentTaskScheduler:
    """
    多任务并发调度器
    
    功能：
    - 多任务并发调度
    - 优先级队列管理
    - 资源限制控制
    - 任务状态监控
    """
    
    def __init__(self, max_workers: int = 4, max_queue_size: int = 100):
        """
        初始化并发调度器
        
        Args:
            max_workers: 最大并发工作线程数
            max_queue_size: 最大队列大小
        """
        self.max_workers = max_workers
        self.max_queue_size = max_queue_size
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.orchestrator = OrchestratorInterface()
        self.tracer = get_trace_logger()
        self.progress = get_progress_monitor()
        self.exception_handler = get_exception_handler()
        
        # 任务队列
        self.task_queue: Queue = Queue(maxsize=max_queue_size)
        self.pending_tasks: Dict[str, TaskRequest] = {}
        self.running_tasks: Dict[str, threading.Thread] = {}
        self.completed_tasks: Dict[str, TaskStatusInfo] = {}
        
        # 锁
        self._lock = threading.RLock()
        self._shutdown = False
        
        # 启动调度线程
        self._scheduler_thread = threading.Thread(target=self._schedule_loop, daemon=True)
        self._scheduler_thread.start()
    
    def submit_task(
        self,
        requirement: str,
        priority: int = 5,
        callback: Optional[Callable[[OrchestratorResult], None]] = None
    ) -> str:
        """
        提交任务
        
        Args:
            requirement: 用户需求描述
            priority: 优先级（1-10，数字越小优先级越高）
            callback: 完成回调函数
            
        Returns:
            str: 任务ID
        """
        with self._lock:
            if self._shutdown:
                raise RuntimeError("调度器已关闭")
            
            task_request = TaskRequest(
                requirement=requirement,
                priority=priority,
                callback=callback
            )
            
            # 添加到队列
            self.task_queue.put(task_request)
            self.pending_tasks[task_request.task_id] = task_request
            
            self.tracer.log(
                task_id=task_request.task_id,
                level=TraceLevel.TASK,
                layer=None,
                operation=OperationType.START,
                operation_name="task_submitted",
                message=f"任务已提交: {requirement[:50]}...",
                data={"priority": priority}
            )
            
            return task_request.task_id
    
    def _schedule_loop(self):
        """调度循环"""
        while not self._shutdown:
            try:
                # 获取任务（阻塞等待）
                task_request = self.task_queue.get(timeout=1.0)
                
                if task_request is None:
                    continue
                
                # 提交到线程池执行
                future = self.executor.submit(self._execute_task, task_request)
                
                with self._lock:
                    self.running_tasks[task_request.task_id] = future
                    del self.pending_tasks[task_request.task_id]
                
            except Exception:
                # 超时或错误，继续循环
                pass
    
    def _execute_task(self, task_request: TaskRequest):
        """
        执行任务
        
        Args:
            task_request: 任务请求
        """
        task_id = task_request.task_id
        start_time = time.time()
        
        try:
            # 更新状态
            self.progress.create_task(task_id, task_request.requirement)
            self.progress.set_task_status(
                task_id=task_id,
                status=TaskStatus.RUNNING,
                message="任务执行中"
            )
            
            # 执行规划
            result = self.orchestrator.plan_task(
                requirement=task_request.requirement,
                task_id=task_id
            )
            
            # 更新完成状态
            end_time = time.time()
            status_info = TaskStatusInfo(
                task_id=task_id,
                status="completed" if result.success else "failed",
                progress=1.0,
                start_time=start_time,
                end_time=end_time,
                result=result,
                error_message=result.error_message
            )
            
            with self._lock:
                self.completed_tasks[task_id] = status_info
                if task_id in self.running_tasks:
                    del self.running_tasks[task_id]
            
            # 调用回调
            if task_request.callback:
                try:
                    task_request.callback(result)
                except Exception as e:
                    handle_exception(e, task_id=task_id)
            
        except Exception as e:
            end_time = time.time()
            status_info = TaskStatusInfo(
                task_id=task_id,
                status="failed",
                progress=0.0,
                start_time=start_time,
                end_time=end_time,
                error_message=str(e)
            )
            
            with self._lock:
                self.completed_tasks[task_id] = status_info
                if task_id in self.running_tasks:
                    del self.running_tasks[task_id]
            
            handle_exception(e, task_id=task_id)
    
    def get_task_status(self, task_id: str) -> Optional[TaskStatusInfo]:
        """
        获取任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            TaskStatusInfo: 任务状态信息
        """
        with self._lock:
            if task_id in self.completed_tasks:
                return self.completed_tasks[task_id]
            
            if task_id in self.pending_tasks:
                return TaskStatusInfo(
                    task_id=task_id,
                    status="pending",
                    progress=0.0
                )
            
            if task_id in self.running_tasks:
                return TaskStatusInfo(
                    task_id=task_id,
                    status="running",
                    progress=0.5
                )
            
            return None
    
    def get_all_tasks_status(self) -> Dict[str, TaskStatusInfo]:
        """
        获取所有任务状态
        
        Returns:
            Dict[str, TaskStatusInfo]: 所有任务状态
        """
        with self._lock:
            result = {}
            
            # 待处理任务
            for task_id in self.pending_tasks:
                result[task_id] = TaskStatusInfo(
                    task_id=task_id,
                    status="pending",
                    progress=0.0
                )
            
            # 运行中任务
            for task_id in self.running_tasks:
                result[task_id] = TaskStatusInfo(
                    task_id=task_id,
                    status="running",
                    progress=0.5
                )
            
            # 已完成任务
            for task_id, status in self.completed_tasks.items():
                result[task_id] = status
            
            return result
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取调度统计
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        with self._lock:
            return {
                "pending_count": len(self.pending_tasks),
                "running_count": len(self.running_tasks),
                "completed_count": len(self.completed_tasks),
                "max_workers": self.max_workers,
                "max_queue_size": self.max_queue_size
            }
    
    def shutdown(self, wait: bool = True):
        """
        关闭调度器
        
        Args:
            wait: 是否等待所有任务完成
        """
        with self._lock:
            self._shutdown = True
        
        if wait:
            self.executor.shutdown(wait=True)
        else:
            self.executor.shutdown(wait=False)


# 全局单例
_scheduler_instance: Optional[ConcurrentTaskScheduler] = None


def get_scheduler(max_workers: int = 4) -> ConcurrentTaskScheduler:
    """
    获取调度器单例
    
    Args:
        max_workers: 最大并发工作线程数
        
    Returns:
        ConcurrentTaskScheduler: 调度器
    """
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = ConcurrentTaskScheduler(max_workers=max_workers)
    return _scheduler_instance


# 使用示例
if __name__ == "__main__":
    import time
    
    print("=" * 60)
    print("多任务并发调度器 - 使用示例")
    print("=" * 60)
    
    # 创建调度器
    scheduler = ConcurrentTaskScheduler(max_workers=3)
    
    # 测试用例
    test_cases = [
        ("开发一个用户登录系统", 1),
        ("设计一个电商网站的商品搜索功能", 2),
        ("实现一个数据备份和恢复系统", 3),
        ("构建一个实时消息推送服务", 1),
        ("创建一个自动化测试框架", 2),
    ]
    
    # 提交任务
    print("\n1. 提交任务:")
    task_ids = []
    for requirement, priority in test_cases:
        task_id = scheduler.submit_task(requirement, priority=priority)
        task_ids.append(task_id)
        print(f"   提交: {requirement[:30]}... (优先级: {priority}, ID: {task_id[:8]})")
    
    # 等待所有任务完成
    print("\n2. 等待任务完成:")
    time.sleep(2)
    
    # 获取结果
    print("\n3. 任务结果:")
    for task_id in task_ids:
        status = scheduler.get_task_status(task_id)
        if status:
            print(f"   {task_id[:8]}: {status.status} (耗时: {status.end_time - status.start_time:.3f}s)" if status.end_time else f"   {task_id[:8]}: {status.status}")
    
    # 统计
    print("\n4. 调度统计:")
    stats = scheduler.get_statistics()
    print(f"   待处理: {stats['pending_count']}")
    print(f"   运行中: {stats['running_count']}")
    print(f"   已完成: {stats['completed_count']}")
    
    # 关闭
    scheduler.shutdown(wait=False)
    
    print("\n" + "=" * 60)
    print("多任务并发调度器 - 示例完成")
    print("=" * 60)
