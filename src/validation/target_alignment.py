"""
第四层：分段校验收敛层 - 目标对齐预校验
基于第一性原理的AI Agent任务规划系统

核心功能：
- 目标匹配度验证
- 偏离度检测
- 范围越界检测
- 收敛性监控
"""

import re
import time
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from validation.segment_validator import (
    SegmentValidator,
    ValidationPoint,
    ValidationResult,
    ValidationRule,
    ValidationReport,
    CircuitState
)


class AlignmentStatus(Enum):
    """对齐状态"""
    ALIGNED = "aligned"           # 完全对齐
    PARTIAL = "partial"           # 部分对齐
    DEVIATED = "deviated"         # 已偏离
    BLOCKED = "blocked"           # 被阻止


class DriftType(Enum):
    """偏离类型"""
    SEMANTIC = "semantic"          # 语义偏离
    SCOPE = "scope"               # 范围偏离
    DIRECTION = "direction"        # 方向偏离
    SCALE = "scale"               # 规模偏离


@dataclass
class TargetDefinition:
    """目标定义"""
    target_id: str
    target_text: str              # 原始目标文本
    target_keywords: List[str]     # 关键词列表
    target_entities: List[str]     # 实体列表
    scope_boundary: List[str]     # 范围边界关键词
    anti_keywords: List[str]       # 反向关键词（表示偏离）
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AlignmentMetrics:
    """对齐指标"""
    match_score: float = 0.0      # 匹配度 0-1
    drift_score: float = 0.0       # 偏离度 0-1
    coverage_score: float = 0.0    # 覆盖率 0-1
    relevance_score: float = 0.0    # 相关度 0-1
    alignment_status: AlignmentStatus = AlignmentStatus.ALIGNED


@dataclass
class AlignmentReport:
    """对齐报告"""
    target_id: str
    action_id: str
    timestamp: float = field(default_factory=time.time)
    
    metrics: AlignmentMetrics = field(default_factory=AlignmentMetrics)
    drift_detected: List[DriftType] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    
    should_block: bool = False    # 是否阻止执行
    reason: str = ""              # 阻止原因


