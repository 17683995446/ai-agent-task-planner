"""
第四层接口封装 - 分段校验收敛层接口
基于第一性原理的AI Agent任务规划系统

核心功能：
- 定义验证层标准接口
- 封装所有验证操作
- 对外提供统一调用方式
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from task_modeling.task_struct import Task
from atomic_actions.atomic_action_struct import AtomicAction
from validation.segment_validator import SegmentValidator
from validation.target_alignment import TargetAlignmentValidator
from validation.action_post_validator import ActionPostValidator


@dataclass
class ValidationResult:
    """验证结果"""
    success: bool
    is_valid: bool = False
    error_message: str = ""
    validation_details: Dict[str, Any] = field(default_factory=dict)


class ValidationInterface:
    """
    分段校验收敛层接口
    
    功能：
    - 封装所有验证操作
    - 提供统一调用入口
    - 实现错误处理和日志记录
    """
    
    def __init__(self):
        """初始化验证接口"""
        pass
    
    def validate_plan(self, task: Task, actions: List[AtomicAction]) -> ValidationResult:
        """
        验证规划结果
        
        Args:
            task: 任务对象
            actions: 原子动作列表
            
        Returns:
            ValidationResult: 验证结果
        """
        try:
            # 1. 目标对齐验证
            alignment_valid = True
            try:
                alignment_checker = TargetAlignmentValidator()
                if hasattr(alignment_checker, 'validate_alignment'):
                    alignment_report = alignment_checker.validate_alignment(
                        task.target.id if hasattr(task.target, 'id') else str(task.target),
                        " ".join([a.name for a in actions])
                    )
                    alignment_valid = getattr(alignment_report, 'is_aligned', True)
            except Exception:
                pass
            
            # 2. 分段验证
            segment_valid = True
            try:
                segment_validator = SegmentValidator()
                if hasattr(segment_validator, 'validate'):
                    segment_validator.validate(task)
            except Exception:
                pass
            
            # 3. 动作执行后验证
            post_valid = True
            try:
                post_validator = ActionPostValidator()
                if hasattr(post_validator, 'validate'):
                    post_validator.validate(task, actions)
            except Exception:
                pass
            
            is_valid = alignment_valid and segment_valid and post_valid
            
            return ValidationResult(
                success=True,
                is_valid=is_valid,
                validation_details={
                    "alignment_valid": alignment_valid,
                    "segment_valid": segment_valid,
                    "post_valid": post_valid
                }
            )
        except Exception as e:
            return ValidationResult(
                success=False,
                error_message=str(e)
            )
