#!/usr/bin/env python3
"""
阶段46测试脚本：任务分段验证框架
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from validation.segment_validator import (
    SegmentValidator,
    ValidationRule,
    ValidationPoint,
    ValidationResult,
    CircuitState,
    create_segment_validator,
    quick_validate
)


def test_basic_validation():
    """测试基本验证功能"""
    print("=" * 60)
    print("测试1: 基本验证功能")
    print("=" * 60)
    
    validator = create_segment_validator()
    
    # 子任务预校验 - 通过
    context_pass = {
        "inputs": {"data": "test_data"},
        "dependencies_ready": True
    }
    report = validator.pre_validate_subtask("subtask_1", context_pass)
    
    print(f"\n预校验（通过场景）:")
    print(f"  结果: {report.result.value}")
    print(f"  通过: {report.is_passed()}")
    print(f"  详情数: {len(report.details)}")
    
    assert report.is_passed(), "应该通过预校验"
    
    # 子任务预校验 - 失败
    context_fail = {
        "inputs": None,
        "dependencies_ready": False
    }
    report_fail = validator.pre_validate_subtask("subtask_2", context_fail)
    
    print(f"\n预校验（失败场景）:")
    print(f"  结果: {report_fail.result.value}")
    print(f"  通过: {report_fail.is_passed()}")
    
    assert not report_fail.is_passed(), "应该失败"
    
    print("\n✅ 基本验证测试通过!")


def test_post_action_validation():
    """测试动作后校验"""
    print("\n" + "=" * 60)
    print("测试2: 原子动作后校验")
    print("=" * 60)
    
    validator = create_segment_validator()
    
    # 后校验 - 通过
    context = {
        "has_output": True,
        "output_data": {"result": "success"},
        "has_error": False
    }
    report = validator.post_validate_action("action_1", context)
    
    print(f"\n后校验（正常）:")
    print(f"  结果: {report.result.value}")
    print(f"  耗时: {report.duration:.4f}s")
    print(f"  警告: {report.has_warnings()}")
    
    assert report.is_passed(), "应该通过后校验"
    
    # 后校验 - 失败（无输出）
    context_no_output = {
        "has_output": False,
        "has_error": True
    }
    report_fail = validator.post_validate_action("action_2", context_no_output)
    
    print(f"\n后校验（异常）:")
    print(f"  结果: {report_fail.result.value}")
    
    assert not report_fail.is_passed(), "应该失败"
    
    print("\n✅ 动作后校验测试通过!")


def test_custom_rules():
    """测试自定义规则"""
    print("\n" + "=" * 60)
    print("测试3: 自定义验证规则")
    print("=" * 60)
    
    validator = create_segment_validator()
    
    # 添加自定义规则
    validator.add_rule(ValidationRule(
        rule_id="custom_check",
        name="自定义数据检查",
        description="检查数据是否满足自定义条件",
        validation_point=ValidationPoint.PRE_ACTION,
        validator=lambda ctx: ctx.get("data_value", 0) > 10,
        severity=3
    ))
    
    # 测试自定义规则 - 通过
    checkpoint = validator.create_checkpoint(
        name="自定义规则测试",
        validation_point=ValidationPoint.PRE_ACTION,
        target_id="custom_action",
        rule_ids=["custom_check"]
    )
    
    context_pass = {"data_value": 100}
    report = validator.validate_checkpoint(checkpoint.checkpoint_id, context_pass)
    
    print(f"\n自定义规则（通过）:")
    print(f"  结果: {report.result.value}")
    print(f"  规则数: {len(report.details)}")
    
    assert report.is_passed(), "自定义规则应该通过"
    
    # 测试自定义规则 - 失败
    context_fail = {"data_value": 5}
    report_fail = validator.validate_checkpoint(checkpoint.checkpoint_id, context_fail)
    
    print(f"\n自定义规则（失败）:")
    print(f"  结果: {report_fail.result.value}")
    
    assert not report_fail.is_passed(), "自定义规则应该失败"
    
    print("\n✅ 自定义规则测试通过!")


def test_circuit_breaker():
    """测试熔断器"""
    print("\n" + "=" * 60)
    print("测试4: 熔断器机制")
    print("=" * 60)
    
    # 创建熔断器阈值为3的验证器
    validator = create_segment_validator(failure_threshold=3)
    
    print(f"\n初始熔断状态:")
    status = validator.get_circuit_status()
    print(f"  状态: {status['state']}")
    
    # 模拟连续失败
    for i in range(3):
        report = validator.post_validate_action(
            "action_test",
            {"has_output": False, "has_error": True}
        )
        print(f"  第{i+1}次验证: {report.result.value}")
    
    status_after = validator.get_circuit_status()
    print(f"\n触发熔断后状态:")
    print(f"  状态: {status_after['state']}")
    print(f"  连续失败: {status_after['consecutive_failures']}")
    
    assert status_after['state'] == CircuitState.OPEN.value, "应该触发熔断"
    
    # 测试熔断拒绝执行
    report_blocked = validator.post_validate_action(
        "action_blocked",
        {"has_output": True, "has_error": False}
    )
    
    print(f"\n熔断拒绝执行:")
    print(f"  结果: {report_blocked.result.value}")
    
    assert report_blocked.result == ValidationResult.FAIL, "熔断时应该拒绝"
    
    # 重置熔断器
    validator.reset_circuit_breaker()
    status_reset = validator.get_circuit_status()
    print(f"\n重置后状态: {status_reset['state']}")
    
    assert status_reset['state'] == CircuitState.CLOSED.value, "应该重置为关闭状态"
    
    print("\n✅ 熔断器测试通过!")


def test_quick_validate():
    """测试快速验证"""
    print("\n" + "=" * 60)
    print("测试5: 快速验证")
    print("=" * 60)
    
    validator = create_segment_validator()
    
    context = {
        "has_output": True,
        "has_error": False
    }
    
    report = quick_validate(
        validator=validator,
        validation_point=ValidationPoint.POST_ACTION,
        target_id="quick_test",
        context=context
    )
    
    print(f"\n快速验证结果:")
    print(f"  验证点: {report.validation_point.value}")
    print(f"  目标ID: {report.target_id}")
    print(f"  结果: {report.result.value}")
    print(f"  耗时: {report.duration:.4f}s")
    
    assert report.is_passed(), "快速验证应该通过"
    
    print("\n✅ 快速验证测试通过!")


def test_validation_summary():
    """测试验证摘要"""
    print("\n" + "=" * 60)
    print("测试6: 验证摘要")
    print("=" * 60)
    
    validator = create_segment_validator()
    
    # 执行多次验证
    for i in range(5):
        ctx = {
            "has_output": i % 2 == 0,
            "has_error": i % 2 == 1
        }
        validator.post_validate_action(f"action_{i}", ctx)
    
    summary = validator.get_validation_summary()
    
    print(f"\n验证摘要:")
    print(f"  总验证数: {summary['total_validations']}")
    print(f"  通过: {summary['passed']}")
    print(f"  警告: {summary['warnings']}")
    print(f"  失败: {summary['failed']}")
    print(f"  通过率: {summary['pass_rate']:.1%}")
    
    print(f"\n最近验证:")
    for v in summary['recent_validations']:
        print(f"  {v['checkpoint_id']}: {v['result']}")
    
    assert summary['total_validations'] == 5, "应该有5次验证记录"
    
    print("\n✅ 验证摘要测试通过!")


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("阶段46测试：任务分段验证框架")
    print("=" * 60)
    
    try:
        test_basic_validation()
        test_post_action_validation()
        test_custom_rules()
        test_circuit_breaker()
        test_quick_validate()
        test_validation_summary()
        
        print("\n" + "=" * 60)
        print("🎉 所有测试通过! 阶段46完成!")
        print("=" * 60)
        print("\n📊 第四层分段验证框架基础已建立!")
        print("🎯 总体进度: 46/100 (46%)")
        return True
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
