"""
拓扑纠错模块测试
基于第一性原理的AI Agent任务规划系统
"""

import sys
import os

# 确保能导入模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from topology_corrector import TopologyCorrector, correct_task_topology, correct_and_get_dict
from subtask_splitter import SubTaskSplitter, SplitStrategy
from subtask_node import SubTaskNode, DependencyType


def create_test_tasks_with_cycle() -> list[SubTaskNode]:
    """创建有循环依赖的测试任务"""
    task_a = SubTaskNode(
        node_id="task-a",
        name="任务A",
        description="第一个任务",
        sequence=1
    )
    task_b = SubTaskNode(
        node_id="task-b",
        name="任务B",
        description="第二个任务",
        sequence=2
    )
    task_c = SubTaskNode(
        node_id="task-c",
        name="任务C",
        description="第三个任务",
        sequence=3
    )
    
    # 创建循环依赖 A→B→C→A
    from subtask_node import Dependency
    task_b.dependencies.append(Dependency(
        dependency_id="task-a",
        dependency_type=DependencyType.HARD,
        description="依赖任务A"
    ))
    task_c.dependencies.append(Dependency(
        dependency_id="task-b",
        dependency_type=DependencyType.HARD,
        description="依赖任务B"
    ))
    task_a.dependencies.append(Dependency(
        dependency_id="task-c",
        dependency_type=DependencyType.SOFT,
        description="软依赖任务C"
    ))
    
    return [task_a, task_b, task_c]


def create_test_tasks_with_dangling() -> list[SubTaskNode]:
    """创建有悬空节点的测试任务"""
    task_a = SubTaskNode(
        node_id="task-a",
        name="任务A",
        description="第一个任务",
        sequence=1
    )
    task_b = SubTaskNode(
        node_id="task-b",
        name="任务B",
        description="第二个任务",
        sequence=2
    )
    task_c = SubTaskNode(
        node_id="task-c",
        name="任务C（悬空）",
        description="第三个任务，悬空",
        sequence=3
    )
    task_d = SubTaskNode(
        node_id="task-d",
        name="任务D（悬空）",
        description="第四个任务，悬空",
        sequence=4
    )
    
    # A和B有依赖，C和D悬空
    from subtask_node import Dependency
    task_b.dependencies.append(Dependency(
        dependency_id="task-a",
        dependency_type=DependencyType.HARD,
        description="依赖任务A"
    ))
    
    return [task_a, task_b, task_c, task_d]


def test_topology_corrector():
    """测试拓扑纠错模块"""
    print("=" * 70)
    print("拓扑纠错模块测试")
    print("=" * 70)
    
    corrector = TopologyCorrector()
    
    # 测试用例1：处理循环依赖
    print("\n" + "=" * 70)
    print("\n[测试1] 处理循环依赖")
    cycle_tasks = create_test_tasks_with_cycle()
    print("原始任务数量:", len(cycle_tasks))
    
    corrected = corrector.correct_topology(cycle_tasks)
    print("✅ 纠错完成")
    print(f"原始拓扑有效: {corrected.original_topology.is_valid}")
    print(f"纠错后拓扑有效: {corrected.corrected_topology.is_valid}")
    print(f"纠错成功: {corrected.is_successful}")
    print(f"纠错操作数量: {len(corrected.corrections_applied)}")
    
    for i, action in enumerate(corrected.corrections_applied, 1):
        print(f"\n操作 {i}:")
        print(f"  类型: {action.correction_type.value}")
        print(f"  描述: {action.description}")
        print(f"  影响节点: {action.affected_nodes}")
        print(f"  影响边: {action.affected_edges}")
    
    # 测试用例2：处理悬空节点
    print("\n" + "=" * 70)
    print("\n[测试2] 处理悬空节点")
    dangling_tasks = create_test_tasks_with_dangling()
    print("原始任务数量:", len(dangling_tasks))
    
    corrected2 = corrector.correct_topology(dangling_tasks)
    print("✅ 纠错完成")
    print(f"原始拓扑有效: {corrected2.original_topology.is_valid}")
    print(f"纠错后拓扑有效: {corrected2.corrected_topology.is_valid}")
    print(f"纠错成功: {corrected2.is_successful}")
    print(f"纠错操作数量: {len(corrected2.corrections_applied)}")
    
    for i, action in enumerate(corrected2.corrections_applied, 1):
        print(f"\n操作 {i}:")
        print(f"  类型: {action.correction_type.value}")
        print(f"  描述: {action.description}")
        print(f"  影响节点: {action.affected_nodes}")
        print(f"  影响边: {action.affected_edges}")
    
    # 测试用例3：正常任务处理
    print("\n" + "=" * 70)
    print("\n[测试3] 正常任务处理")
    splitter = SubTaskSplitter()
    normal_tasks = splitter.split_task(
        "开发一个Web应用",
        task_id="task-normal",
        strategy=SplitStrategy.BY_PHASE
    )
    print(f"正常任务数量: {len(normal_tasks)}")
    
    corrected3 = corrector.correct_topology(normal_tasks)
    print("✅ 纠错完成")
    print(f"原始拓扑有效: {corrected3.original_topology.is_valid}")
    print(f"纠错后拓扑有效: {corrected3.corrected_topology.is_valid}")
    print(f"纠错成功: {corrected3.is_successful}")
    print(f"纠错操作数量: {len(corrected3.corrections_applied)}")
    
    # 测试用例4：便捷函数测试
    print("\n" + "=" * 70)
    print("\n[测试4] 便捷函数测试")
    print("测试 correct_task_topology...")
    corrected_obj = correct_task_topology(normal_tasks)
    print(f"✅ 调用成功，纠错成功: {corrected_obj.is_successful}")
    
    print("\n测试 correct_and_get_dict...")
    result_dict = correct_and_get_dict(normal_tasks)
    print(f"✅ 调用成功")
    print(f"  纠错成功: {result_dict['is_successful']}")
    print(f"  纠错数量: {result_dict['corrections_count']}")
    print(f"  原始有效: {result_dict['original_valid']}")
    print(f"  纠错后有效: {result_dict['corrected_valid']}")
    print(f"  拓扑排序: {result_dict['topology_order']}")
    
    # 测试用例5：纠错结果转字典
    print("\n" + "=" * 70)
    print("\n[测试5] 纠错结果转字典")
    dict_data = corrector.corrected_to_dict(corrected)
    print(f"✅ 转换成功")
    print(f"字典键: {list(dict_data.keys())}")
    print(f"纠错成功: {dict_data['is_successful']}")
    print(f"纠错数量: {dict_data['corrections_count']}")
    
    print("\n" + "=" * 70)
    print("测试完成！")
    print("=" * 70)


if __name__ == "__main__":
    test_topology_corrector()
