"""
第四层：分段校验收敛层 - 分段验证框架核心
基于第一性原理的AI Agent任务规划系统

核心功能：
- 定义验证点和验证标准
- 预校验：执行前检查
- 后校验：执行后验证
- 熔断回滚机制
"""

import time
import uuid
from typing import List, Dict, Any, Optional, Set, Callable
from dataclasses import dataclass, field
from enum import Enum


class ValidationPoint(Enum):
    """验证点类型"""
    PRE_SUBTASK = "pre_subtask"           # 子任务级预校验
    POST_ACTION = "post_action"           # 原子动作执行后校验
    PRE_ACTION = "pre_action"             # 原子动作执行前校验
    MILESTONE = "milestone"               # 里程碑校验
    FINAL = "final"                       # 最终校验


class ValidationResult(Enum):
    """验证结果"""
    PASS = "pass"                         # 通过
    FAIL = "fail"                        # 失败
    WARNING = "warning"                   # 警告
    SKIP = "skip"                        # 跳过


class CircuitState(Enum):
    """熔断状态"""
    CLOSED = "closed"                     # 正常（熔断器关闭）
    OPEN = "open"                         # 熔断（拒绝执行）
    HALF_OPEN = "half_open"               # 半开（尝试恢复）


@dataclass
class ValidationRule:
    """验证规则"""
    rule_id: str
    name: str
    description: str
    validation_point: ValidationPoint
    validator: Callable[[Any], bool]  # 验证函数
    severity: int = 3  # 1-5，严重程度
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self, context: Any) -> bool:
        """执行验证"""
        if not self.enabled:
            return True
        try:
            return self.validator(context)
        except Exception:
            return False


@dataclass
class ValidationCheckpoint:
    """验证检查点"""
    checkpoint_id: str
    name: str
    validation_point: ValidationPoint
    target_id: str  # 对应的任务/动作ID
    rules: List[ValidationRule] = field(default_factory=list)
    timeout: float = 30.0  # 验证超时时间（秒）
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationReport:
    """验证报告"""
    checkpoint_id: str
    validation_point: ValidationPoint
    target_id: str
    result: ValidationResult
    details: List[Dict[str, Any]] = field(default_factory=list)
    duration: float = 0.0  # 验证耗时
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_passed(self) -> bool:
        """是否通过"""
        return self.result == ValidationResult.PASS

    def has_warnings(self) -> bool:
        """是否有警告"""
        return self.result == ValidationResult.WARNING


@dataclass
class CircuitBreakerMetrics:
    """熔断器指标"""
    failure_count: int = 0
    success_count: int = 0
    total_calls: int = 0
    last_failure_time: Optional[float] = None
    last_success_time: Optional[float] = None
    consecutive_failures: int = 0


