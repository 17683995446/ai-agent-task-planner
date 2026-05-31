"""
原子校验引擎测试
基于第一性原理的AI Agent任务规划系统
"""

import sys
import os

# 确保能导入模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from atomic_validator import (
    AtomicValidator, ValidationResult, ValidationIssue,
    IssueSeverity, IssueType,
    validate_atomic_actions, validate_queue_and_summarize
)
from atomic_action_struct import (
    AtomicAction, AtomicActionQueue, AtomicActionType, AtomicCondition,
    create_atomic_action
)


def test_single_responsibility_check():
    """测试单一职责原则校验"""
    print("="*70)
    print("测试1：单一职责原则校验")
    print("="*70)
    
    # 好的例子 - 单一职责
    good_action = create_atomic_action(
        action_id="good_action",
        name="读取配置文件",
        description="从指定路径读取配置文件",
        action_type=AtomicActionType.FILE_IO
    )
    good_action.add_input("file_path", "string", required=True)
    good_action.add_output("config", "dict")
    
    # 坏的例子 - 多职责
    bad_action = create_atomic_action(
        action_id="bad_action",
        name="读取配置文件和解析数据并保存到数据库",
        description="读取文件并且同时解析数据并且保存到数据库",
        action_type=AtomicActionType.CUSTOM
    )
    
    validator = AtomicValidator()
    
    # 校验好动作
    print("\n--- 好的动作（单一职责） ---")
    good_result = validator.validate_atomic_action(good_action)
    print(f"是否有效: {good_result.is_valid}")
    print(f"评分: {good_result.score}")
    print(f"问题数量: {len(good_result.issues)}")
    for issue in good_result.issues:
        print(f"  - {issue.severity.value}: {issue.description}")
    
    # 校验坏动作
    print("\n--- 坏的动作（多职责） ---")
    bad_result = validator.validate_atomic_action(bad_action)
    print(f"是否有效: {bad_result.is_valid}")
    print(f"评分: {bad_result.score}")
    print(f"问题数量: {len(bad_result.issues)}")
    for issue in bad_result.issues:
        print(f"  - {issue.severity.value}: {issue.description}")
        if issue.suggestion:
            print(f"    建议: {issue.suggestion}")
    
    return good_result, bad_result


def test_side_effect_check():
    """测试无副作用原则校验"""
    print("\n" + "="*70)
    print("测试2：无副作用原则校验")
    print("="*70)
    
    # 有副作用的例子
    side_effect_action = create_atomic_action(
        action_id="side_effect",
        name="删除旧数据",
        description="删除所有过期的数据记录",
        action_type=AtomicActionType.DATA_WRITE
    )
    
    # 无副作用的例子
    pure_action = create_atomic_action(
        action_id="pure_calc",
        name="计算平均值",
        description="基于输入数据计算统计平均值",
        action_type=AtomicActionType.COMPUTATION
    )
    
    validator = AtomicValidator()
    
    print("\n--- 有副作用的动作 ---")
    result1 = validator.validate_atomic_action(side_effect_action)
    print(f"是否有效: {result1.is_valid}")
    print(f"评分: {result1.score}")
    for issue in result1.issues:
        print(f"  - {issue.severity.value}: {issue.description}")
    
    print("\n--- 无副作用的动作 ---")
    result2 = validator.validate_atomic_action(pure_action)
    print(f"是否有效: {result2.is_valid}")
    print(f"评分: {result2.score}")
    for issue in result2.issues:
        print(f"  - {issue.severity.value}: {issue.description}")
    
    return result1, result2


