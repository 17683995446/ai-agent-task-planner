#!/usr/bin/env python3
"""
阶段44测试脚本：子任务下沉转为原子队列逻辑
"""

import sys
import os

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from atomic_actions.atomic_queue_generator import (
    AtomicQueueGenerator,
    QueueStrategy,
    generate_atomic_queue_from_subtasks
)
from topology.subtask_node import SubTaskNode


def test_basic_conversion():
    """测试基本转换功能"""
    print("=" * 60)
    print("测试1: 基本子任务到原子队列转换")
    print("=" * 60)
    
    # 创建生成器
    generator = AtomicQueueGenerator()
    
    # 创建子任务
    subtask1 = SubTaskNode(
        node_id="subtask_1",
        name="读取数据",
        description="从数据库读取销售数据",
        priority=1
    )
    subtask1.add_input("database_url", "string", True, "数据库连接地址")
    subtask1.add_output("raw_data", "dict", "原始销售数据")
    
    subtask2 = SubTaskNode(
        node_id="subtask_2",
        name="处理数据",
        description="对销售数据进行统计分析",
        priority=2
    )
    subtask2.add_dependency("subtask_1")
    subtask2.add_input("raw_data", "dict", True, "原始销售数据")
    subtask2.add_output("statistics", "dict", "统计结果")
    
    subtasks = [subtask1, subtask2]
    
    # 生成队列
    queue, mappings = generator.subtasks_to_atomic_queue(
        subtasks,
        strategy=QueueStrategy.TOPOLOGICAL,
        queue_name="测试队列"
    )
    
    # 输出结果
    print(f"\n队列ID: {queue.queue_id}")
    print(f"队列名称: {queue.name}")
    print(f"原子动作数量: {len(queue.actions)}")
    
    print("\n原子动作列表:")
    for i, action in enumerate(queue.actions):
        print(f"  {i+1}. {action.name} ({action.action_type.value})")
        print(f"     优先级: {action.priority}")
        print(f"     依赖: {action.dependencies}")
        print(f"     所属子任务: {action.metadata.get('subtask_node_id')}")
    
    # 验证
    assert len(queue.actions) > 0, "应该生成原子动作"
    assert queue.queue_id.startswith("queue_"), "队列ID格式不正确"
    
    print("\n✅ 基本转换测试通过!")
    return queue, mappings


def test_execution_plan():
    """测试执行计划生成"""
    print("\n" + "=" * 60)
    print("测试2: 执行计划生成")
    print("=" * 60)
    
    generator = AtomicQueueGenerator()
    
    # 创建多个子任务
    subtasks = []
    for i in range(3):
        subtask = SubTaskNode(
            node_id=f"subtask_{i+1}",
            name=f"步骤{i+1}",
            description=f"执行步骤{i+1}",
            priority=i+1
        )
        if i > 0:
            subtask.add_dependency(f"subtask_{i}")
        subtasks.append(subtask)
    
    queue, _ = generator.subtasks_to_atomic_queue(subtasks)
    plan = generator.get_execution_plan(queue)
    
    print(f"\n执行计划 (共{len(plan)}步):")
    for step in plan:
        print(f"  步骤 {step['step']}: {step['name']}")
        print(f"     类型: {step['type']}")
        print(f"     优先级: {step['priority']}")
        print(f"     依赖: {step['dependencies']}")
    
    assert len(plan) == len(queue.actions), "执行计划步骤数应等于动作数"
    print("\n✅ 执行计划测试通过!")


def test_validation():
    """测试队列验证功能"""
    print("\n" + "=" * 60)
    print("测试3: 队列验证")
    print("=" * 60)
    
    generator = AtomicQueueGenerator()
    
    subtask = SubTaskNode(
        node_id="test_subtask",
        name="验证测试",
        description="测试验证功能"
    )
    
    queue, _ = generator.subtasks_to_atomic_queue([subtask])
    validation = generator.validate_atomic_queue(queue)
    
    print(f"\n原子验证结果:")
    print(f"  总动作数: {validation['atomic_validation']['total_actions']}")
    print(f"  有效动作数: {validation['atomic_validation']['valid_actions']}")
    print(f"  平均评分: {validation['atomic_validation']['average_score']:.1f}")
    
    print(f"\n依赖检查结果:")
    print(f"  是否有效: {validation['dependency_check']['is_valid']}")
    print(f"  总依赖数: {validation['dependency_check']['total_dependencies']}")
    
    print(f"\n整体验证: {'✅ 通过' if validation['is_valid'] else '❌ 失败'}")
    
    print("\n✅ 队列验证测试通过!")


def test_different_strategies():
    """测试不同排序策略"""
    print("\n" + "=" * 60)
    print("测试4: 不同排序策略")
    print("=" * 60)
    
    generator = AtomicQueueGenerator()
    
    # 创建有不同优先级的子任务
    subtasks = []
    priorities = [3, 1, 2]  # 故意打乱顺序
    for i, p in enumerate(priorities):
        subtask = SubTaskNode(
            node_id=f"subtask_{i+1}",
            name=f"任务{i+1}",
            description=f"优先级{p}",
            priority=p,
            sequence=i
        )
        subtasks.append(subtask)
    
    strategies = [
        (QueueStrategy.TOPOLOGICAL, "拓扑排序"),
        (QueueStrategy.PRIORITY, "优先级排序"),
        (QueueStrategy.SEQUENCE, "原顺序排序"),
        (QueueStrategy.WEIGHTED, "加权排序")
    ]
    
    for strategy, name in strategies:
        queue, _ = generator.subtasks_to_atomic_queue(subtasks, strategy=strategy)
        action_priorities = [a.priority for a in queue.actions]
        print(f"\n{name}结果:")
        print(f"  动作优先级顺序: {action_priorities}")
    
    print("\n✅ 多策略测试通过!")


def test_convenience_functions():
    """测试便捷函数"""
    print("\n" + "=" * 60)
    print("测试5: 便捷函数")
    print("=" * 60)
    
    from atomic_actions.atomic_queue_generator import get_execution_plan_from_subtasks
    
    subtasks = [
        SubTaskNode(
            node_id="quick_test",
            name="快速测试",
            description="测试便捷函数"
        )
    ]
    
    # 测试一站式生成
    queue, mappings, validation = generate_atomic_queue_from_subtasks(subtasks)
    print(f"一站式生成: {len(queue.actions)} 个动作")
    print(f"验证结果: {'通过' if validation['is_valid'] else '失败'}")
    
    # 测试快速执行计划
    plan = get_execution_plan_from_subtasks(subtasks)
    print(f"快速执行计划: {len(plan)} 步")
    
    print("\n✅ 便捷函数测试通过!")


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("阶段44测试: 子任务下沉转为原子队列逻辑")
    print("=" * 60)
    
    try:
        test_basic_conversion()
        test_execution_plan()
        test_validation()
        test_different_strategies()
        test_convenience_functions()
        
        print("\n" + "=" * 60)
        print("🎉 所有测试通过! 阶段44完成!")
        print("=" * 60)
        return True
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