class TargetAlignmentValidator:
    """
    目标对齐预校验器
    
    功能：
    - 目标匹配度验证
    - 偏离度检测
    - 范围越界检测
    - 与分段验证框架集成
    """

    def __init__(
        self,
        base_validator: Optional[SegmentValidator] = None,
        match_threshold: float = 0.6,
        drift_threshold: float = 0.3
    ):
        """
        初始化目标对齐验证器
        
        Args:
            base_validator: 基础验证器
            match_threshold: 匹配度阈值
            drift_threshold: 偏离度阈值
        """
        self.base_validator = base_validator or SegmentValidator()
        self.match_threshold = match_threshold
        self.drift_threshold = drift_threshold
        
        self.targets: Dict[str, TargetDefinition] = {}
        self.alignment_history: List[AlignmentReport] = []
        
        # 注册目标对齐规则
        self._register_alignment_rules()

    def _register_alignment_rules(self):
        """注册对齐验证规则"""
        self.base_validator.add_rule(ValidationRule(
            rule_id="rule_target_match",
            name="目标匹配度检查",
            description="验证动作是否匹配目标",
            validation_point=ValidationPoint.PRE_SUBTASK,
            validator=lambda ctx: ctx.get("match_score", 1.0) >= self.match_threshold,
            severity=5
        ))

        self.base_validator.add_rule(ValidationRule(
            rule_id="rule_drift_check",
            name="偏离度检查",
            description="检测是否偏离目标",
            validation_point=ValidationPoint.PRE_SUBTASK,
            validator=lambda ctx: ctx.get("drift_score", 0.0) <= self.drift_threshold,
            severity=5
        ))

        self.base_validator.add_rule(ValidationRule(
            rule_id="rule_scope_check",
            name="范围边界检查",
            description="验证是否超出任务范围",
            validation_point=ValidationPoint.PRE_ACTION,
            validator=lambda ctx: not ctx.get("scope_violation", False),
            severity=4
        ))

    def define_target(
        self,
        target_id: str,
        target_text: str,
        scope_keywords: Optional[List[str]] = None,
        anti_keywords: Optional[List[str]] = None
    ) -> TargetDefinition:
        """
        定义目标
        
        Args:
            target_id: 目标ID
            target_text: 目标文本
            scope_keywords: 范围关键词（如果不提供则自动提取）
            anti_keywords: 反向关键词
        
        Returns:
            TargetDefinition: 目标定义
        """
        # 如果未提供scope_keywords，则自动提取
        if scope_keywords is None:
            scope_keywords = self._extract_keywords(target_text)
        
        # 提取实体
        entities = self._extract_entities(target_text)
        
        target = TargetDefinition(
            target_id=target_id,
            target_text=target_text,
            target_keywords=scope_keywords,  # 使用scope_keywords作为关键词
            target_entities=entities,
            scope_boundary=scope_keywords,
            anti_keywords=anti_keywords or []
        )
        
        self.targets[target_id] = target
        return target

    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        # 改进的关键词提取
        # 移除标点符号，用空格替换
        text_clean = re.sub(r'[,，。、；;：:\s（）()《》""'']', ' ', text)
        
        # 提取所有2-4字的中文词组
        chinese_phrases = re.findall(r'[\u4e00-\u9fff]{2,4}', text_clean)
        
        # 提取英文单词
        english_words = re.findall(r'[a-zA-Z]{2,}', text_clean.lower())
        
        # 过滤停用词
        stopwords = {
            '的', '了', '和', '是', '在', '有', '个', '上', '不', '就',
            '包含', '包括', '以及', '还有', '这个', '那个', '某个',
            '每个', '各种', '某些', '各个', '其他',
            'to', 'the', 'a', 'an', 'is', 'are', 'and', 'or'
        }
        
        # 合并关键词并过滤
        keywords = []
        for phrase in chinese_phrases + english_words:
            phrase_lower = phrase.lower()
            if phrase_lower not in stopwords and len(phrase_lower) >= 2:
                keywords.append(phrase_lower)
        
        # 使用字典去重，保持出现顺序
        seen = set()
        unique_keywords = []
        for kw in keywords:
            if kw not in seen:
                seen.add(kw)
                unique_keywords.append(kw)
        
        return unique_keywords[:10]  # 最多10个关键词

    def _extract_entities(self, text: str) -> List[str]:
        """提取实体（简单实现）"""
        # 简单实现：提取带引号或书名号的词
        quoted = re.findall(r'["""\'\'\'](.+?)["""\'\'\']', text)
        bracketed = re.findall(r'《(.+?)》', text)
        
        entities = quoted + bracketed
        return list(set(entities))

    def validate_alignment(
        self,
        target_id: str,
        action_text: str,
        action_context: Optional[Dict[str, Any]] = None
    ) -> AlignmentReport:
        """
        验证目标对齐
        
        Args:
            target_id: 目标ID
            action_text: 动作/步骤文本
            action_context: 动作上下文
        
        Returns:
            AlignmentReport: 对齐报告
        """
        if target_id not in self.targets:
            return AlignmentReport(
                target_id=target_id,
                action_id="unknown",
                should_block=True,
                reason=f"目标未定义: {target_id}"
            )
        
        target = self.targets[target_id]
        
        # 计算各项指标（使用原始文本）
        metrics = self._calculate_alignment_metrics(target, action_text)
        
        # 检测偏离
        drifts = self._detect_drift(target, action_text)
        
        # 生成警告和建议
        warnings, suggestions = self._generate_feedback(metrics, drifts)
        
        # 判断是否阻止执行
        should_block = (
            metrics.match_score < self.match_threshold or
            metrics.drift_score > self.drift_threshold or
            len(drifts) > 0
        )
        
        reason = ""
        if should_block:
            if metrics.match_score < self.match_threshold:
                reason += f"匹配度过低({metrics.match_score:.2f}<{self.match_threshold}) "
            if metrics.drift_score > self.drift_threshold:
                reason += f"偏离度过高({metrics.drift_score:.2f}>{self.drift_threshold}) "
            if drifts:
                reason += f"检测到偏离: {[d.value for d in drifts]}"
        
        report = AlignmentReport(
            target_id=target_id,
            action_id=action_context.get("action_id", "unknown") if action_context else "unknown",
            metrics=metrics,
            drift_detected=drifts,
            warnings=warnings,
            suggestions=suggestions,
            should_block=should_block,
            reason=reason.strip()
        )
        
        # 记录历史
        self.alignment_history.append(report)
        
        return report

    def _calculate_alignment_metrics(
        self,
        target: TargetDefinition,
        action_text: str
    ) -> AlignmentMetrics:
        """计算对齐指标"""
        # 匹配度计算
        match_score = self._calculate_match_score(target, action_text)
        
        # 偏离度计算
        drift_score = self._calculate_drift_score(target, action_text)
        
        # 覆盖率计算
        coverage_score = self._calculate_coverage_score(target, action_text)
        
        # 相关度计算
        relevance_score = self._calculate_relevance_score(target, action_text)
        
        # 确定对齐状态
        if match_score >= self.match_threshold and drift_score <= self.drift_threshold:
            status = AlignmentStatus.ALIGNED
        elif match_score >= 0.4 and drift_score <= 0.6:
            status = AlignmentStatus.PARTIAL
        else:
            status = AlignmentStatus.DEVIATED
        
        return AlignmentMetrics(
            match_score=match_score,
            drift_score=drift_score,
            coverage_score=coverage_score,
            relevance_score=relevance_score,
            alignment_status=status
        )

    def _calculate_match_score(
        self,
        target: TargetDefinition,
        action_text: str
    ) -> float:
        """计算匹配度"""
        if not target.target_keywords:
            return 0.5
        
        matches = 0
        for keyword in target.target_keywords:
            if keyword in action_text:
                matches += 1
        
        return matches / len(target.target_keywords)

    def _calculate_drift_score(
        self,
        target: TargetDefinition,
        action_text: str
    ) -> float:
        """计算偏离度"""
        if not target.anti_keywords:
            return 0.0
        
        anti_matches = 0
        for anti_keyword in target.anti_keywords:
            if anti_keyword in action_text:
                anti_matches += 1
        
        return anti_matches / len(target.anti_keywords) if target.anti_keywords else 0.0

    def _calculate_coverage_score(
        self,
        target: TargetDefinition,
        action_text: str
    ) -> float:
        """计算覆盖率"""
        covered = 0
        for keyword in target.target_keywords:
            if keyword in action_text:
                covered += 1
        
        total_keywords = len(target.target_keywords)
        return covered / total_keywords if total_keywords > 0 else 0.0

    def _calculate_relevance_score(
        self,
        target: TargetDefinition,
        action_text: str
    ) -> float:
        """计算相关度"""
        # 综合匹配度和覆盖率
        match = self._calculate_match_score(target, action_text)
        coverage = self._calculate_coverage_score(target, action_text)
        
        return (match + coverage) / 2

    def _detect_drift(
        self,
        target: TargetDefinition,
        action_text: str
    ) -> List[DriftType]:
        """检测偏离类型"""
        drifts = []
        
        # 语义偏离检测
        if target.anti_keywords:
            for anti in target.anti_keywords:
                if anti in action_text:
                    drifts.append(DriftType.SEMANTIC)
                    break
        
        # 方向偏离检测（关键词完全不匹配）
        match_score = self._calculate_match_score(target, action_text)
        if match_score < 0.2:
            drifts.append(DriftType.DIRECTION)
        
        # 范围偏离检测（暂时禁用，因为逻辑有争议）
        # 注意：关键词在动作中不一定代表偏离，可能代表动作在范围内
        # 如果需要检测动作超出范围，应该使用anti_keywords
        
        return drifts

    def _generate_feedback(
        self,
        metrics: AlignmentMetrics,
        drifts: List[DriftType]
    ) -> Tuple[List[str], List[str]]:
        """生成反馈"""
        warnings = []
        suggestions = []
        
        if metrics.match_score < self.match_threshold:
            warnings.append(f"匹配度过低: {metrics.match_score:.2f}")
            suggestions.append("建议使用更接近目标的描述")
        
        if metrics.drift_score > self.drift_threshold:
            warnings.append(f"检测到偏离: {metrics.drift_score:.2f}")
            suggestions.append("建议检查动作是否与目标相关")
        
        if metrics.coverage_score < 0.3:
            warnings.append("覆盖率过低，可能偏离目标")
            suggestions.append("建议重新审视动作是否必要")
        
        if DriftType.SEMANTIC in drifts:
            warnings.append("检测到语义偏离")
            suggestions.append("建议使用更准确的目标相关词汇")
        
        if DriftType.DIRECTION in drifts:
            warnings.append("检测到方向偏离")
            suggestions.append("建议重新规划执行方向")
        
        if DriftType.SCOPE in drifts:
            warnings.append("检测到范围偏离")
            suggestions.append("建议聚焦于核心目标")
        
        return warnings, suggestions

    def validate_with_segment_validator(
        self,
        target_id: str,
        action_text: str,
        action_context: Optional[Dict[str, Any]] = None
    ) -> Tuple[AlignmentReport, ValidationReport]:
        """
        综合验证：目标对齐 + 分段验证
        
        Args:
            target_id: 目标ID
            action_text: 动作文本
            action_context: 动作上下文
        
        Returns:
            (AlignmentReport, ValidationReport): 对齐报告和验证报告
        """
        # 目标对齐验证
        alignment_report = self.validate_alignment(target_id, action_text, action_context)
        
        # 分段验证
        context = action_context or {}
        context.update({
            "match_score": alignment_report.metrics.match_score,
            "drift_score": alignment_report.metrics.drift_score,
            "scope_violation": DriftType.SCOPE in alignment_report.drift_detected
        })
        
        validation_report = self.base_validator.pre_validate_subtask(
            target_id,
            context
        )
        
        return alignment_report, validation_report

    def get_alignment_trend(
        self,
        target_id: str,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        获取对齐趋势
        
        Args:
            target_id: 目标ID
            limit: 限制返回数量
        
        Returns:
            Dict: 对齐趋势数据
        """
        history = [
            r for r in self.alignment_history
            if r.target_id == target_id
        ]
        
        if limit:
            history = history[-limit:]
        
        if not history:
            return {"trend": "no_data", "reports": []}
        
        match_scores = [r.metrics.match_score for r in history]
        drift_scores = [r.metrics.drift_score for r in history]
        
        # 计算趋势
        avg_match = sum(match_scores) / len(match_scores)
        avg_drift = sum(drift_scores) / len(drift_scores)
        
        if len(match_scores) >= 2:
            if match_scores[-1] > match_scores[0]:
                match_trend = "improving"
            elif match_scores[-1] < match_scores[0]:
                match_trend = "declining"
            else:
                match_trend = "stable"
        else:
            match_trend = "insufficient_data"
        
        return {
            "target_id": target_id,
            "total_checks": len(history),
            "average_match_score": avg_match,
            "average_drift_score": avg_drift,
            "match_trend": match_trend,
            "recent_metrics": [
                {
                    "timestamp": r.timestamp,
                    "match_score": r.metrics.match_score,
                    "drift_score": r.metrics.drift_score,
                    "status": r.metrics.alignment_status.value
                }
                for r in history[-5:]
            ]
        }


# 便捷函数
def quick_align_check(
    target_text: str,
    action_text: str,
    match_threshold: float = 0.6
) -> Tuple[float, bool, List[str]]:
    """
    快速对齐检查
    
    Args:
        target_text: 目标文本
        action_text: 动作文本
        match_threshold: 匹配度阈值
    
    Returns:
        (match_score, is_aligned, suggestions): 匹配度、是否对齐、建议
    """
    validator = TargetAlignmentValidator(
        match_threshold=match_threshold
    )
    
    target = validator.define_target(
        target_id="quick_check",
        target_text=target_text
    )
    
    report = validator.validate_alignment(
        target_id=target.target_id,
        action_text=action_text
    )
    
    return (
        report.metrics.match_score,
        not report.should_block,
        report.suggestions
    )
