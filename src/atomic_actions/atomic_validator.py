"""
第三层：原子动作收敛层 - 原子校验引擎
基于第一性原理的AI Agent任务规划系统

核心功能：
- 单一职责原则自动校验
- 无副作用原则自动校验
- 幂等性原则自动校验
- 非原子动作自动识别
- 违规问题报告和建议
"""

from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum
import re

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from atomic_action_struct import (
    AtomicAction, AtomicActionQueue, AtomicActionStatus, AtomicActionType,
    AtomicCondition, ActionInput, ActionOutput, ActionConstraint,
    create_atomic_action
)


class IssueSeverity(Enum):
    """问题严重程度"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class IssueType(Enum):
    """问题类型"""
    MULTIPLE_RESPONSIBILITIES = "multiple_responsibilities"  # 多职责
    HAS_SIDE_EFFECTS = "has_side_effects"  # 有副作用
    NOT_IDEMPOTENT = "not_idempotent"  # 非幂等
    UNCLEAR_PURPOSE = "unclear_purpose"  # 目的不明确
    INSUFFICIENT_INPUT_OUTPUT = "insufficient_input_output"  # 输入输出不足
    TOO_COMPLEX = "too_complex"  # 过于复杂


@dataclass
class ValidationIssue:
    """校验问题"""
    action_id: str
    action_name: str
    issue_type: IssueType
    severity: IssueSeverity
    description: str
    suggestion: str = ""
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ValidationResult:
    """校验结果"""
    action: AtomicAction
    is_valid: bool
    issues: List[ValidationIssue]
    condition_results: Dict[AtomicCondition, bool]
    score: float  # 原子性评分 0-100
    suggestions: List[str]


class AtomicValidator:
    """
    原子校验引擎
    
    功能：
    - 三大原子判定条件自动校验
    - 非原子动作自动识别
    - 提供整改建议
    """
    
    def __init__(self):
        # 多职责检测关键词
        self.multi_responsibility_keywords = [
            "和", "与", "并且", "同时", "既...又", "一方面...另一方面",
            "以及", "包括", "包含", "完成", "执行并", "处理并且"
        ]
        
        # 副作用检测关键词
        self.side_effect_keywords = [
            "删除", "修改", "更新", "插入", "创建", "移除", "销毁",
            "写入", "保存", "发送", "发布", "触发", "通知", "报警",
            "改变", "变更", "替换", "覆盖", "追加", "删除掉", "覆盖掉"
        ]
        
        # 幂等性检测关键词（负面）
        self.non_idempotent_keywords = [
            "递增", "累加", "加1", "每次加", "计数", "计数器",
            "追加", "添加到", "插入到", "生成新", "创建新", "生成唯一"
        ]
        
        # 复杂动作关键词
        self.complex_action_keywords = [
            "流程", "系统", "模块", "功能", "完整", "全面", "综合",
            "多步骤", "分阶段", "依次", "逐个", "分别", "同时进行"
        ]
    
    def validate_atomic_action(
        self,
        action: AtomicAction
    ) -> ValidationResult:
        """
        校验单个原子动作
        
        Args:
            action: 待校验的原子动作
        
        Returns:
            ValidationResult: 校验结果
        """
        issues = []
        condition_results = {}
        
        # 1. 单一职责校验
        single_resp_valid = self._check_single_responsibility(action, issues)
        condition_results[AtomicCondition.SINGLE_RESPONSIBILITY] = single_resp_valid
        
        # 2. 无副作用校验
        side_effect_free = self._check_side_effect_free(action, issues)
        condition_results[AtomicCondition.SIDE_EFFECT_FREE] = side_effect_free
        
        # 3. 幂等性校验
        idempotent = self._check_idempotent(action, issues)
        condition_results[AtomicCondition.IDEMPOTENT] = idempotent
        
        # 4. 基础完整性校验
        self._check_basic_completeness(action, issues)
        
        # 5. 复杂度校验
        self._check_complexity(action, issues)
        
        # 计算得分
        score = self._calculate_score(condition_results, issues)
        
        is_valid = len([i for i in issues if i.severity in [IssueSeverity.ERROR, IssueSeverity.CRITICAL]]) == 0
        
        # 收集建议
        suggestions = [issue.suggestion for issue in issues if issue.suggestion]
        
        return ValidationResult(
            action=action,
            is_valid=is_valid,
            issues=issues,
            condition_results=condition_results,
            score=score,
            suggestions=suggestions
        )
    
    def validate_atomic_queue(
        self,
        queue: AtomicActionQueue
    ) -> List[ValidationResult]:
        """
        校验整个原子动作队列
        
        Args:
            queue: 原子动作队列
        
        Returns:
            List[ValidationResult]: 每个动作的校验结果
        """
        results = []
        
        for action in queue.actions:
            result = self.validate_atomic_action(action)
            results.append(result)
        
        return results
    
    def _check_single_responsibility(
        self,
        action: AtomicAction,
        issues: List[ValidationIssue]
    ) -> bool:
        """
        单一职责原则校验
        
        Returns:
            bool: 是否符合单一职责
        """
        text = f"{action.name} {action.description}"
        
        # 检测多职责关键词
        found_keywords = []
        for keyword in self.multi_responsibility_keywords:
            if keyword in text:
                found_keywords.append(keyword)
        
        if found_keywords:
            issue = ValidationIssue(
                action_id=action.action_id,
                action_name=action.name,
                issue_type=IssueType.MULTIPLE_RESPONSIBILITIES,
                severity=IssueSeverity.WARNING,
                description=f"发现多职责关键词: {', '.join(found_keywords)}",
                suggestion="建议将动作拆分为更小的单元，每个动作只负责一件事情"
            )
            issues.append(issue)
            return False
        
        # 检测名称长度（过长可能意味着多职责）
        if len(action.name) > 30:
            issue = ValidationIssue(
                action_id=action.action_id,
                action_name=action.name,
                issue_type=IssueType.UNCLEAR_PURPOSE,
                severity=IssueSeverity.INFO,
                description="动作名称过长，可能包含多个职责",
                suggestion="建议使用更简短、明确的名称"
            )
            issues.append(issue)
        
        return True
    
    def _check_side_effect_free(
        self,
        action: AtomicAction,
        issues: List[ValidationIssue]
    ) -> bool:
        """
        无副作用原则校验
        
        Returns:
            bool: 是否符合无副作用
        """
        # 注意：某些动作类型天生有副作用（DATA_WRITE等）
        # 但我们仍然要检查是否有过多副作用
        
        text = f"{action.name} {action.description}"
        
        found_keywords = []
        for keyword in self.side_effect_keywords:
            if keyword in text:
                found_keywords.append(keyword)
        
        if found_keywords:
            # 根据动作类型判断是否应该警告
            if action.action_type in [AtomicActionType.DATA_WRITE, AtomicActionType.FILE_IO]:
                # 写入类动作，副作用是预期的
                return True
            
            issue = ValidationIssue(
                action_id=action.action_id,
                action_name=action.name,
                issue_type=IssueType.HAS_SIDE_EFFECTS,
                severity=IssueSeverity.WARNING,
                description=f"发现可能有副作用的关键词: {', '.join(found_keywords)}",
                suggestion="建议明确声明副作用，或拆分出纯计算部分"
            )
            issues.append(issue)
            return False
        
        return True
    
    def _check_idempotent(
        self,
        action: AtomicAction,
        issues: List[ValidationIssue]
    ) -> bool:
        """
        幂等性原则校验
        
        Returns:
            bool: 是否符合幂等性
        """
        text = f"{action.name} {action.description}"
        
        found_keywords = []
        for keyword in self.non_idempotent_keywords:
            if keyword in text:
                found_keywords.append(keyword)
        
        if found_keywords:
            issue = ValidationIssue(
                action_id=action.action_id,
                action_name=action.name,
                issue_type=IssueType.NOT_IDEMPOTENT,
                severity=IssueSeverity.WARNING,
                description=f"发现非幂等关键词: {', '.join(found_keywords)}",
                suggestion="建议设计为幂等操作，或明确说明重复执行的影响"
            )
            issues.append(issue)
            return False
        
        return True
    
    def _check_basic_completeness(
        self,
        action: AtomicAction,
        issues: List[ValidationIssue]
    ):
        """
        基础完整性校验
        """
        # 检查是否有输入
        if not action.inputs:
            issue = ValidationIssue(
                action_id=action.action_id,
                action_name=action.name,
                issue_type=IssueType.INSUFFICIENT_INPUT_OUTPUT,
                severity=IssueSeverity.INFO,
                description="动作没有定义输入",
                suggestion="建议明确定义输入参数"
            )
            issues.append(issue)
        
        # 检查是否有输出
        if not action.outputs:
            issue = ValidationIssue(
                action_id=action.action_id,
                action_name=action.name,
                issue_type=IssueType.INSUFFICIENT_INPUT_OUTPUT,
                severity=IssueSeverity.INFO,
                description="动作没有定义输出",
                suggestion="建议明确定义输出结果"
            )
            issues.append(issue)
        
        # 检查描述是否清晰
        if len(action.description) < 10:
            issue = ValidationIssue(
                action_id=action.action_id,
                action_name=action.name,
                issue_type=IssueType.UNCLEAR_PURPOSE,
                severity=IssueSeverity.WARNING,
                description="动作描述过于简短",
                suggestion="建议提供更详细的功能描述"
            )
            issues.append(issue)
    
    def _check_complexity(
        self,
        action: AtomicAction,
        issues: List[ValidationIssue]
    ):
        """
        复杂度校验
        """
        text = f"{action.name} {action.description}"
        
        # 检测复杂关键词
        for keyword in self.complex_action_keywords:
            if keyword in text:
                issue = ValidationIssue(
                    action_id=action.action_id,
                    action_name=action.name,
                    issue_type=IssueType.TOO_COMPLEX,
                    severity=IssueSeverity.WARNING,
                    description=f"发现复杂动作关键词: {keyword}",
                    suggestion="建议拆分为多个更简单的原子动作"
                )
                issues.append(issue)
                break
        
        # 检查输入数量
        if len(action.inputs) > 5:
            issue = ValidationIssue(
                action_id=action.action_id,
                action_name=action.name,
                issue_type=IssueType.TOO_COMPLEX,
                severity=IssueSeverity.INFO,
                description=f"输入数量较多: {len(action.inputs)} 个",
                suggestion="建议考虑是否可以拆分为多个动作"
            )
            issues.append(issue)
    
    def _calculate_score(
        self,
        condition_results: Dict[AtomicCondition, bool],
        issues: List[ValidationIssue]
    ) -> float:
        """
        计算原子性评分
        
        Returns:
            float: 0-100的评分
        """
        score = 100
        
        # 条件权重
        condition_weights = {
            AtomicCondition.SINGLE_RESPONSIBILITY: 40,
            AtomicCondition.SIDE_EFFECT_FREE: 30,
            AtomicCondition.IDEMPOTENT: 30
        }
        
        # 减分条件
        for condition, satisfied in condition_results.items():
            if not satisfied:
                score -= condition_weights.get(condition, 20)
        
        # 问题减分
        for issue in issues:
            if issue.severity == IssueSeverity.CRITICAL:
                score -= 30
            elif issue.severity == IssueSeverity.ERROR:
                score -= 15
            elif issue.severity == IssueSeverity.WARNING:
                score -= 5
        
        return max(0, min(100, score))
    
    def get_validation_summary(
        self,
        results: List[ValidationResult]
    ) -> Dict[str, Any]:
        """
        获取校验摘要
        
        Args:
            results: 校验结果列表
        
        Returns:
            Dict: 摘要信息
        """
        total = len(results)
        valid_count = sum(1 for r in results if r.is_valid)
        avg_score = sum(r.score for r in results) / total if total > 0 else 0
        
        all_issues = []
        for result in results:
            all_issues.extend(result.issues)
        
        issue_count_by_type = {}
        for issue in all_issues:
            type_name = issue.issue_type.value
            if type_name not in issue_count_by_type:
                issue_count_by_type[type_name] = 0
            issue_count_by_type[type_name] += 1
        
        return {
            "total_actions": total,
            "valid_actions": valid_count,
            "invalid_actions": total - valid_count,
            "average_score": avg_score,
            "total_issues": len(all_issues),
            "issues_by_type": issue_count_by_type,
            "passed_conditions": {
                cond.value: sum(1 for r in results if r.condition_results.get(cond, False))
                for cond in AtomicCondition
            }
        }


# 便捷函数
def validate_atomic_actions(
    actions: List[AtomicAction]
) -> List[ValidationResult]:
    """
    便捷函数：校验多个原子动作
    
    Args:
        actions: 原子动作列表
    
    Returns:
        List[ValidationResult]: 校验结果列表
    """
    validator = AtomicValidator()
    results = []
    
    for action in actions:
        result = validator.validate_atomic_action(action)
        results.append(result)
    
    return results


def validate_queue_and_summarize(
    queue: AtomicActionQueue
) -> Tuple[List[ValidationResult], Dict[str, Any]]:
    """
    便捷函数：校验队列并获取摘要
    
    Args:
        queue: 原子动作队列
    
    Returns:
        (results, summary): 校验结果和摘要
    """
    validator = AtomicValidator()
    results = validator.validate_atomic_queue(queue)
    summary = validator.get_validation_summary(results)
    return results, summary
