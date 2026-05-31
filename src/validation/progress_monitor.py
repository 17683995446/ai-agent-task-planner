"""
第四层：分段校验收敛层 - 实时进度状态更新组件
基于第一性原理的AI Agent任务规划系统

核心功能：
- 实时任务进度跟踪
- 四层架构各阶段状态更新
- 进度回调通知机制
- 历史进度查询和统计
"""

import time
import threading
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from collections import deque


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"           # 待处理
    RUNNING = "running"           # 运行中
    PAUSED = "paused"             # 已暂停
    COMPLETED = "completed"       # 已完成
    FAILED = "failed"             # 失败
    CANCELLED = "cancelled"       # 已取消


class LayerStatus(Enum):
    """层级状态"""
    NOT_STARTED = "not_started"  # 未开始
    IN_PROGRESS = "in_progress"    # 进行中
    COMPLETED = "completed"      # 已完成
    FAILED = "failed"              # 失败


class ProgressPhase(Enum):
    """进度阶段"""
    MODELING = "modeling"           # 建模阶段
    TOPOLOGY = "topology"           # 拓扑阶段
    ATOMIC = "atomic"               # 原子阶段
    VALIDATION = "validation"       # 验证阶段


@dataclass
class LayerProgress:
    """层级进度"""
    layer: ProgressPhase
    status: LayerStatus
    progress: float = 0.0            # 进度百分比 0.0-1.0
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProgressUpdate:
    """进度更新"""
    task_id: str
    timestamp: float
    overall_progress: float
    current_phase: Optional[ProgressPhase]
    status: TaskStatus
    message: str
    layer_progress: Dict[ProgressPhase, LayerProgress]
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProgressHistory:
    """进度历史记录"""
    task_id: str
    updates: List[ProgressUpdate] = field(default_factory=list)
    start_time: Optional[float] = None
    end_time: Optional[float] = None


