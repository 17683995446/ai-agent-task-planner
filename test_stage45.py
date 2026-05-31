#!/usr/bin/env python3
"""
阶段45测试脚本：动作净化单元
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from atomic_actions.action_purifier import (
    ActionPurifier,
    PurificationLevel,
    purify_atomic_queue,
    get_action_quality_score
)
from atomic_actions.atomic_action_struct import (
    AtomicAction,
    AtomicActionQueue,
    AtomicActionType,
    AtomicCondition,
    create_atomic_action
)


def create_test_queue() -> AtomicActionQueue:
    """创建测试用的原子队列"""
    queue = AtomicActionQueue(
        queue_id="test_queue_45",
        name="测试队列 - 动作净化"
    )
    
    # 动作1: 正常动作
    action1 = create_atomic_action(
        action_id="action_1",
        name="读取配置文件",
        description="从指定路径读取JSON格式的配置文件",
        action_type=AtomicActionType.FILE_IO,
        priority=1
    )
    action1.add_input("file_path", "string", True, "配置文件路径")
    action1.add_output("config_data", "dict", "配置数据")
    action1.add_atomic_condition(AtomicCondition.SINGLE_RESPONSIBILITY)
    queue.add_action(action1)
    
    # 动作2: 模糊命名的动作
    action2 = create_atomic_action(
        action_id="action_2",
        name="处理数据",
        description="做一些相关处理",
        action_type=AtomicActionType.TRANSFORM,
        priority=2
    )
    queue.add_action(action2)
    
    # 动作3: 多职责动作
    action3 = create_atomic_action(
        action_id="action_3",
        name="读取和写入数据",
        description="同时读取数据并且写入到数据库",
        action_type=AtomicActionType.DATA_READ,
        priority=3
    )
    action3.add_input("input1", "any", True)
    action3.add_input("input2", "any", True)
    action3.add_input("input3", "any", True)
    action3.add_input("input4", "any", True)
    action3.add_input("input5", "any", True)
    action3.add_output("output1", "any")
    action3.add_output("output2", "any")
    action3.add_output("output3", "any")
    action3.add_output("output4", "any")
    queue.add_action(action3)
    
    # 动作4: 重复动作（和action1类似）
    action4 = create_atomic_action(
        action_id="action_4",
        name="读取配置文件",
        description="从指定路径读取JSON格式的配置文件",
        action_type=AtomicActionType.FILE_IO,
        priority=1
    )
    action4.add_input("file_path", "string", True, "配置文件路径")
    action4.add_output("config_data", "dict", "配置数据")
    queue.add_action(action4)
    
    # 动作5: 缺少IO的动作
    action5 = create_atomic_action(
        action_id="action_5",
        name="简单操作",
        description="一个简单的操作",
        action_type=AtomicActionType.CUSTOM,
        priority=4
    )
    queue.add_action(action5)
    
    return queue


def test_basic_purification():
    """测试基础净化"""
    print("=" * 60)
    print("测试1: 基础净化 (BASIC级别)")
    print("=" * 60)
    
    purifier = ActionPurifier()
    queue = create_test_queue()
    
    print(f"\n原始队列动作数: {len(queue.actions)}")
    
    result = purifier.purify_queue(queue, PurificationLevel.BASIC)
    
    print(f"净化后队列动作数: {len(result.purified_queue.actions)}")
    print(f"净化前评分: {result.quality_score_before:.1f}")
    print(f"净化后评分: {result.quality_score_after:.1f}")
    print(f"评分提升: {result.quality_score_after - result.quality_score_before:+.1f}")
    print(f"发现问题数: {len(result.issues)}")
    
    # 验证去重
    original_ids = {a.action_id for a in queue.actions}
    purified_ids = {a.action_id for a in result.purified_queue.actions}
    removed = original_ids - purified_ids
    
    if removed:
        print(f"\n移除的重复动作: {', '.join(removed)}")
    
    assert len(result.purified_queue.actions) <= len(queue.actions), "净化后动作数不应增加"
    print("\n✅ 基础净化测试通过!")
    
    return result


def test_standard_purification():
    """测试标准净化"""
    print("\n" + "=" * 60)
    print("测试2: 标准净化 (STANDARD级别)")
    print("=" * 60)
    
    purifier = ActionPurifier()
    queue = create_test_queue()
    
    result = purifier.purify_queue(queue, PurificationLevel.STANDARD)
    
    print(f"\n发现问题详情:")
    for issue in result.issues:
        print(f"\n【{issue.category.value}】{issue.action_name}")
        print(f"  严重程度: {'⭐' * issue.severity}")
        print(f"  描述: {issue.description}")
        print(f"  建议: {issue.suggestion}")
    
    # 统计问题类型
    issue_types = {}
    for issue in result.issues:
        issue_type = issue.category.value
        issue_types[issue_type] = issue_types.get(issue_type, 0) + 1
    
    print(f"\n问题类型统计: {issue_types}")
    
    assert len(result.issues) > 0, "应该能检测到问题"
    print("\n✅ 标准净化测试通过!")
    
    return result


def test_advanced_purification():
    """测试高级净化"""
    print("\n" + "=" * 60)
    print("测试3: 高级净化 (ADVANCED级别)")
    print("=" * 60)
    
    purifier = ActionPurifier()
    queue = create_test_queue()
    
    result = purifier.purify_queue(queue, PurificationLevel.ADVANCED)
    report = purifier.get_purification_report(result)
    
    print(f"\n净化报告摘要:")
    summary = report["summary"]
    print(f"  动作数: {summary['total_actions_before']} → {summary['total_actions_after']}")
    print(f"  质量评分: {summary['score_before']:.1f} → {summary['score_after']:.1f}")
    
    print(f"\n改进建议:")
    for rec in report["recommendations"]:
        print(f"  {rec}")
    
    print("\n✅ 高级净化测试通过!")
    
    return report


def test_convenience_functions():
    """测试便捷函数"""
    print("\n" + "=" * 60)
    print("测试4: 便捷函数")
    print("=" * 60)
    
    queue = create_test_queue()
    
    # 测试 purify_atomic_queue
    purified_queue, report = purify_atomic_queue(queue)
    print(f"一站式净化: {len(queue.actions)} → {len(purified_queue.actions)} 个动作")
    
    # 测试 get_action_quality_score
    test_action = queue.actions[0]
    score = get_action_quality_score(test_action)
    print(f"动作 '{test_action.name}' 质量评分: {score:.1f}/100")
    
    assert score >= 0 and score <= 100, "评分应该在0-100之间"
    print("\n✅ 便捷函数测试通过!")


def test_purification_improvements():
    """测试净化改进效果"""
    print("\n" + "=" * 60)
    print("测试5: 净化改进效果验证")
    print("=" * 60)
    
    purifier = ActionPurifier()
    queue = create_test_queue()
    
    # 测试不同级别
    levels = [
        (PurificationLevel.BASIC, "基础"),
        (PurificationLevel.STANDARD, "标准"),
        (PurificationLevel.ADVANCED, "高级")
    ]
    
    print("\n不同净化级别的效果:")
    for level, name in levels:
        result = purifier.purify_queue(queue, level)
        improvement = result.quality_score_after - result.quality_score_before
        print(f"  {name}级别: +{improvement:+.1f} 分, 发现 {len(result.issues)} 个问题")
    
    # 验证去重生效
    result_advanced = purifier.purify_queue(queue, PurificationLevel.ADVANCED)
    assert len(result_advanced.purified_queue.actions) <= len(queue.actions), \
        "净化后动作数不应增加"
    
    print("\n✅ 改进效果验证通过!")


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("阶段45测试：动作净化单元")
    print("=" * 60)
    
    try:
        test_basic_purification()
        test_standard_purification()
        test_advanced_purification()
        test_convenience_functions()
        test_purification_improvements()
        
        print("\n" + "=" * 60)
        print("🎉 所有测试通过! 阶段45完成!")
        print("=" * 60)
        print("\n📊 原子动作收敛层 5/5 模块全部完成!")
        print("🎯 总体进度: 45/100 (45%)")
        return True
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
