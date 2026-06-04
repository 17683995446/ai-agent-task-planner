"""
系统调度接口封装 - 统一入口接口
基于第一性原理的AI Agent任务规划系统

核心功能：
- 定义系统标准接口
- 封装四层架构调用
- 对外提供统一调用方式
- 实现彻底解耦
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from .modeling_interface import ModelingInterface, ModelingResult
from .topology_interface import TopologyInterface, TopologyResult
from .atomic_interface import AtomicInterface, AtomicResult
from .validation_interface import ValidationInterface, ValidationResult

from validation.trace_logger import get_trace_logger, LayerType, OperationType
from validation.progress_monitor import get_progress_monitor, TaskStatus, LayerStatus, ProgressPhase
from validation.exception_handler import get_exception_handler, handle_exception


@dataclass
class OrchestratorResult:
    """调度结果"""
    success: bool
    task_id: str
    modeling_result: Optional[ModelingResult] = None
    topology_result: Optional[TopologyResult] = None
    atomic_result: Optional[AtomicResult] = None
    validation_result: Optional[ValidationResult] = None
    error_message: str = ""
    execution_time: float = 0.0


class OrchestratorInterface:
    """
    系统调度接口
    
    功能：
    - 统一入口、统一调度
    - 封装四层架构调用
    - 实现彻底解耦
    - 提供完整监控和日志
    """
    
    def __init__(self):
        """初始化调度接口"""
        self.modeling = ModelingInterface()
        self.topology = TopologyInterface()
        self.atomic = AtomicInterface()
        self.validation = ValidationInterface()
        self.tracer = get_trace_logger()
        self.progress = get_progress_monitor()
        self.exception_handler = get_exception_handler()
    
    def plan_task(self, requirement: str, task_id: Optional[str] = None) -> OrchestratorResult:
        """
        规划任务 - 统一入口
        
        Args:
            requirement: 用户需求描述
            task_id: 任务ID（可选）
            
        Returns:
            OrchestratorResult: 调度结果
        """
        import time
        import uuid
        
        start_time = time.time()
        task_id = task_id or str(uuid.uuid4())
        
        # 创建追踪和进度
        self.tracer.create_task(requirement, {"requirement": requirement})
        self.progress.create_task(task_id, requirement)
        
        result = OrchestratorResult(
            success=False,
            task_id=task_id
        )
        
        try:
            # ========== 第一层：任务归一建模层 ==========
            self.progress.update_layer_progress(
                task_id=task_id,
                phase=ProgressPhase.MODELING,
                layer_status=LayerStatus.IN_PROGRESS,
                progress=0.0,
                message="开始任务建模"
            )
            
            modeling_result = self.modeling.parse_requirement(requirement)
            result.modeling_result = modeling_result
            
            if not modeling_result.success or not modeling_result.task:
                result.error_message = modeling_result.error_message or "建模失败"
                return result
            
            # 验证任务
            is_valid, error_msg = self.modeling.validate_task(modeling_result.task)
            if not is_valid:
                result.error_message = error_msg
                return result
            
            self.progress.update_layer_progress(
                task_id=task_id,
                phase=ProgressPhase.MODELING,
                layer_status=LayerStatus.COMPLETED,
                progress=1.0,
                message="任务建模完成"
            )
            
            # ========== 第二层：拓扑依赖拆解层 ==========
            self.progress.update_layer_progress(
                task_id=task_id,
                phase=ProgressPhase.TOPOLOGY,
                layer_status=LayerStatus.IN_PROGRESS,
                progress=0.0,
                message="开始拓扑拆解"
            )
            
            topology_result = self.topology.decompose_task(modeling_result.task)
            result.topology_result = topology_result
            
            if not topology_result.success:
                result.error_message = topology_result.error_message or "拓扑拆解失败"
                return result
            
            self.progress.update_layer_progress(
                task_id=task_id,
                phase=ProgressPhase.TOPOLOGY,
                layer_status=LayerStatus.COMPLETED,
                progress=1.0,
                message="拓扑拆解完成"
            )
            
            # ========== 第三层：原子动作收敛层 ==========
            self.progress.update_layer_progress(
                task_id=task_id,
                phase=ProgressPhase.ATOMIC,
                layer_status=LayerStatus.IN_PROGRESS,
                progress=0.0,
                message="开始原子拆分"
            )
            
            atomic_result = self.atomic.split_to_atomic(topology_result.subtasks)
            result.atomic_result = atomic_result
            
            if not atomic_result.success:
                result.error_message = atomic_result.error_message or "原子拆分失败"
                return result
            
            self.progress.update_layer_progress(
                task_id=task_id,
                phase=ProgressPhase.ATOMIC,
                layer_status=LayerStatus.COMPLETED,
                progress=1.0,
                message="原子拆分完成"
            )
            
            # ========== 第四层：分段校验收敛层 ==========
            self.progress.update_layer_progress(
                task_id=task_id,
                phase=ProgressPhase.VALIDATION,
                layer_status=LayerStatus.IN_PROGRESS,
                progress=0.0,
                message="开始验证收敛"
            )
            
            validation_result = self.validation.validate_plan(
                modeling_result.task,
                atomic_result.actions
            )
            result.validation_result = validation_result
            
            self.progress.update_layer_progress(
                task_id=task_id,
                phase=ProgressPhase.VALIDATION,
                layer_status=LayerStatus.COMPLETED,
                progress=1.0,
                message="验证收敛完成"
            )
            
            # 完成
            result.success = True
            result.execution_time = time.time() - start_time
            
            self.tracer.complete_task(
                task_id=task_id,
                success=True,
                result={
                    "subtasks_count": len(topology_result.subtasks),
                    "atomic_actions_count": len(atomic_result.actions),
                    "validation_passed": validation_result.is_valid if validation_result else False
                }
            )
            self.progress.set_task_status(
                task_id=task_id,
                status=TaskStatus.COMPLETED,
                message="任务规划完成"
            )
            
        except Exception as e:
            result.error_message = str(e)
            result.execution_time = time.time() - start_time
            
            handle_exception(e, task_id=task_id)
            
            self.tracer.complete_task(
                task_id=task_id,
                success=False,
                result={"error": str(e)}
            )
            self.progress.set_task_status(
                task_id=task_id,
                status=TaskStatus.FAILED,
                message=str(e)
            )
        
        return result
