"""
第三层：原子动作收敛层 - 动作净化单元
基于第一性原理的AI Agent任务规划系统

核心功能：
- 模糊动作识别与标准化
- 多职责动作检测与拆分建议
- 动作去重与合并
- 动作质量评分与优化建议
"""

import re
import uuid
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum
from collections import defaultdict

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from atomic_action_struct import (
    AtomicAction, AtomicActionQueue, AtomicActionType,
    AtomicCondition, AtomicActionStatus, create_atomic_action
)
from atomic_validator import AtomicValidator, ValidationResult


class PurificationLevel(Enum):
    """净化级别"""
    BASIC = "basic"              # 基础净化（去重、命名规范）
    STANDARD = "standard"        # 标准净化（模糊识别、多职责检测）
    ADVANCED = "advanced"        # 高级净化（深度分析、优化建议）


class IssueCategory(Enum):
    """问题类别"""
    VAGUE_NAME = "vague_name"                    # 模糊命名
    AMBIGUOUS_DESCRIPTION = "ambiguous_desc"    # 描述模糊
    MULTIPLE_RESPONSIBILITIES = "multi_resp"    # 多职责
    DUPLICATE_ACTION = "duplicate"               # 重复动作
    MISSING_INPUT_OUTPUT = "missing_io"          # 缺少输入输出
    INCONSISTENT_NAMING = "inconsistent_naming"  # 命名不一致
    LOW_ATOMICITY_SCORE = "low_score"            # 原子性评分低


@dataclass
class PurificationIssue:
    """净化问题"""
    action_id: str
    action_name: str
    category: IssueCategory
    severity: int  # 1-5，5最严重
    description: str
    suggestion: str
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class PurificationResult:
    """净化结果"""
    original_queue: AtomicActionQueue
    purified_queue: AtomicActionQueue
    issues: List[PurificationIssue]
    improvements: Dict[str, Any]
    quality_score_before: float
    quality_score_after: float


@dataclass
class ActionSimilarity:
    """动作相似度"""
    action1_id: str
    action2_id: str
    similarity_score: float  # 0-1
    reason: str