def test_idempotent_check():
    """测试幂等性原则校验"""
    print("\n" + "="*70)
    print("测试3：幂等性原则校验")
    print("="*70)
    
    # 非幂等的例子
    non_idempotent = create_atomic_action(
        action_id="non_idempotent",
        name="递增计数器",
        description="每次调用计数器值加1",
        action_type=AtomicActionType.COMPUTATION
    )
    
    # 幂等的例子
    idempotent = create_atomic_action(
        action_id="idempotent",
        name="设置状态为完成",
        description="将任务状态设置为完成（多次执行结果相同）",
        action_type=AtomicActionType.DATA_WRITE
    )
    
    validator = AtomicValidator()
    
    print("\n--- 非幂等的动作 ---")
    result1 = validator.validate_atomic_action(non_idempotent)
    print(f"是否有效: {result1.is_valid}")
    print(f"评分: {result1.score}")
    for issue in result1.issues:
        print(f"  - {issue.severity.value}: {issue.description}")
    
    print("\n--- 幂等的动作 ---")
    result2 = validator.validate_atomic_action(idempotent)
    print(f"是否有效: {result2.is_valid}")
    print(f"评分: {result2.score}")
    for issue in result2.issues:
        print(f"  - {issue.severity.value}: {issue.description}")
    
    return result1, result2


def test_complex_action_detection():
    """测试复杂动作识别"""
    print("\n" + "="*70)
    print("测试4：复杂动作识别")
    print("="*70)
    
    # 复杂动作
    complex_action = create_atomic_action(
        action_id="complex",
        name="完整数据处理流程",
        description="这是一个完整的系统，包括多步骤处理，分阶段执行，同时进行多个操作",
        action_type=AtomicActionType.TRANSFORM
    )
    for i in range(10):
        complex_action.add_input(f"input_{i}", "string")
    
    validator = AtomicValidator()
    
    result = validator.validate_atomic_action(complex_action)
    print(f"是否有效: {result.is_valid}")
    print(f"评分: {result.score}")
    print(f"问题数量: {len(result.issues)}")
    
    for issue in result.issues:
        print(f"  - {issue.issue_type.value}: {issue.description}")
        if issue.suggestion:
            print(f"    建议: {issue.suggestion}")
    
    return result


def test_queue_validation():
    """测试队列校验"""
    print("\n" + "="*70)
    print("测试5：队列校验和摘要")
    print("="*70)
    
    queue = AtomicActionQueue(
        queue_id="test_queue",
        name="测试队列"
    )
    
    # 添加几个动作
    action1 = create_atomic_action(
        "act1", "读取数据", "从源读取数据", AtomicActionType.DATA_READ
    )
    action2 = create_atomic_action(
        "act2", "处理数据和保存结果", "处理数据并且同时保存结果", AtomicActionType.TRANSFORM
    )
    action3 = create_atomic_action(
        "act3", "发送通知", "发送通知给用户", AtomicActionType.NETWORK
    )
    
    queue.add_actions([action1, action2, action3])
    
    validator = AtomicValidator()
    results, summary = validate_queue_and_summarize(queue)
    
    print(f"总动作数: {summary['total_actions']}")
    print(f"有效动作数: {summary['valid_actions']}")
    print(f"平均评分: {summary['average_score']:.1f}")
    print(f"总问题数: {summary['total_issues']}")
    print("\n问题类型统计:")
    for issue_type, count in summary['issues_by_type'].items():
        print(f"  - {issue_type}: {count}")
    
    print("\n条件通过情况:")
    for cond, count in summary['passed_conditions'].items():
        print(f"  - {cond}: {count}/{summary['total_actions']}")
    
    return results, summary


def test_convenience_functions():
    """测试便捷函数"""
    print("\n" + "="*70)
    print("测试6：便捷函数使用")
    print("="*70)
    
    actions = [
        create_atomic_action("1", "动作1", "这是第一个动作", AtomicActionType.DATA_READ),
        create_atomic_action("2", "动作2", "处理数据和保存结果", AtomicActionType.TRANSFORM),
        create_atomic_action("3", "动作3", "删除旧数据", AtomicActionType.DATA_WRITE),
    ]
    
    print("✅ 使用便捷函数校验多个动作...")
    results = validate_atomic_actions(actions)
    
    print(f"✅ 校验完成，结果:")
    for i, result in enumerate(results, 1):
        print(f"\n  {i}. {result.action.name}")
        print(f"     评分: {result.score}")
        print(f"     问题数: {len(result.issues)}")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*70)
    print("原子校验引擎测试")
    print("="*70)
    
    try:
        test_single_responsibility_check()
        test_side_effect_check()
        test_idempotent_check()
        test_complex_action_detection()
        test_queue_validation()
        test_convenience_functions()
        
        print("\n" + "="*70)
        print("✅ 所有测试通过！")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
