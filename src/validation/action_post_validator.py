"""
第四层：分段校验收敛层 - 动作执行后校验
基于第一性原理的AI Agent任务规划系统

核心功能：
- 动作输出验证
- 错误检测与处理
- 结果一致性检查
- 性能指标监控
"""

import time
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from validation.logger_manager import (
    LoggerManager,
    LogLevel,
    Environment,
    get_logger,
    performance_trace
)
from validation.segment_validator import (
    SegmentValidator,
    ValidationPoint,
    ValidationResult,
    ValidationRule,
    ValidationReport,
    CircuitState
)

# 使用统一的日志管理
logger = get_logger('validation.action_post')


class OutputValidationStatus(Enum):
    """输出验证状态"""
    VALID = "valid"                 # 有效
    INVALID = "invalid"            # 无效
    PARTIAL = "partial"            # 部分有效
    EMPTY = "empty"                # 空输出
    ERROR = "error"                # 错误


class ErrorSeverity(Enum):
    """错误严重程度"""
    LOW = 1        # 轻微
    MEDIUM = 2     # 中等
    HIGH = 3       # 高
    CRITICAL = 4   # 严重


@dataclass
class ActionOutput:
    """动作输出"""
    action_id: str
    success: bool
    data: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_successful(self) -> bool:
        """检查是否成功"""
        return self.success and self.error is None


@dataclass
class OutputValidationRule:
    """输出验证规则"""
    rule_id: str
    name: str
    validator: Callable[[ActionOutput], bool]
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
    description: str = ""


@dataclass
class PostActionValidationReport:
    """后校验报告"""
    action_id: str
    output: ActionOutput
    validation_status: OutputValidationStatus
    results: List[Dict[str, Any]]
    execution_time: float
    timestamp: float = field(default_factory=time.time)
    
    def is_valid(self) -> bool:
        """是否有效"""
        return self.validation_status == OutputValidationStatus.VALID
    
    def has_errors(self) -> bool:
        """是否有错误"""
        return self.validation_status == OutputValidationStatus.ERROR


