"""
任务合法性校验模块
基于第一性原理的AI Agent任务规划系统
"""

from typing import List, Dict, Any, Tuple
from task_struct import Task, Target, Condition, Boundary, EndRule


class TaskValidationError(Exception):
    """任务合法性校验异常"""
    def __init__(self, errors: List[str]):
        self.errors = errors
        super().__init__(f"任务校验失败，共{len(errors)}个错误: {', '.join(errors)}")


class TaskValidator:
    """
    任务合法性校验器
    功能：对Task四元组进行完整的合法性校验
    """
    
    def __init__(self):
        """初始化校验器"""
        pass
    
    def validate(self, task: Task) -> Tuple[bool, List[str]]:
        """
        校验任务合法性
        
        Args:
            task: 待校验的Task对象
            
        Returns:
            Tuple[bool, List[str]]: (是否合法, 错误列表)
        """
        errors = []
        
        # 1. 校验Task基本信息
        errors.extend(self._validate_task_basic(task))
        
        # 2. 校验Target
        errors.extend(self._validate_target(task.target))
        
        # 3. 校验Condition
        errors.extend(self._validate_condition(task.condition))
        
        # 4. 校验Boundary
        errors.extend(self._validate_boundary(task.boundary))
        
        # 5. 校验EndRule
        errors.extend(self._validate_end_rule(task.end_rule))
        
        return len(errors) == 0, errors
    
    def validate_or_raise(self, task: Task) -> None:
        """
        校验任务合法性，如果不合法则抛出异常
        
        Args:
            task: 待校验的Task对象
            
        Raises:
            TaskValidationError: 当任务不合法时抛出
        """
        is_valid, errors = self.validate(task)
        if not is_valid:
            raise TaskValidationError(errors)
    
    def _validate_task_basic(self, task: Task) -> List[str]:
        """校验Task基本信息"""
        errors = []
        
        if not task.id or len(task.id.strip()) == 0:
            errors.append("任务ID不能为空")
        
        if not isinstance(task.status.value, str):
            errors.append("任务状态无效")
        
        return errors
    
    def _validate_target(self, target: Target) -> List[str]:
        """校验Target"""
        errors = []
        
        # 检查ID
        if not target.id or len(target.id.strip()) == 0:
            errors.append("Target的ID不能为空")
        
        # 检查描述
        if not target.description or len(target.description.strip()) == 0:
            errors.append("Target的描述不能为空")
        
        if len(target.description) > 500:
            errors.append("Target的描述过长（最大500字符）")
        
        # 检查可衡量标准
        if not target.measurable_criteria or len(target.measurable_criteria) == 0:
            errors.append("Target至少需要一个可衡量标准(measurable_criteria)")
        
        # 检查优先级范围
        if target.priority < 1 or target.priority > 10:
            errors.append("Target的优先级必须在1-10之间")
        
        # 检查每个可衡量标准
        for idx, criterion in enumerate(target.measurable_criteria):
            if not criterion.id:
                errors.append(f"可衡量标准[{idx}]的ID不能为空")
            if not criterion.description:
                errors.append(f"可衡量标准[{idx}]的描述不能为空")
            if criterion.type not in ['boolean', 'numeric', 'qualitative']:
                errors.append(f"可衡量标准[{idx}]的类型无效（必须为boolean/numeric/qualitative）")
            if criterion.type == 'numeric' and criterion.threshold is None:
                errors.append(f"可衡量标准[{idx}]为数值类型但未设置阈值")
        
        return errors
    
    def _validate_condition(self, condition: Condition) -> List[str]:
        """校验Condition"""
        errors = []
        
        # 检查逻辑运算符
        if condition.logical_operator not in ['AND', 'OR']:
            errors.append("Condition的logical_operator必须为AND或OR")
        
        # 检查条件列表
        if not condition.conditions or len(condition.conditions) == 0:
            # 前置条件可以为空，但必须有默认值
            errors.append("Condition至少需要一个条件或明确标注无前置条件")
        
        # 检查每个条件项
        for idx, item in enumerate(condition.conditions):
            if not item.id:
                errors.append(f"前置条件[{idx}]的ID不能为空")
            if not item.description:
                errors.append(f"前置条件[{idx}]的描述不能为空")
            if item.type not in ['existence', 'value', 'state']:
                errors.append(f"前置条件[{idx}]的类型无效（必须为existence/value/state）")
            if not item.check_rule:
                errors.append(f"前置条件[{idx}]必须设置check_rule")
        
        return errors
    
    def _validate_boundary(self, boundary: Boundary) -> List[str]:
        """校验Boundary"""
        errors = []
        
        # 检查Scope
        if not boundary.scope:
            errors.append("Boundary的scope不能为空")
        else:
            if not isinstance(boundary.scope.inclusions, list):
                errors.append("Boundary.scope.inclusions必须是列表")
            if not isinstance(boundary.scope.exclusions, list):
                errors.append("Boundary.scope.exclusions必须是列表")
        
        # 检查Resources
        if not boundary.resources:
            errors.append("Boundary的resources不能为空")
        else:
            resources = boundary.resources
            if resources.max_time_seconds is not None and resources.max_time_seconds <= 0:
                errors.append("Boundary.resources.max_time_seconds必须大于0")
            if resources.max_cost is not None and resources.max_cost < 0:
                errors.append("Boundary.resources.max_cost不能为负数")
            if resources.max_iterations is not None and resources.max_iterations <= 0:
                errors.append("Boundary.resources.max_iterations必须大于0")
        
        # 检查Quality（可选）
        if boundary.quality:
            quality = boundary.quality
            if quality.min_accuracy is not None:
                if quality.min_accuracy < 0 or quality.min_accuracy > 1:
                    errors.append("Boundary.quality.min_accuracy必须在0-1之间")
            if quality.max_error_rate is not None:
                if quality.max_error_rate < 0 or quality.max_error_rate > 1:
                    errors.append("Boundary.quality.max_error_rate必须在0-1之间")
            if not isinstance(quality.other_constraints, list):
                errors.append("Boundary.quality.other_constraints必须是列表")
        
        return errors
    
    def _validate_end_rule(self, end_rule: EndRule) -> List[str]:
        """校验EndRule"""
        errors = []
        
        # 检查成功条件列表
        if not end_rule.success_conditions or len(end_rule.success_conditions) == 0:
            errors.append("EndRule至少需要一个成功条件")
        
        # 检查每个成功条件
        for idx, cond in enumerate(end_rule.success_conditions):
            if not cond.id:
                errors.append(f"成功条件[{idx}]的ID不能为空")
            if not cond.description:
                errors.append(f"成功条件[{idx}]的描述不能为空")
            if not cond.check_rule:
                errors.append(f"成功条件[{idx}]必须设置check_rule")
        
        # 检查失败条件（可选但推荐）
        if not end_rule.failure_conditions or len(end_rule.failure_conditions) == 0:
            errors.append("EndRule建议至少有一个失败条件")
        
        # 检查每个失败条件
        for idx, cond in enumerate(end_rule.failure_conditions):
            if not cond.id:
                errors.append(f"失败条件[{idx}]的ID不能为空")
            if not cond.description:
                errors.append(f"失败条件[{idx}]的描述不能为空")
            if not cond.check_rule:
                errors.append(f"失败条件[{idx}]必须设置check_rule")
            if cond.priority < 1:
                errors.append(f"失败条件[{idx}]的优先级必须>=1")
        
        return errors


# 便捷函数
def validate_task(task: Task) -> Tuple[bool, List[str]]:
    """
    便捷函数：校验任务合法性
    
    Args:
        task: 待校验的Task对象
        
    Returns:
        Tuple[bool, List[str]]: (是否合法, 错误列表)
    """
    validator = TaskValidator()
    return validator.validate(task)


def validate_task_or_raise(task: Task) -> None:
    """
    便捷函数：校验任务合法性，如果不合法则抛出异常
    
    Args:
        task: 待校验的Task对象
        
    Raises:
        TaskValidationError: 当任务不合法时抛出
    """
    validator = TaskValidator()
    validator.validate_or_raise(task)