class SegmentValidator:
    """
    分段验证器
    
    功能：
    - 定义和管理验证点
    - 执行预校验和后校验
    - 熔断机制
    - 验证报告生成
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        half_open_calls: int = 3
    ):
        """
        初始化分段验证器
        
        Args:
            failure_threshold: 失败阈值，触发熔断
            recovery_timeout: 恢复超时时间（秒）
            half_open_calls: 半开状态允许的调用次数
        """
        self.checkpoints: Dict[str, ValidationCheckpoint] = {}
        self.rules: Dict[str, ValidationRule] = {}
        self.validation_history: List[ValidationReport] = []
        
        # 熔断器配置
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_calls = half_open_calls
        
        # 熔断器状态
        self.circuit_state = CircuitState.CLOSED
        self.metrics = CircuitBreakerMetrics()
        
        # 注册默认验证规则
        self._register_default_rules()

    def _register_default_rules(self):
        """注册默认验证规则"""
        self.add_rule(ValidationRule(
            rule_id="rule_input_check",
            name="输入完整性检查",
            description="验证输入参数是否完整",
            validation_point=ValidationPoint.PRE_ACTION,
            validator=lambda ctx: bool(ctx.get("inputs")),
            severity=4
        ))

        self.add_rule(ValidationRule(
            rule_id="rule_dependency_check",
            name="依赖前置检查",
            description="验证前置依赖是否满足",
            validation_point=ValidationPoint.PRE_ACTION,
            validator=lambda ctx: bool(ctx.get("dependencies_ready", True)),
            severity=5
        ))

        self.add_rule(ValidationRule(
            rule_id="rule_output_check",
            name="输出有效性检查",
            description="验证输出结果是否有效",
            validation_point=ValidationPoint.POST_ACTION,
            validator=lambda ctx: ctx.get("has_output", False),
            severity=4
        ))

        self.add_rule(ValidationRule(
            rule_id="rule_error_check",
            name="错误状态检查",
            description="检查执行过程是否有错误",
            validation_point=ValidationPoint.POST_ACTION,
            validator=lambda ctx: not ctx.get("has_error", False),
            severity=5
        ))

    def add_rule(self, rule: ValidationRule):
        """添加验证规则"""
        self.rules[rule.rule_id] = rule

    def remove_rule(self, rule_id: str):
        """移除验证规则"""
        if rule_id in self.rules:
            del self.rules[rule_id]

    def create_checkpoint(
        self,
        name: str,
        validation_point: ValidationPoint,
        target_id: str,
        rule_ids: Optional[List[str]] = None
    ) -> ValidationCheckpoint:
        """
        创建验证检查点
        
        Args:
            name: 检查点名称
            validation_point: 验证点类型
            target_id: 目标ID（任务/动作ID）
            rule_ids: 关联的规则ID列表
        
        Returns:
            ValidationCheckpoint: 验证检查点
        """
        checkpoint_id = f"chk_{uuid.uuid4().hex[:8]}"
        
        # 获取规则
        rules = []
        if rule_ids:
            for rid in rule_ids:
                if rid in self.rules:
                    rules.append(self.rules[rid])
        else:
            # 默认获取该验证点的所有规则
            rules = [r for r in self.rules.values() 
                    if r.validation_point == validation_point]
        
        checkpoint = ValidationCheckpoint(
            checkpoint_id=checkpoint_id,
            name=name,
            validation_point=validation_point,
            target_id=target_id,
            rules=rules
        )
        
        self.checkpoints[checkpoint_id] = checkpoint
        return checkpoint

    def validate_checkpoint(
        self,
        checkpoint_id: str,
        context: Dict[str, Any]
    ) -> ValidationReport:
        """
        执行检查点验证
        
        Args:
            checkpoint_id: 检查点ID
            context: 验证上下文
        
        Returns:
            ValidationReport: 验证报告
        """
        start_time = time.time()
        
        if checkpoint_id not in self.checkpoints:
            return ValidationReport(
                checkpoint_id=checkpoint_id,
                validation_point=ValidationPoint.PRE_ACTION,
                target_id="",
                result=ValidationResult.FAIL,
                details=[{"error": f"检查点不存在: {checkpoint_id}"}],
                duration=time.time() - start_time
            )
        
        checkpoint = self.checkpoints[checkpoint_id]
        
        # 检查熔断状态
        if not self._can_execute():
            return ValidationReport(
                checkpoint_id=checkpoint_id,
                validation_point=checkpoint.validation_point,
                target_id=checkpoint.target_id,
                result=ValidationResult.FAIL,
                details=[{"error": "熔断器已触发，执行被拒绝"}],
                duration=time.time() - start_time,
                metadata={"circuit_state": self.circuit_state.value}
            )
        
        # 执行验证
        details = []
        all_passed = True
        has_warning = False
        
        for rule in checkpoint.rules:
            rule_start = time.time()
            try:
                passed = rule.validate(context)
                rule_duration = time.time() - rule_start
                
                detail = {
                    "rule_id": rule.rule_id,
                    "rule_name": rule.name,
                    "passed": passed,
                    "severity": rule.severity,
                    "duration": rule_duration
                }
                
                if not passed:
                    all_passed = False
                    if rule.severity >= 4:
                        detail["level"] = "error"
                    else:
                        detail["level"] = "warning"
                        has_warning = True
                
                details.append(detail)
                
            except Exception as e:
                all_passed = False
                details.append({
                    "rule_id": rule.rule_id,
                    "rule_name": rule.name,
                    "passed": False,
                    "level": "error",
                    "error": str(e),
                    "severity": rule.severity
                })
        
        # 确定结果
        if all_passed:
            result = ValidationResult.PASS
        elif has_warning:
            result = ValidationResult.WARNING
        else:
            result = ValidationResult.FAIL
        
        # 更新熔断器
        self._update_circuit_breaker(result == ValidationResult.FAIL)
        
        # 生成报告
        report = ValidationReport(
            checkpoint_id=checkpoint_id,
            validation_point=checkpoint.validation_point,
            target_id=checkpoint.target_id,
            result=result,
            details=details,
            duration=time.time() - start_time
        )
        
        # 记录历史
        self.validation_history.append(report)
        
        return report

    def pre_validate_subtask(
        self,
        subtask_id: str,
        context: Dict[str, Any]
    ) -> ValidationReport:
        """
        子任务级预校验
        
        Args:
            subtask_id: 子任务ID
            context: 验证上下文
        
        Returns:
            ValidationReport: 验证报告
        """
        checkpoint = self.create_checkpoint(
            name=f"预校验: {subtask_id}",
            validation_point=ValidationPoint.PRE_SUBTASK,
            target_id=subtask_id,
            rule_ids=["rule_dependency_check", "rule_input_check"]
        )
        
        return self.validate_checkpoint(checkpoint.checkpoint_id, context)

    def post_validate_action(
        self,
        action_id: str,
        context: Dict[str, Any]
    ) -> ValidationReport:
        """
        原子动作执行后校验
        
        Args:
            action_id: 动作ID
            context: 验证上下文
        
        Returns:
            ValidationReport: 验证报告
        """
        checkpoint = self.create_checkpoint(
            name=f"后校验: {action_id}",
            validation_point=ValidationPoint.POST_ACTION,
            target_id=action_id,
            rule_ids=["rule_output_check", "rule_error_check"]
        )
        
        return self.validate_checkpoint(checkpoint.checkpoint_id, context)

    def _can_execute(self) -> bool:
        """检查是否可以执行"""
        if self.circuit_state == CircuitState.CLOSED:
            return True
        elif self.circuit_state == CircuitState.OPEN:
            # 检查是否超时，可以转换到半开状态
            if self.metrics.last_failure_time:
                elapsed = time.time() - self.metrics.last_failure_time
                if elapsed >= self.recovery_timeout:
                    self.circuit_state = CircuitState.HALF_OPEN
                    self.metrics.consecutive_failures = 0
                    return True
            return False
        elif self.circuit_state == CircuitState.HALF_OPEN:
            return True
        return False

    def _update_circuit_breaker(self, has_failure: bool):
        """更新熔断器状态"""
        if has_failure:
            self.metrics.failure_count += 1
            self.metrics.consecutive_failures += 1
            self.metrics.last_failure_time = time.time()
            
            if self.metrics.consecutive_failures >= self.failure_threshold:
                self.circuit_state = CircuitState.OPEN
        else:
            self.metrics.success_count += 1
            self.metrics.consecutive_failures = 0
            self.metrics.last_success_time = time.time()
            
            if self.circuit_state == CircuitState.HALF_OPEN:
                # 连续成功，关闭熔断器
                self.circuit_state = CircuitState.CLOSED

    def get_circuit_status(self) -> Dict[str, Any]:
        """获取熔断器状态"""
        return {
            "state": self.circuit_state.value,
            "failure_count": self.metrics.failure_count,
            "success_count": self.metrics.success_count,
            "consecutive_failures": self.metrics.consecutive_failures,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout
        }

    def reset_circuit_breaker(self):
        """重置熔断器"""
        self.circuit_state = CircuitState.CLOSED
        self.metrics = CircuitBreakerMetrics()

    def get_validation_summary(
        self,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        获取验证摘要
        
        Args:
            limit: 限制返回的记录数
        
        Returns:
            Dict: 验证摘要
        """
        history = self.validation_history
        if limit:
            history = history[-limit:]
        
        total = len(history)
        passed = sum(1 for r in history if r.is_passed())
        warnings = sum(1 for r in history if r.has_warnings())
        failed = total - passed - warnings
        
        return {
            "total_validations": total,
            "passed": passed,
            "warnings": warnings,
            "failed": failed,
            "pass_rate": passed / total if total > 0 else 0,
            "recent_validations": [
                {
                    "checkpoint_id": r.checkpoint_id,
                    "result": r.result.value,
                    "timestamp": r.timestamp,
                    "duration": r.duration
                }
                for r in history[-10:]
            ]
        }


# 便捷函数
def create_segment_validator(
    failure_threshold: int = 5,
    recovery_timeout: float = 60.0
) -> SegmentValidator:
    """
    创建分段验证器
    
    Args:
        failure_threshold: 失败阈值
        recovery_timeout: 恢复超时
    
    Returns:
        SegmentValidator: 分段验证器实例
    """
    return SegmentValidator(
        failure_threshold=failure_threshold,
        recovery_timeout=recovery_timeout
    )


def quick_validate(
    validator: SegmentValidator,
    validation_point: ValidationPoint,
    target_id: str,
    context: Dict[str, Any]
) -> ValidationReport:
    """
    快速验证
    
    Args:
        validator: 验证器实例
        validation_point: 验证点类型
        target_id: 目标ID
        context: 验证上下文
    
    Returns:
        ValidationReport: 验证报告
    """
    checkpoint = validator.create_checkpoint(
        name=f"快速验证: {target_id}",
        validation_point=validation_point,
        target_id=target_id
    )
    
    return validator.validate_checkpoint(checkpoint.checkpoint_id, context)
