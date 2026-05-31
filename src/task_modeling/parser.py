"""
用户需求统一解析入口
基于第一性原理的AI Agent任务规划系统
"""

import re
import uuid
from typing import Dict, Any, Tuple, Optional
from .task_struct import (
    Task, Target, Condition, Boundary, EndRule,
    MeasurableCriterion, ConditionItem,
    ScopeBoundary, ResourceBoundary, QualityBoundary,
    SuccessCondition, FailureCondition
)


class RequirementsParseError(Exception):
    """需求解析错误异常"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "message": self.message,
            "details": self.details
        }


class TaskRequirementsParser:
    """用户需求统一解析器"""
    
    def __init__(self):
        """初始化解析器"""
        self.parsing_rules = self._init_parsing_rules()
    
    def _init_parsing_rules(self) -> Dict[str, Any]:
        """初始化解析规则"""
        return {
            "vague_words": ["大概", "尽量", "可能", "合适", "适当", "好的", "好的"],
            "conjunction_words": ["和", "与", "以及", "同时", "并且", "然后"],
            "condition_keywords": ["需要", "前提", "必须", "依赖", "需要先"],
            "boundary_keywords": ["不超过", "最多", "至少", "范围", "边界"],
            "time_keywords": ["分钟", "小时", "秒", "天内", "周内", "月内"],
            "quality_keywords": ["准确率", "质量", "精度", "误差"]
        }
    
    def parse(self, description: str) -> Task:
        """
        解析用户需求，生成Task四元组
        
        Args:
            description: 用户自然语言描述的需求
            
        Returns:
            Task: 标准化的Task四元组
            
        Raises:
            RequirementsParseError: 解析失败时抛出
        """
        if not description or not description.strip():
            raise RequirementsParseError(
                "需求描述不能为空",
                {"field": "description", "value": description}
            )
        
        cleaned_description = description.strip()
        
        issues = self._detect_issues(cleaned_description)
        if issues:
            raise RequirementsParseError(
                "需求描述存在问题",
                {"issues": issues}
            )
        
        target = self._extract_target(cleaned_description)
        condition = self._extract_condition(cleaned_description)
        boundary = self._extract_boundary(cleaned_description)
        end_rule = self._extract_end_rule(cleaned_description, target)
        
        task_id = f"TASK-{uuid.uuid4().hex[:12].upper()}"
        
        return Task(
            id=task_id,
            target=target,
            condition=condition,
            boundary=boundary,
            end_rule=end_rule
        )
    
    def _detect_issues(self, description: str) -> list:
        """
        检测需求描述中的问题
        
        Args:
            description: 需求描述
            
        Returns:
            list: 问题列表，空列表表示无问题
        """
        issues = []
        
        for vague_word in self.parsing_rules["vague_words"]:
            if vague_word in description:
                issues.append({
                    "type": "vague",
                    "word": vague_word,
                    "suggestion": f"建议将模糊词「{vague_word}」替换为具体描述"
                })
        
        multi_targets = self._check_multi_targets(description)
        if multi_targets:
            issues.append({
                "type": "multi_targets",
                "description": "检测到多个目标",
                "suggestion": "建议将复合目标拆分为多个独立任务"
            })
        
        return issues
    
    def _check_multi_targets(self, description: str) -> bool:
        """
        检查是否存在多个目标
        
        Args:
            description: 需求描述
            
        Returns:
            bool: True表示存在多个目标
        """
        for conjunction in self.parsing_rules["conjunction_words"]:
            pattern = rf'{conjunction}'.join([r'.+?' for _ in range(2)])
            if re.search(pattern, description):
                return True
        
        target_verbs = ["生成", "创建", "完成", "制作", "编写", "分析", "处理"]
        verb_count = sum(1 for verb in target_verbs if verb in description)
        
        return verb_count > 1
    
    def _extract_target(self, description: str) -> Target:
        """
        提取目标信息
        
        Args:
            description: 需求描述
            
        Returns:
            Target: 目标对象
        """
        clean_description = description
        for vague_word in self.parsing_rules["vague_words"]:
            clean_description = clean_description.replace(vague_word, "")
        
        clean_description = re.sub(r'\s+', ' ', clean_description).strip()
        
        target_id = f"T-{uuid.uuid4().hex[:8].upper()}"
        
        measurable_criteria = []
        
        if "页" in description:
            match = re.search(r'(\d+)\s*页', description)
            if match:
                page_count = int(match.group(1))
                measurable_criteria.append(MeasurableCriterion(
                    id=f"MC-{uuid.uuid4().hex[:6].upper()}",
                    description=f"报告页数>={page_count}页",
                    type="numeric",
                    threshold=page_count,
                    unit="页"
                ))
        
        if any(kw in description for kw in ["数据", "信息", "内容"]):
            measurable_criteria.append(MeasurableCriterion(
                id=f"MC-{uuid.uuid4().hex[:6].upper()}",
                description="包含完整必要数据",
                type="boolean",
                threshold=True
            ))
        
        if len(measurable_criteria) == 0:
            measurable_criteria.append(MeasurableCriterion(
                id=f"MC-{uuid.uuid4().hex[:6].upper()}",
                description="任务完成",
                type="boolean",
                threshold=True
            ))
        
        return Target(
            id=target_id,
            description=clean_description,
            measurable_criteria=measurable_criteria,
            priority=5
        )
    
    def _extract_condition(self, description: str) -> Condition:
        """
        提取前置条件
        
        Args:
            description: 需求描述
            
        Returns:
            Condition: 前置条件对象
        """
        conditions = []
        condition_keywords = self.parsing_rules["condition_keywords"]
        
        for keyword in condition_keywords:
            if keyword in description:
                pattern = rf'{keyword}([^,，。]+)'
                matches = re.findall(pattern, description)
                for i, match in enumerate(matches):
                    conditions.append(ConditionItem(
                        id=f"C-{uuid.uuid4().hex[:6].upper()}",
                        description=f"需要: {match.strip()}",
                        type="existence",
                        check_rule=f"check_condition('{match.strip()}')",
                        required=True
                    ))
        
        if not conditions:
            conditions.append(ConditionItem(
                id=f"C-{uuid.uuid4().hex[:6].upper()}",
                description="任务开始执行",
                type="state",
                check_rule="True",
                required=False
            ))
        
        return Condition(
            conditions=conditions,
            logical_operator="AND"
        )
    
    def _extract_boundary(self, description: str) -> Boundary:
        """
        提取边界约束
        
        Args:
            description: 需求描述
            
        Returns:
            Boundary: 边界约束对象
        """
        inclusions = []
        exclusions = []
        
        if "范围" in description:
            match = re.search(r'范围[是为：:]([^,，。]+)', description)
            if match:
                inclusions.append(match.group(1).strip())
        
        time_seconds = None
        for time_kw in self.parsing_rules["time_keywords"]:
            if time_kw in description:
                match = re.search(rf'(\d+)\s*{time_kw}', description)
                if match:
                    time_value = int(match.group(1))
                    if time_kw == "秒":
                        time_seconds = time_value
                    elif time_kw == "分钟":
                        time_seconds = time_value * 60
                    elif time_kw == "小时":
                        time_seconds = time_value * 3600
                    break
        
        if not time_seconds:
            time_seconds = 3600
        
        return Boundary(
            scope=ScopeBoundary(
                inclusions=inclusions if inclusions else ["全部"],
                exclusions=exclusions
            ),
            resources=ResourceBoundary(
                max_time_seconds=time_seconds,
                max_cost=None,
                max_iterations=10
            ),
            quality=QualityBoundary(
                min_accuracy=0.9,
                max_error_rate=0.1
            )
        )
    
    def _extract_end_rule(self, description: str, target: Target) -> EndRule:
        """
        提取终止规则
        
        Args:
            description: 需求描述
            target: 目标对象
            
        Returns:
            EndRule: 终止规则对象
        """
        success_conditions = []
        
        for criterion in target.measurable_criteria:
            success_conditions.append(SuccessCondition(
                id=f"SC-{uuid.uuid4().hex[:6].upper()}",
                description=criterion.description,
                check_rule=f"check_measurable('{criterion.id}')"
            ))
        
        failure_conditions = [
            FailureCondition(
                id=f"FC-{uuid.uuid4().hex[:6].upper()}",
                description="执行超时",
                check_rule="elapsed_time() > max_time_seconds",
                priority=1
            ),
            FailureCondition(
                id=f"FC-{uuid.uuid4().hex[:6].upper()}",
                description="超过最大迭代次数",
                check_rule="iteration_count() >= max_iterations",
                priority=2
            ),
            FailureCondition(
                id=f"FC-{uuid.uuid4().hex[:6].upper()}",
                description="连续错误超过3次",
                check_rule="consecutive_errors() >= 3",
                priority=3
            )
        ]
        
        evaluation_logic = "success: (" + " AND ".join([f"SC-{i+1}" for i in range(len(success_conditions))]) + "); "
        evaluation_logic += "failure: (FC-1 OR FC-2 OR FC-3)"
        
        return EndRule(
            success_conditions=success_conditions,
            failure_conditions=failure_conditions,
            evaluation_logic=evaluation_logic
        )


def parse_task_from_description(description: str) -> Tuple[Task, list]:
    """
    从用户描述解析Task的便捷函数
    
    Args:
        description: 用户自然语言描述
        
    Returns:
        Tuple[Task, list]: (解析的Task, 警告列表)
    """
    parser = TaskRequirementsParser()
    
    warnings = []
    
    try:
        task = parser.parse(description)
        return task, warnings
    except RequirementsParseError as e:
        warnings.append(e.to_dict())
        
        cleaned = description
        for vague_word in ["大概", "尽量", "可能", "合适"]:
            cleaned = cleaned.replace(vague_word, "")
        
        try:
            task = parser.parse(cleaned)
            warnings.append({
                "type": "auto_fix",
                "message": "已自动修复模糊描述",
                "original": description,
                "fixed": cleaned
            })
            return task, warnings
        except Exception:
            raise e


def create_parser() -> TaskRequirementsParser:
    """
    创建需求解析器的工厂函数
    
    Returns:
        TaskRequirementsParser: 配置好的解析器实例
    """
    return TaskRequirementsParser()
