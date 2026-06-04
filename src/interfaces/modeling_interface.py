"""
第一层接口封装 - 任务归一建模层接口
基于第一性原理的AI Agent任务规划系统

核心功能：
- 定义建模层标准接口
- 封装所有建模操作
- 对外提供统一调用方式
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field

from task_modeling.task_struct import Task, Target, Condition, Boundary, EndRule
from task_modeling.parser import parse_task_from_description
from task_modeling.target_extractor import extract_target
from task_modeling.condition_extractor import extract_condition
from task_modeling.boundary_extractor import extract_boundary
from task_modeling.end_rule_extractor import extract_end_rule
from task_modeling.task_validator import validate_task
from task_modeling.task_interceptor import intercept_task


@dataclass
class ModelingResult:
    """建模结果"""
    success: bool
    task: Optional[Task] = None
    error_message: str = ""
    processing_records: List[Dict[str, Any]] = field(default_factory=list)


class ModelingInterface:
    """
    任务归一建模层接口
    
    功能：
    - 封装所有建模操作
    - 提供统一调用入口
    - 实现错误处理和日志记录
    """
    
    def __init__(self):
        """初始化建模接口"""
        pass
    
    def parse_requirement(self, requirement: str) -> ModelingResult:
        """
        解析用户需求
        
        Args:
            requirement: 用户需求描述
            
        Returns:
            ModelingResult: 建模结果
        """
        try:
            # 尝试使用解析器
            parsed_task, warnings = parse_task_from_description(requirement)
            
            if parsed_task.target:
                return ModelingResult(
                    success=True,
                    task=parsed_task,
                    processing_records=[{"step": "parse", "warnings": warnings}]
                )
        except Exception:
            pass
        
        # 备用方案：手动提取
        try:
            target, _ = extract_target(requirement)
            condition, _ = extract_condition(requirement)
            boundary = extract_boundary(requirement)
            end_rule = extract_end_rule(requirement)
            
            task = Task(
                id="",
                target=target,
                condition=condition,
                boundary=boundary,
                end_rule=end_rule
            )
            
            return ModelingResult(
                success=True,
                task=task,
                processing_records=[{"step": "manual_extract"}]
            )
        except Exception as e:
            return ModelingResult(
                success=False,
                error_message=str(e)
            )
    
    def validate_task(self, task: Task) -> Tuple[bool, str]:
        """
        验证任务合法性
        
        Args:
            task: 任务对象
            
        Returns:
            Tuple[bool, str]: (是否合法, 错误信息)
        """
        is_valid, errors = validate_task(task)
        if is_valid:
            return True, ""
        return False, ", ".join(errors)
    
    def intercept_invalid_task(self, errors: List[str], task_id: Optional[str] = None) -> Dict[str, Any]:
        """
        拦截无效任务
        
        Args:
            errors: 错误列表
            task_id: 任务ID
            
        Returns:
            Dict[str, Any]: 拦截结果
        """
        return intercept_task(errors, task_id)