class ProgressMonitor:
    """
    实时进度状态监控器
    
    功能：
    - 跟踪任务整体进度
    - 跟踪四层架构各阶段进度
    - 进度回调通知机制
    - 历史进度查询和统计
    """
    
    def __init__(self):
        """初始化进度监控器"""
        self._task_progress: Dict[str, ProgressHistory] = {}
        self._callbacks: List[Callable[[ProgressUpdate], None]] = []
        self._lock = threading.RLock()
    
    def create_task(self, task_id: str, task_description: str = "") -> None:
        """
        创建任务进度跟踪
        
        Args:
            task_id: 任务ID
            task_description: 任务描述
        """
        with self._lock:
            if task_id in self._task_progress:
                return
            
            # 初始化各层级进度
            layer_progress = {}
            for phase in ProgressPhase:
                layer_progress[phase] = LayerProgress(
                    layer=phase,
                    status=LayerStatus.NOT_STARTED
                )
            
            # 创建初始进度历史
            history = ProgressHistory(
                task_id=task_id,
                start_time=time.time()
            )
            
            # 创建初始更新
            initial_update = ProgressUpdate(
                task_id=task_id,
                timestamp=time.time(),
                overall_progress=0.0,
                current_phase=None,
                status=TaskStatus.PENDING,
                message=f"任务已创建: {task_description}",
                layer_progress=layer_progress.copy()
            )
            
            history.updates.append(initial_update)
            self._task_progress[task_id] = history
            
            # 通知回调
            self._notify_callbacks(initial_update)
    
    def update_overall_progress(
        self, task_id: str, progress: float, message: str = "",
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        更新整体进度
        
        Args:
            task_id: 任务ID
            progress: 进度百分比 0.0-1.0
            message: 进度消息
            details: 附加详细信息
        """
        with self._lock:
            if task_id not in self._task_progress:
                return
            
            history = self._task_progress[task_id]
            last_update = history.updates[-1] if history.updates else None
            
            # 创建新的更新
            new_update = ProgressUpdate(
                task_id=task_id,
                timestamp=time.time(),
                overall_progress=max(0.0, min(1.0, progress)),
                current_phase=last_update.current_phase if last_update else None,
                status=last_update.status if last_update else TaskStatus.RUNNING,
                message=message,
                layer_progress=last_update.layer_progress.copy() if last_update else {},
                details=details or {}
            )
            
            history.updates.append(new_update)
            
            # 通知回调
            self._notify_callbacks(new_update)
    
    def update_layer_progress(
        self, task_id: str, phase: ProgressPhase,
        layer_status: LayerStatus, progress: float = 0.0,
        message: str = "", details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        更新层级进度
        
        Args:
            task_id: 任务ID
            phase: 进度阶段
            layer_status: 层级状态
            progress: 进度百分比 0.0-1.0
            message: 进度消息
            details: 附加详细信息
        """
        with self._lock:
            if task_id not in self._task_progress:
                return
            
            history = self._task_progress[task_id]
            last_update = history.updates[-1] if history.updates else None
            
            # 复制并更新层级进度
            new_layer_progress = last_update.layer_progress.copy() if last_update else {}
            
            # 更新指定层级
            if phase not in new_layer_progress:
                new_layer_progress[phase] = LayerProgress(layer=phase, status=layer_status)
            
            layer_prog = new_layer_progress[phase]
            layer_prog.status = layer_status
            layer_prog.progress = max(0.0, min(1.0, progress))
            layer_prog.message = message
            
            if layer_status == LayerStatus.IN_PROGRESS and layer_prog.start_time is None:
                layer_prog.start_time = time.time()
            elif layer_status in [LayerStatus.COMPLETED, LayerStatus.FAILED]:
                layer_prog.end_time = time.time()
            
            if details:
                layer_prog.details.update(details)
            
            # 计算整体进度
            overall_progress = self._calculate_overall_progress(new_layer_progress)
            
            # 创建新的更新
            new_update = ProgressUpdate(
                task_id=task_id,
                timestamp=time.time(),
                overall_progress=overall_progress,
                current_phase=phase,
                status=TaskStatus.RUNNING,
                message=message,
                layer_progress=new_layer_progress,
                details=details or {}
            )
            
            history.updates.append(new_update)
            
            # 通知回调
            self._notify_callbacks(new_update)
    
    def _calculate_overall_progress(self, layer_progress: Dict[ProgressPhase, LayerProgress]) -> float:
        """
        计算整体进度
        
        Args:
            layer_progress: 层级进度
        
        Returns:
            整体进度 0.0-1.0
        """
        if not layer_progress:
            return 0.0
        
        # 每个阶段权重
        weights = {
            ProgressPhase.MODELING: 0.25,
            ProgressPhase.TOPOLOGY: 0.25,
            ProgressPhase.ATOMIC: 0.25,
            ProgressPhase.VALIDATION: 0.25
        }
        
        total = 0.0
        for phase, layer_prog in layer_progress.items():
            weight = weights.get(phase, 0.0)
            total += layer_prog.progress * weight
        
        return total
    
    def set_task_status(self, task_id: str, status: TaskStatus, message: str = "") -> None:
        """
        设置任务状态
        
        Args:
            task_id: 任务ID
            status: 任务状态
            message: 状态消息
        """
        with self._lock:
            if task_id not in self._task_progress:
                return
            
            history = self._task_progress[task_id]
            last_update = history.updates[-1] if history.updates else None
            
            new_update = ProgressUpdate(
                task_id=task_id,
                timestamp=time.time(),
                overall_progress=last_update.overall_progress if last_update else 0.0,
                current_phase=last_update.current_phase if last_update else None,
                status=status,
                message=message,
                layer_progress=last_update.layer_progress.copy() if last_update else {}
            )
            
            history.updates.append(new_update)
            
            if status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                history.end_time = time.time()
            
            self._notify_callbacks(new_update)
    
    def get_current_progress(self, task_id: str) -> Optional[ProgressUpdate]:
        """
        获取当前进度
        
        Args:
            task_id: 任务ID
        
        Returns:
            当前进度更新
        """
        with self._lock:
            if task_id not in self._task_progress:
                return None
            history = self._task_progress[task_id]
            return history.updates[-1] if history.updates else None
    
    def get_progress_history(self, task_id: str, limit: Optional[int] = None) -> List[ProgressUpdate]:
        """
        获取进度历史
        
        Args:
            task_id: 任务ID
            limit: 返回数量限制
        
        Returns:
            进度更新列表
        """
        with self._lock:
            if task_id not in self._task_progress:
                return []
            history = self._task_progress[task_id]
            updates = history.updates
            if limit and limit < len(updates):
                return updates[-limit:]
            return updates.copy()
    
    def get_statistics(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取进度统计
        
        Args:
            task_id: 任务ID
        
        Returns:
            统计信息
        """
        with self._lock:
            if task_id not in self._task_progress:
                return None
            
            history = self._task_progress[task_id]
            last_update = history.updates[-1] if history.updates else None
            
            if not last_update:
                return None
            
            stats = {
                "task_id": task_id,
                "status": last_update.status.value,
                "overall_progress": last_update.overall_progress,
                "current_phase": last_update.current_phase.value if last_update.current_phase else None,
                "start_time": history.start_time,
                "end_time": history.end_time,
                "duration": (history.end_time - history.start_time) if history.end_time and history.start_time else None,
                "total_updates": len(history.updates),
                "layer_progress": {}
            }
            
            for phase, layer_prog in last_update.layer_progress.items():
                stats["layer_progress"][phase.value] = {
                    "status": layer_prog.status.value,
                    "progress": layer_prog.progress,
                    "message": layer_prog.message
                }
            
            return stats
    
    def register_callback(self, callback: Callable[[ProgressUpdate], None]) -> None:
        """
        注册进度回调
        
        Args:
            callback: 回调函数，接收ProgressUpdate参数
        """
        with self._lock:
            if callback not in self._callbacks:
                self._callbacks.append(callback)
    
    def unregister_callback(self, callback: Callable[[ProgressUpdate], None]) -> None:
        """
        注销进度回调
        
        Args:
            callback: 回调函数
        """
        with self._lock:
            if callback in self._callbacks:
                self._callbacks.remove(callback)
    
    def _notify_callbacks(self, update: ProgressUpdate) -> None:
        """
        通知所有回调
        
        Args:
            update: 进度更新
        """
        for callback in self._callbacks:
            try:
                callback(update)
            except Exception:
                pass


# 全局单例
_progress_monitor_instance: Optional[ProgressMonitor] = None


def get_progress_monitor() -> ProgressMonitor:
    """
    获取进度监控器单例
    
    Returns:
        ProgressMonitor: 进度监控器
    """
    global _progress_monitor_instance
    if _progress_monitor_instance is None:
        _progress_monitor_instance = ProgressMonitor()
    return _progress_monitor_instance


# 使用示例
if __name__ == "__main__":
    import time
    
    print("=" * 60)
    print("实时进度状态更新组件 - 使用示例")
    print("=" * 60)
    
    # 获取监控器
    monitor = get_progress_monitor()
    
    # 定义回调函数
    def on_progress_update(update: ProgressUpdate):
        phase_str = update.current_phase.value if update.current_phase else "None"
        print(f"\r进度: {update.overall_progress * 100:.1f}% | 阶段: {phase_str} | 状态: {update.status.value} | {update.message}", end="", flush=True)
    
    monitor.register_callback(on_progress_update)
    
    # 创建任务
    print("\n1. 创建任务:")
    task_id = "test_task_001"
    monitor.create_task(task_id, task_description="示例任务规划")
    time.sleep(0.5)
    
    # 模拟各阶段进度
    print("\n\n2. 模拟各阶段进度:")
    
    # 建模阶段
    monitor.update_layer_progress(
        task_id=task_id,
        phase=ProgressPhase.MODELING,
        layer_status=LayerStatus.IN_PROGRESS,
        progress=0.0,
        message="开始建模阶段"
    )
    time.sleep(0.3)
    
    monitor.update_layer_progress(
        task_id=task_id,
        phase=ProgressPhase.MODELING,
        layer_status=LayerStatus.IN_PROGRESS,
        progress=0.5,
        message="解析用户需求"
    )
    time.sleep(0.3)
    
    monitor.update_layer_progress(
        task_id=task_id,
        phase=ProgressPhase.MODELING,
        layer_status=LayerStatus.COMPLETED,
        progress=1.0,
        message="建模完成"
    )
    time.sleep(0.3)
    
    # 拓扑阶段
    monitor.update_layer_progress(
        task_id=task_id,
        phase=ProgressPhase.TOPOLOGY,
        layer_status=LayerStatus.IN_PROGRESS,
        progress=0.0,
        message="开始拓扑阶段"
    )
    time.sleep(0.3)
    
    monitor.update_layer_progress(
        task_id=task_id,
        phase=ProgressPhase.TOPOLOGY,
        layer_status=LayerStatus.IN_PROGRESS,
        progress=0.5,
        message="分解任务拓扑"
    )
    time.sleep(0.3)
    
    monitor.update_layer_progress(
        task_id=task_id,
        phase=ProgressPhase.TOPOLOGY,
        layer_status=LayerStatus.COMPLETED,
        progress=1.0,
        message="拓扑分解完成"
    )
    time.sleep(0.3)
    
    # 原子阶段
    monitor.update_layer_progress(
        task_id=task_id,
        phase=ProgressPhase.ATOMIC,
        layer_status=LayerStatus.IN_PROGRESS,
        progress=0.0,
        message="开始原子阶段"
    )
    time.sleep(0.3)
    
    monitor.update_layer_progress(
        task_id=task_id,
        phase=ProgressPhase.ATOMIC,
        layer_status=LayerStatus.COMPLETED,
        progress=1.0,
        message="原子拆分完成"
    )
    time.sleep(0.3)
    
    # 验证阶段
    monitor.update_layer_progress(
        task_id=task_id,
        phase=ProgressPhase.VALIDATION,
        layer_status=LayerStatus.IN_PROGRESS,
        progress=0.0,
        message="开始验证阶段"
    )
    time.sleep(0.3)
    
    monitor.update_layer_progress(
        task_id=task_id,
        phase=ProgressPhase.VALIDATION,
        layer_status=LayerStatus.COMPLETED,
        progress=1.0,
        message="验证完成"
    )
    time.sleep(0.3)
    
    # 完成任务
    print("\n\n3. 完成任务:")
    monitor.set_task_status(
        task_id=task_id,
        status=TaskStatus.COMPLETED,
        message="任务成功完成！"
    )
    time.sleep(0.2)
    
    # 获取统计
    print("\n\n4. 进度统计:")
    stats = monitor.get_statistics(task_id)
    if stats:
        print(f"   状态: {stats['status']}")
        print(f"   总进度: {stats['overall_progress'] * 100:.1f}%")
        print(f"   总更新: {stats['total_updates']}次")
        if stats['duration']:
            print(f"   总耗时: {stats['duration']:.2f}s")
        
        print("\n   各层进度:")
        for phase, layer_stat in stats['layer_progress'].items():
            print(f"     {phase}: {layer_stat['progress'] * 100:.0f}% - {layer_stat['status']}")
    
    print("\n" + "=" * 60)
    print("实时进度状态更新组件 - 示例完成")
    print("=" * 60)
