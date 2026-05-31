"""
原子动作结构体测试
基于第一性原理的AI Agent任务规划系统
"""

import sys
import os

# 确保能导入模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from atomic_action_struct import (
    AtomicAction, AtomicActionQueue, AtomicActionStatus, AtomicActionType,
    AtomicCondition, ActionInput, ActionOutput, ActionConstraint,
    create_atomic_action
)


def test_atomic_action_creation():
    """测试原子动作创建"""
    print("="*70)
    print("测试1：原子动作创建")
    print("="*70)
    
    action = create_atomic_action(
        action_id="read_config",
        name="读取配置文件",
        description="从文件系统读取配置文件",
        action_type=AtomicActionType.FILE_IO,
        priority=3
    )
    
    print(f"✅ 动作ID: {action.action_id}")
    print(f"✅ 动作名称: {action.name}")
    print(f"✅ 动作描述: {action.description}")
    print(f"✅ 动作类型: {action.action_type.value}")
    print(f"✅ 优先级: {action.priority}")
    print()
    
    # 添加输入
    action.add_input("file_path", "string", required=True, description="配置文件路径")
    action.add_input("encoding", "string", required=False, default="utf-8", description="文件编码")
    print(f"✅ 添加输入: {len(action.inputs)} 个")
    
    # 添加输出
    action.add_output("config_data", "dict", description="配置数据字典")
    print(f"✅ 添加输出: {len(action.outputs)} 个")
    
    # 添加原子条件
    action.add_atomic_condition(AtomicCondition.SINGLE_RESPONSIBILITY)
    action.add_atomic_condition(AtomicCondition.SIDE_EFFECT_FREE)
    print(f"✅ 添加原子条件: {len(action.atomic_conditions)} 个")
    
    print()
    print("原子条件验证:")
    conditions = action.validate_atomic_conditions()
    for cond, satisfied in conditions.items():
        status = "✅" if satisfied else "❌"
        print(f"  {status} {cond}: {satisfied}")
    
    return action


def test_atomic_action_serialization():
    """测试原子动作序列化"""
    print("\n" + "="*70)
    print("测试2：原子动作序列化/反序列化")
    print("="*70)
    
    action = create_atomic_action(
        action_id="write_data",
        name="写入数据",
        description="向数据库写入数据",
        action_type=AtomicActionType.DATA_WRITE,
        priority=2
    )
    
    action.add_input("table", "string", required=True, description="数据表名")
    action.add_input("data", "dict", required=True, description="数据内容")
    action.add_output("result", "dict", description="写入结果")
    action.add_atomic_condition(AtomicCondition.SINGLE_RESPONSIBILITY)
    
    # 序列化
    print("✅ 序列化到字典...")
    action_dict = action.to_dict()
    print(f"✅ 字典键: {list(action_dict.keys())}")
    print(f"✅ 动作ID: {action_dict['action_id']}")
    
    # 反序列化
    print("\n✅ 从字典反序列化...")
    restored_action = AtomicAction.from_dict(action_dict)
    print(f"✅ 反序列化成功: {restored_action.name}")
    print(f"✅ 动作名称一致: {action.name == restored_action.name}")
    print(f"✅ 动作类型一致: {action.action_type == restored_action.action_type}")
    print(f"✅ 输入数量一致: {len(action.inputs) == len(restored_action.inputs)}")


def test_atomic_action_status():
    """测试原子动作状态管理"""
    print("\n" + "="*70)
    print("测试3：原子动作状态管理")
    print("="*70)
    
    action = create_atomic_action(
        action_id="process_data",
        name="处理数据",
        description="数据处理操作",
        action_type=AtomicActionType.TRANSFORM
    )
    
    print(f"初始状态: {action.status.value}")
    
    action.update_status(AtomicActionStatus.READY)
    print(f"更新为就绪: {action.status.value}")
    print(f"是否就绪: {action.is_ready()}")
    
    action.update_status(AtomicActionStatus.RUNNING)
    print(f"更新为运行中: {action.status.value}")
    
    action.update_status(AtomicActionStatus.COMPLETED)
    print(f"更新为完成: {action.status.value}")
    print(f"是否完成: {action.is_completed()}")


def test_atomic_action_queue():
    """测试原子动作队列"""
    print("\n" + "="*70)
    print("测试4：原子动作队列")
    print("="*70)
    
    # 创建动作队列
    queue = AtomicActionQueue(
        queue_id="data_pipeline",
        name="数据处理流水线"
    )
    
    # 创建动作1
    action1 = create_atomic_action(
        action_id="read_data",
        name="读取数据",
        description="从数据源读取",
        action_type=AtomicActionType.DATA_READ
    )
    action1.add_input("source", "string", required=True)
    action1.add_output("raw_data", "list")
    action1.add_atomic_condition(AtomicCondition.SINGLE_RESPONSIBILITY)
    
    # 创建动作2
    action2 = create_atomic_action(
        action_id="clean_data",
        name="清洗数据",
        description="清洗和转换数据",
        action_type=AtomicActionType.TRANSFORM
    )
    action2.add_input("raw_data", "list", required=True)
    action2.add_dependency("read_data")
    action2.add_atomic_condition(AtomicCondition.SINGLE_RESPONSIBILITY)
    
    # 创建动作3
    action3 = create_atomic_action(
        action_id="save_result",
        name="保存结果",
        description="保存处理结果",
        action_type=AtomicActionType.DATA_WRITE
    )
    action3.add_input("clean_data", "list", required=True)
    action3.add_dependency("clean_data")
    action3.add_atomic_condition(AtomicCondition.SINGLE_RESPONSIBILITY)
    
    queue.add_actions([action1, action2, action3])
    print(f"✅ 添加动作: {len(queue.actions)} 个")
    
    print()
    print("队列中的动作:")
    for i, action in enumerate(queue.actions, 1):
        print(f"  {i}. {action.name} ({action.action_type.value}")
    
    print()
    pending = queue.get_pending_actions()
    print(f"待执行动作: {len(pending)} 个")
    
    print()
    action_found = queue.get_action("read_data")
    if action_found:
        print(f"✅ 找到动作: {action_found.name}")


def test_atomic_action_dependencies():
    """测试原子动作依赖关系"""
    print("\n" + "="*70)
    print("测试5：原子动作依赖关系")
    print("="*70)
    
    action = create_atomic_action(
        action_id="complex_action",
        name="复杂操作",
        description="需要前置步骤",
        action_type=AtomicActionType.COMPUTATION
    )
    
    action.add_dependency("step_1")
    action.add_dependency("step_2")
    action.add_dependency("step_3")
    
    print(f"添加依赖: {action.dependencies}")
    print(f"依赖数量: {len(action.dependencies)}")
    
    print()
    action.add_dependency("step_2")  # 重复添加
    print(f"重复添加后: {action.dependencies}")
    print(f"依赖数量: {len(action.dependencies)}")  # 应该不变


def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*70)
    print("原子动作结构体测试")
    print("="*70)
    
    try:
        test_atomic_action_creation()
        test_atomic_action_serialization()
        test_atomic_action_status()
        test_atomic_action_queue()
        test_atomic_action_dependencies()
        
        print("\n" + "="*70)
        print("✅ 所有测试通过！")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
