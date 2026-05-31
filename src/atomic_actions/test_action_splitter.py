"""
复合动作自动拆分工具测试
基于第一性原理的AI Agent任务规划系统
"""

import sys
import os

# 确保能导入模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from action_splitter import (
    ActionSplitter, CompositeAction, SplitStrategy,
    split_composite_to_atomic
)
from atomic_action_struct import AtomicActionType, AtomicCondition


def test_basic_composite_split():
    """测试基本的复合动作拆分"""
    print("="*70)
    print("测试1：基本复合动作拆分（带明确步骤）")
    print("="*70)
    
    # 创建一个有明确步骤的复合动作
    composite = CompositeAction(
        composite_id="data_processing",
        name="数据处理流水线",
        description="从源读取数据、处理、保存",
        steps=[
            "读取原始数据",
            "清洗和转换数据",
            "验证处理结果",
            "保存最终结果"
        ]
    )
    
    splitter = ActionSplitter()
    queue = splitter.split_composite_action(composite)
    
    print(f"✅ 拆分完成，队列名称: {queue.name}")
    print(f"✅ 生成的原子动作数量: {len(queue.actions)}")
    
    print("\n生成的原子动作:")
    for i, action in enumerate(queue.actions, 1):
        print(f"\n  {i}. {action.name}")
        print(f"     ID: {action.action_id}")
        print(f"     类型: {action.action_type.value}")
        print(f"     输入: {len(action.inputs)} 个")
        print(f"     输出: {len(action.outputs)} 个")
        print(f"     依赖: {action.dependencies}")
        
        conditions = action.validate_atomic_conditions()
        print(f"     原子条件: {conditions}")
    
    return queue


def test_description_based_split():
    """测试基于描述的拆分"""
    print("\n" + "="*70)
    print("测试2：基于描述的拆分（模式匹配）")
    print("="*70)
    
    # 创建只有描述的复合动作
    composite = CompositeAction(
        composite_id="api_workflow",
        name="API调用流程",
        description="读取配置文件、调用API接口、写入结果数据",
        raw_description="读取配置文件、调用API接口、写入结果数据"
    )
    
    splitter = ActionSplitter()
    queue = splitter.split_composite_action(composite)
    
    print(f"✅ 拆分完成，队列名称: {queue.name}")
    print(f"✅ 生成的原子动作数量: {len(queue.actions)}")
    
    print("\n生成的原子动作:")
    for i, action in enumerate(queue.actions, 1):
        print(f"\n  {i}. {action.name}")
        print(f"     ID: {action.action_id}")
        print(f"     类型: {action.action_type.value}")
    
    return queue


def test_different_strategies():
    """测试不同的拆分策略"""
    print("\n" + "="*70)
    print("测试3：不同的拆分策略")
    print("="*70)
    
    composite = CompositeAction(
        composite_id="multi_strategy",
        name="多策略测试",
        description="执行多个操作",
        steps=[
            "步骤A",
            "步骤B",
            "步骤C",
            "步骤D"
        ]
    )
    
    strategies = [
        (SplitStrategy.SEQUENTIAL, "顺序策略"),
        (SplitStrategy.DEPENDENCY_BASED, "依赖导向策略"),
        (SplitStrategy.DATA_FLOW, "数据流策略"),
    ]
    
    for strategy, name in strategies:
        print(f"\n--- {name} ---")
        splitter = ActionSplitter()
        result = splitter.split_with_strategy(composite, strategy)
        
        queue = result['queue']
        print(f"✅ 策略: {result['strategy']}")
        print(f"✅ 动作数量: {result['action_count']}")
        
        for action in queue.actions:
            print(f"   - {action.name} (依赖: {action.dependencies})")


def test_custom_pattern():
    """测试自定义拆分模式"""
    print("\n" + "="*70)
    print("测试4：自定义拆分模式")
    print("="*70)
    
    splitter = ActionSplitter()
    
    # 添加自定义模式
    splitter.add_custom_pattern(
        pattern=r'发送|推送|通知',
        strategy=SplitStrategy.SEQUENTIAL,
        action_type=AtomicActionType.NETWORK,
        name_template="发送{resource}通知",
        description_template="发送{resource}通知"
    )
    
    print("✅ 添加自定义模式成功")
    
    # 测试自定义模式
    composite = CompositeAction(
        composite_id="notification",
        name="通知流程",
        description="发送系统通知、推送更新消息",
        raw_description="发送系统通知、推送更新消息"
    )
    
    queue = splitter.split_composite_action(composite)
    print(f"✅ 拆分完成，生成 {len(queue.actions)} 个动作")
    
    for action in queue.actions:
        print(f"\n  - {action.name}")
        print(f"    类型: {action.action_type.value}")


def test_convenience_function():
    """测试便捷函数"""
    print("\n" + "="*70)
    print("测试5：便捷函数使用")
    print("="*70)
    
    print("✅ 使用便捷函数拆分...")
    queue = split_composite_to_atomic(
        composite_id="quick_split",
        name="快速拆分测试",
        description="测试便捷函数",
        steps=[
            "初始化环境",
            "执行任务",
            "清理资源"
        ]
    )
    
    print(f"✅ 成功生成队列: {queue.name}")
    print(f"✅ 动作数量: {len(queue.actions)}")
    
    for action in queue.actions:
        print(f"\n  - {action.name}")
        print(f"    ID: {action.action_id}")
        print(f"    依赖: {action.dependencies}")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*70)
    print("复合动作自动拆分工具测试")
    print("="*70)
    
    try:
        test_basic_composite_split()
        test_description_based_split()
        test_different_strategies()
        test_custom_pattern()
        test_convenience_function()
        
        print("\n" + "="*70)
        print("✅ 所有测试通过！")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