class ActionPostValidator:
    """
    动作执行后校验器
    
    功能：
    - 动作输出验证
    - 错误检测与处理
    - 结果一致性检查
    - 性能指标监控
    """
    
    def __init__(self, base_validator: Optional[SegmentValidator] = None):
        """
        初始化后校验器
        
        Args:
            base_validator: 基础验证器
        """
        self.base_validator = base_validator or SegmentValidator()
        self.validation_rules: Dict[str, OutputValidationRule] = {}
        self.validation_history: List[PostActionValidationReport] = []
        
        # 统计信息
        self.stats = {
            "total_validations": 0,
            "successful_validations": 0,
            "failed_validations": 0,
            "total_execution_time": 0.0
        }
        
        # 注册默认规则
        self._register_default_rules()
        
        logger.info("✅ 动作执行后校验器初始化完成")

    def _register_default_rules(self):
        """注册默认验证规则"""
        self.add_rule(OutputValidationRule(
            rule_id="rule_success_check",
            name="成功状态检查",
            validator=lambda output: output.is_successful(),
            severity=ErrorSeverity.CRITICAL,
            description="检查动作是否成功执行"
        ))
        
        self.add_rule(OutputValidationRule(
            rule_id="rule_output_exists",
            name="输出存在性检查",
            validator=lambda output: output.data is not None,
            severity=ErrorSeverity.HIGH,
            description="检查输出数据是否存在"
        ))
        
        self.add_rule(OutputValidationRule(
            rule_id="rule_no_error",
            name="错误检查",
            validator=lambda output: output.error is None,
            severity=ErrorSeverity.CRITICAL,
            description="检查是否有错误信息"
        ))
        
        self.add_rule(OutputValidationRule(
            rule_id="rule_execution_time",
            name="执行时间检查",
            validator=lambda output: output.execution_time < 30.0,  # 默认30秒超时
            severity=ErrorSeverity.MEDIUM,
            description="检查执行时间是否超时"
        ))
        
        logger.debug(f"已注册 {len(self.validation_rules)} 个默认验证规则")

    def add_rule(self, rule: OutputValidationRule):
        """添加验证规则"""
        self.validation_rules[rule.rule_id] = rule
        logger.debug(f"添加验证规则: {rule.rule_id} - {rule.name}")

    def remove_rule(self, rule_id: str):
        """移除验证规则"""
        if rule_id in self.validation_rules:
            del self.validation_rules[rule_id]
            logger.debug(f"移除验证规则: {rule_id}")

    def validate_action_output(
        self,
        action_id: str,
        output: ActionOutput,
        custom_rules: Optional[List[str]] = None
    ) -> PostActionValidationReport:
        """
        验证动作输出
        
        Args:
            action_id: 动作ID
            output: 动作输出
            custom_rules: 自定义规则ID列表
        
        Returns:
            PostActionValidationReport: 后校验报告
        """
        start_time = time.time()
        
        # 添加性能追踪
        trace_id = None
        if logger.level <= LogLevel.DEBUG.value:
            trace_id = LoggerManager().start_performance_trace(
                f'validate_{action_id}',
                output_status=output.success
            )
        
        logger.info(f"🔍 开始验证动作: {action_id}")
        logger.debug(f"   成功状态: {output.success}")
        logger.debug(f"   错误信息: {output.error}")
        logger.debug(f"   执行时间: {output.execution_time:.3f}s")
        
        # 获取要执行的规则
        if custom_rules:
            rules_to_execute = [
                self.validation_rules[rid]
                for rid in custom_rules
                if rid in self.validation_rules
            ]
        else:
            rules_to_execute = list(self.validation_rules.values())
        
        logger.debug(f"   将执行 {len(rules_to_execute)} 个验证规则")
        
        # 执行验证
        results = []
        all_passed = True
        critical_failed = False
        has_warnings = False
        
        for rule in rules_to_execute:
            rule_start = time.time()
            try:
                passed = rule.validator(output)
                rule_duration = time.time() - rule_start
                
                result = {
                    "rule_id": rule.rule_id,
                    "rule_name": rule.name,
                    "passed": passed,
                    "severity": rule.severity.value,
                    "duration": rule_duration
                }
                
                if not passed:
                    logger.warning(f"   ⚠️ 规则失败: {rule.name} (严重程度: {rule.severity.name})")
                    all_passed = False
                    if rule.severity == ErrorSeverity.CRITICAL:
                        critical_failed = True
                    elif rule.severity == ErrorSeverity.HIGH:
                        has_warnings = True
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"   ❌ 规则执行异常: {rule.name} - {str(e)}")
                results.append({
                    "rule_id": rule.rule_id,
                    "rule_name": rule.name,
                    "passed": False,
                    "severity": rule.severity.value,
                    "error": str(e)
                })
                all_passed = False
        
        # 确定验证状态
        if critical_failed:
            status = OutputValidationStatus.ERROR
            logger.error(f"   ❌ 验证状态: ERROR (严重错误)")
        elif not all_passed and has_warnings:
            status = OutputValidationStatus.PARTIAL
            logger.warning(f"   ⚠️ 验证状态: PARTIAL (部分有效)")
        elif not all_passed:
            status = OutputValidationStatus.INVALID
            logger.warning(f"   ⚠️ 验证状态: INVALID (无效)")
        elif output.data is None:
            status = OutputValidationStatus.EMPTY
            logger.warning(f"   ⚠️ 验证状态: EMPTY (空输出)")
        else:
            status = OutputValidationStatus.VALID
            logger.info(f"   ✅ 验证状态: VALID (有效)")
        
        # 生成报告
        execution_time = time.time() - start_time
        report = PostActionValidationReport(
            action_id=action_id,
            output=output,
            validation_status=status,
            results=results,
            execution_time=execution_time
        )
        
        # 更新统计
        self._update_stats(report)
        
        # 记录历史
        self.validation_history.append(report)
        
        logger.info(f"   验证完成，耗时: {execution_time:.3f}s")
        
        # 结束性能追踪
        if trace_id:
            LoggerManager().end_performance_trace(trace_id)
        
        return report

    def _update_stats(self, report: PostActionValidationReport):
        """更新统计信息"""
        self.stats["total_validations"] += 1
        self.stats["total_execution_time"] += report.execution_time
        
        if report.is_valid():
            self.stats["successful_validations"] += 1
        else:
            self.stats["failed_validations"] += 1

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        total = self.stats["total_validations"]
        success_rate = (
            self.stats["successful_validations"] / total
            if total > 0 else 0
        )
        avg_time = (
            self.stats["total_execution_time"] / total
            if total > 0 else 0
        )
        
        return {
            "total_validations": total,
            "successful": self.stats["successful_validations"],
            "failed": self.stats["failed_validations"],
            "success_rate": success_rate,
            "average_execution_time": avg_time
        }

    def get_validation_history(
        self,
        limit: Optional[int] = None,
        action_id: Optional[str] = None,
        status: Optional[OutputValidationStatus] = None
    ) -> List[PostActionValidationReport]:
        """获取验证历史"""
        history = self.validation_history
        
        # 按动作ID过滤
        if action_id:
            history = [r for r in history if r.action_id == action_id]
        
        # 按状态过滤
        if status:
            history = [r for r in history if r.validation_status == status]
        
        # 限制数量
        if limit:
            history = history[-limit:]
        
        return history

    def get_failed_validations(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取失败的验证"""
        failed = [
            r for r in self.validation_history
            if not r.is_valid()
        ]
        
        if limit:
            failed = failed[-limit:]
        
        return [
            {
                "action_id": r.action_id,
                "status": r.validation_status.value,
                "timestamp": r.timestamp,
                "results": r.results
            }
            for r in failed
        ]


# 便捷函数
def quick_validate_output(
    action_id: str,
    success: bool,
    data: Any = None,
    error: Optional[str] = None,
    execution_time: float = 0.0
) -> PostActionValidationReport:
    """
    快速验证动作输出
    
    Args:
        action_id: 动作ID
        success: 是否成功
        data: 输出数据
        error: 错误信息
        execution_time: 执行时间
    
    Returns:
        PostActionValidationReport: 后校验报告
    """
    validator = ActionPostValidator()
    
    output = ActionOutput(
        action_id=action_id,
        success=success,
        data=data,
        error=error,
        execution_time=execution_time
    )
    
    return validator.validate_action_output(action_id, output)


# 使用示例和测试
if __name__ == "__main__":
    print("=" * 60)
    print("动作执行后校验器 - 快速测试")
    print("=" * 60)
    
    # 创建校验器
    validator = ActionPostValidator()
    
    # 测试1: 正常输出
    print("\n📝 测试1: 正常输出验证")
    output1 = ActionOutput(
        action_id="action_001",
        success=True,
        data={"result": "success", "count": 10},
        execution_time=0.5
    )
    report1 = validator.validate_action_output("action_001", output1)
    print(f"   结果: {report1.validation_status.value}")
    print(f"   有效: {report1.is_valid()}")
    
    # 测试2: 错误输出
    print("\n📝 测试2: 错误输出验证")
    output2 = ActionOutput(
        action_id="action_002",
        success=False,
        error="数据库连接失败",
        execution_time=0.1
    )
    report2 = validator.validate_action_output("action_002", output2)
    print(f"   结果: {report2.validation_status.value}")
    print(f"   有效: {report2.is_valid()}")
    
    # 测试3: 超时输出
    print("\n📝 测试3: 超时输出验证")
    output3 = ActionOutput(
        action_id="action_003",
        success=True,
        data={"partial": True},
        execution_time=35.0  # 超时
    )
    report3 = validator.validate_action_output("action_003", output3)
    print(f"   结果: {report3.validation_status.value}")
    print(f"   有警告: {report3.has_errors()}")
    
    # 打印统计
    print("\n📊 统计信息:")
    stats = validator.get_statistics()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print("\n✅ 快速测试完成!")