class ActionPurifier:
    """
    动作净化单元
    
    功能：
    - 模糊动作识别与标准化
    - 多职责动作检测
    - 重复动作去重
    - 动作质量优化
    """

    def __init__(self):
        self.validator = AtomicValidator()
        
        # 模糊词汇列表
        self.vague_words = {
            "处理", "搞定", "做", "弄", "搞", "干", "操作", "执行",
            "相关", "有关", "一些", "某些", "某个", "各种", "多个",
            "等等", "之类", "等", " stuff", "things", "something",
            "manage", "handle", "process", "do"
        }
        
        # 多职责指示词
        self.multi_resp_indicators = [
            "和", "与", "及", "以及", "并且", "同时", "既...又",
            "一方面...另一方面", "包括", "包含", "以及", "plus",
            "and", "&", "also", "together", "both", "while"
        ]
        
        # 标准化命名映射
        self.naming_standards = {
            "读取": ["读", "获取", "加载", "load", "read", "fetch", "get"],
            "写入": ["写", "保存", "存储", "save", "write", "store"],
            "更新": ["修改", "编辑", "update", "edit", "modify"],
            "删除": ["移除", "remove", "delete", "destroy"],
            "验证": ["检查", "校验", "check", "validate", "verify"],
            "转换": ["处理", "transform", "convert", "process"],
            "计算": ["算", "compute", "calculate"],
            "发送": ["发", "send", "dispatch"],
            "接收": ["收", "receive", "accept"]
        }

    def purify_queue(
        self,
        queue: AtomicActionQueue,
        level: PurificationLevel = PurificationLevel.STANDARD
    ) -> PurificationResult:
        """
        净化原子动作队列
        
        Args:
            queue: 原始队列
            level: 净化级别
            
        Returns:
            PurificationResult: 净化结果
        """
        issues = []
        score_before = self._calculate_queue_quality_score(queue)
        
        # 创建副本
        purified_queue = AtomicActionQueue(
            queue_id=f"purified_{queue.queue_id}",
            name=f"{queue.name} (已净化)",
            metadata={**queue.metadata, "purification_level": level.value}
        )
        
        # 步骤1：分析问题
        issues.extend(self._detect_duplicate_actions(queue))
        issues.extend(self._detect_vague_actions(queue))
        
        if level in [PurificationLevel.STANDARD, PurificationLevel.ADVANCED]:
            issues.extend(self._detect_multi_resp_actions(queue))
            issues.extend(self._detect_missing_io(queue))
        
        if level == PurificationLevel.ADVANCED:
            issues.extend(self._detect_inconsistent_naming(queue))
        
        # 步骤2：应用净化
        purified_actions = self._apply_purification(queue.actions, issues, level)
        
        # 步骤3：更新依赖关系
        self._update_dependencies(purified_actions, issues)
        
        # 添加到净化队列
        purified_queue.add_actions(purified_actions)
        
        score_after = self._calculate_queue_quality_score(purified_queue)
        
        # 统计改进
        improvements = {
            "total_issues": len(issues),
            "issues_by_category": self._group_issues_by_category(issues),
            "score_improvement": score_after - score_before,
            "actions_processed": len(queue.actions)
        }
        
        return PurificationResult(
            original_queue=queue,
            purified_queue=purified_queue,
            issues=issues,
            improvements=improvements,
            quality_score_before=score_before,
            quality_score_after=score_after
        )

    def _calculate_queue_quality_score(self, queue: AtomicActionQueue) -> float:
        """计算队列质量评分"""
        if not queue.actions:
            return 0.0
        
        total_score = 0.0
        for action in queue.actions:
            validation = self.validator.validate_atomic_action(action)
            total_score += validation.score
        
        return total_score / len(queue.actions)

    def _detect_duplicate_actions(self, queue: AtomicActionQueue) -> List[PurificationIssue]:
        """检测重复动作"""
        issues = []
        action_signatures = {}
        
        for action in queue.actions:
            # 创建动作签名
            signature = self._create_action_signature(action)
            
            if signature in action_signatures:
                # 发现重复
                original = action_signatures[signature]
                issues.append(PurificationIssue(
                    action_id=action.action_id,
                    action_name=action.name,
                    category=IssueCategory.DUPLICATE_ACTION,
                    severity=3,
                    description=f"与动作 '{original.name}' 重复",
                    suggestion=f"考虑合并或移除，与 {original.action_id} 功能相同",
                    metadata={"duplicate_of": original.action_id}
                ))
            else:
                action_signatures[signature] = action
        
        return issues

    def _create_action_signature(self, action: AtomicAction) -> str:
        """创建动作签名用于去重"""
        input_names = sorted([inp.name for inp in action.inputs])
        output_names = sorted([out.name for out in action.outputs])
        
        return f"{action.action_type.value}:{action.name}:{input_names}:{output_names}"

    def _detect_vague_actions(self, queue: AtomicActionQueue) -> List[PurificationIssue]:
        """检测模糊动作"""
        issues = []
        
        for action in queue.actions:
            # 检查名称
            vague_in_name = any(word in action.name for word in self.vague_words)
            
            # 检查描述
            vague_in_desc = any(word in action.description for word in self.vague_words)
            
            # 检查描述长度
            desc_too_short = len(action.description.strip()) < 10
            
            if vague_in_name or vague_in_desc or desc_too_short:
                severity = 4 if vague_in_name else 2
                issues.append(PurificationIssue(
                    action_id=action.action_id,
                    action_name=action.name,
                    category=IssueCategory.VAGUE_NAME,
                    severity=severity,
                    description="动作名称或描述模糊，不够明确",
                    suggestion="使用更具体、明确的词汇，描述动作的具体功能",
                    metadata={
                        "vague_in_name": vague_in_name,
                        "vague_in_desc": vague_in_desc,
                        "desc_too_short": desc_too_short
                    }
                ))
        
        return issues

    def _detect_multi_resp_actions(self, queue: AtomicActionQueue) -> List[PurificationIssue]:
        """检测多职责动作"""
        issues = []
        
        for action in queue.actions:
            # 检查多职责指示词
            has_multi_indicators = any(
                indicator in f"{action.name} {action.description}"
                for indicator in self.multi_resp_indicators
            )
            
            # 检查输入输出数量
            too_many_inputs = len(action.inputs) > 4
            too_many_outputs = len(action.outputs) > 3
            
            if has_multi_indicators or too_many_inputs or too_many_outputs:
                issues.append(PurificationIssue(
                    action_id=action.action_id,
                    action_name=action.name,
                    category=IssueCategory.MULTIPLE_RESPONSIBILITIES,
                    severity=4,
                    description="动作可能承担多个职责",
                    suggestion="考虑拆分为多个单一职责的原子动作",
                    metadata={
                        "has_multi_indicators": has_multi_indicators,
                        "input_count": len(action.inputs),
                        "output_count": len(action.outputs)
                    }
                ))
        
        return issues

    def _detect_missing_io(self, queue: AtomicActionQueue) -> List[PurificationIssue]:
        """检测缺少输入输出的动作"""
        issues = []
        
        for action in queue.actions:
            missing_input = len(action.inputs) == 0
            missing_output = len(action.outputs) == 0
            
            if missing_input or missing_output:
                issues.append(PurificationIssue(
                    action_id=action.action_id,
                    action_name=action.name,
                    category=IssueCategory.MISSING_INPUT_OUTPUT,
                    severity=3,
                    description="缺少明确的输入或输出定义",
                    suggestion="补充输入输出定义，明确动作的数据流转",
                    metadata={
                        "missing_input": missing_input,
                        "missing_output": missing_output
                    }
                ))
        
        return issues

    def _detect_inconsistent_naming(self, queue: AtomicActionQueue) -> List[PurificationIssue]:
        """检测命名不一致"""
        issues = []
        name_patterns = defaultdict(list)
        
        for action in queue.actions:
            # 提取动作类型关键词
            pattern = self._extract_naming_pattern(action)
            name_patterns[pattern].append(action)
        
        for pattern, actions in name_patterns.items():
            if len(actions) > 1:
                # 检查同类型动作的命名一致性
                standard = self._suggest_standard_name(actions[0])
                for action in actions[1:]:
                    if not self._is_naming_consistent(action, standard):
                        issues.append(PurificationIssue(
                            action_id=action.action_id,
                            action_name=action.name,
                            category=IssueCategory.INCONSISTENT_NAMING,
                            severity=1,
                            description=f"命名风格与同类动作不一致",
                            suggestion=f"建议使用 '{standard}' 风格",
                            metadata={"standard_pattern": standard}
                        ))
        
        return issues

    def _extract_naming_pattern(self, action: AtomicAction) -> str:
        """提取命名模式"""
        return action.action_type.value

    def _suggest_standard_name(self, action: AtomicAction) -> str:
        """建议标准名称"""
        name = action.name
        for standard, variations in self.naming_standards.items():
            for var in variations:
                if var in name:
                    return name.replace(var, standard)
        return name

    def _is_naming_consistent(self, action: AtomicAction, standard: str) -> bool:
        """检查命名是否一致"""
        return True  # 简化实现

    def _apply_purification(
        self,
        actions: List[AtomicAction],
        issues: List[PurificationIssue],
        level: PurificationLevel
    ) -> List[AtomicAction]:
        """应用净化"""
        purified = []
        removed_ids = set()
        
        # 先处理重复动作
        for issue in issues:
            if issue.category == IssueCategory.DUPLICATE_ACTION:
                removed_ids.add(issue.action_id)
        
        # 复制并优化剩余动作
        for action in actions:
            if action.action_id in removed_ids:
                continue
            
            # 创建副本
            new_action = AtomicAction.from_dict(action.to_dict())
            
            # 应用改进
            self._improve_action(new_action, issues, level)
            
            purified.append(new_action)
        
        return purified

    def _improve_action(
        self,
        action: AtomicAction,
        issues: List[PurificationIssue],
        level: PurificationLevel
    ):
        """改进单个动作"""
        # 标记为已净化
        action.metadata["purified"] = True
        action.metadata["purification_level"] = level.value
        
        # 根据问题类型应用改进
        action_issues = [i for i in issues if i.action_id == action.action_id]
        
        for issue in action_issues:
            if issue.category == IssueCategory.VAGUE_NAME:
                self._standardize_name(action)
            elif issue.category == IssueCategory.MISSING_INPUT_OUTPUT:
                self._add_default_io(action)

    def _standardize_name(self, action: AtomicAction):
        """标准化命名"""
        name = action.name
        
        # 尝试标准化
        for standard, variations in self.naming_standards.items():
            for var in variations:
                if var in name and standard not in name:
                    name = name.replace(var, standard)
                    break
        
        action.name = name
        action.metadata["original_name"] = action.name

    def _add_default_io(self, action: AtomicAction):
        """添加默认输入输出"""
        if not action.inputs:
            action.add_input(
                name="input",
                type="any",
                required=False,
                description="输入数据"
            )
        
        if not action.outputs:
            action.add_output(
                name="output",
                type="any",
                description="输出结果"
            )

    def _update_dependencies(
        self,
        actions: List[AtomicAction],
        issues: List[PurificationIssue]
    ):
        """更新依赖关系"""
        # 构建ID映射
        id_map = {}
        for action in actions:
            id_map[action.action_id] = action.action_id
        
        # 处理重复动作的依赖替换
        duplicate_map = {}
        for issue in issues:
            if issue.category == IssueCategory.DUPLICATE_ACTION:
                duplicate_map[issue.action_id] = issue.metadata.get("duplicate_of")
        
        # 更新依赖
        for action in actions:
            new_deps = []
            for dep_id in action.dependencies:
                if dep_id in duplicate_map:
                    new_deps.append(duplicate_map[dep_id])
                elif dep_id in id_map:
                    new_deps.append(dep_id)
            action.dependencies = new_deps

    def _group_issues_by_category(self, issues: List[PurificationIssue]) -> Dict[str, int]:
        """按类别分组问题"""
        groups = defaultdict(int)
        for issue in issues:
            groups[issue.category.value] += 1
        return dict(groups)

    def get_purification_report(self, result: PurificationResult) -> Dict[str, Any]:
        """生成净化报告"""
        return {
            "summary": {
                "total_actions_before": len(result.original_queue.actions),
                "total_actions_after": len(result.purified_queue.actions),
                "score_before": result.quality_score_before,
                "score_after": result.quality_score_after,
                "improvement": result.improvements
            },
            "issues": [
                {
                    "action_id": i.action_id,
                    "action_name": i.action_name,
                    "category": i.category.value,
                    "severity": i.severity,
                    "description": i.description,
                    "suggestion": i.suggestion
                }
                for i in result.issues
            ],
            "recommendations": self._generate_recommendations(result)
        }

    def _generate_recommendations(self, result: PurificationResult) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        if result.improvements["score_improvement"] > 10:
            recommendations.append("✅ 净化效果显著，队列质量大幅提升")
        elif result.improvements["score_improvement"] > 0:
            recommendations.append("ℹ️ 净化有一定效果，可考虑进一步优化")
        else:
            recommendations.append("⚠️ 队列质量已较好，或可使用ADVANCED级别深度净化")
        
        high_severity = [i for i in result.issues if i.severity >= 4]
        if high_severity:
            recommendations.append(f"⚠️ 存在 {len(high_severity)} 个高优先级问题需要关注")
        
        return recommendations


# 便捷函数
def purify_atomic_queue(
    queue: AtomicActionQueue,
    level: PurificationLevel = PurificationLevel.STANDARD
) -> Tuple[AtomicActionQueue, Dict[str, Any]]:
    """
    便捷函数：净化原子队列
    
    Args:
        queue: 原子队列
        level: 净化级别
        
    Returns:
        (净化后队列, 净化报告)
    """
    purifier = ActionPurifier()
    result = purifier.purify_queue(queue, level)
    report = purifier.get_purification_report(result)
    return result.purified_queue, report


def get_action_quality_score(action: AtomicAction) -> float:
    """
    便捷函数：获取单个动作的质量评分
    
    Args:
        action: 原子动作
        
    Returns:
        float: 质量评分 0-100
    """
    purifier = ActionPurifier()
    validator = AtomicValidator()
    validation = validator.validate_atomic_action(action)
    return validation.score
