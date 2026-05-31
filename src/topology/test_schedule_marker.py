"""
调度标记逻辑测试
基于第一性原理的AI Agent任务规划系统
"""

import sys
import os

# 确保能导入模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from schedule_marker import ScheduleMarker, mark_task_schedule, mark_and_get_dict
from subtask_splitter import SubTaskSplitter, SplitStrategy


def test_schedule_marker():
    """测试调度标记逻辑"""
    print("=" * 70)
    print("调度标记逻辑测试")
    print("=" * 70)
    
    marker = ScheduleMarker()
    
    # 测试用例1：基本任务调度标记
    print("\n" + "=" * 70)
    print("\n[测试1] 基本任务调度标记")
    splitter = SubTaskSplitter()
    subtasks = splitter.split_task(
        "开发一个Web应用",
        task_id="task-web",
        strategy=SplitStrategy.BY_PHASE
    )
    print(f"✅ 任务数量: {len(subtasks)}")
    
    scheduled = marker.mark_schedule(subtasks)
    print(f"✅ 调度标记完成")
    print(f"调度节点数量: {len(scheduled.scheduled_nodes)}")
    print(f"并行组数量: {len(scheduled.parallel_groups)}")
    print(f"串行批次数量: {len(scheduled.serial_batches)}")
    
    print("\n并行组:")
    for group_id, nodes in scheduled.parallel_groups.items():
        print(f"  {group_id}: {nodes}")
    
    print("\n串行批次:")
    for i, batch in enumerate(scheduled.serial_batches, 1):
        print(f"  批次 {i}: {batch}")
    
    # 测试用例2：调度标记详情
    print("\n" + "=" * 70)
    print("\n[测试2] 调度标记详情")
    print("调度标记列表:")
    for i, mark in enumerate(scheduled.schedule_marks, 1):
        print(f"\n  标记 {i}:")
        print(f"    节点ID: {mark.node_id}")
        print(f"    名称: {mark.name}")
        print(f"    执行类型: {mark.execution_type.value}")
        print(f"    组ID: {mark.group_id}")
        print(f"    并行组: {mark.parallel_group}")
        print(f"    批次顺序: {mark.batch_order}")
    
    # 测试用例3：调度节点详情
    print("\n" + "=" * 70)
    print("\n[测试3] 调度节点详情")
    for i, node in enumerate(scheduled.scheduled_nodes, 1):
        print(f"\n  节点 {i}:")
        print(f"    ID: {node.node_id}")
        print(f"    名称: {node.name}")
        print(f"    执行类型: {node.execution_type.value}")
        print(f"    可并行: {node.can_parallelize}")
        print(f"    依赖: {node.dependencies}")
        print(f"    被依赖: {node.dependents}")
        print(f"    优先级: {node.priority}")
        print(f"    组ID: {node.group_id}")
    
    # 测试用例4：便捷函数测试
    print("\n" + "=" * 70)
    print("\n[测试4] 便捷函数测试")
    print("测试 mark_task_schedule...")
    scheduled_obj = mark_task_schedule(subtasks)
    print(f"✅ 调用成功")
    print(f"调度节点数量: {len(scheduled_obj.scheduled_nodes)}")
    print(f"并行组数量: {len(scheduled_obj.parallel_groups)}")
    print(f"串行批次数量: {len(scheduled_obj.serial_batches)}")
    
    print("\n测试 mark_and_get_dict...")
    result_dict = mark_and_get_dict(subtasks)
    print(f"✅ 调用成功")
    print(f"  原始有效: {result_dict['original_valid']}")
    print(f"  节点数量: {result_dict['nodes_count']}")
    print(f"  并行组数量: {result_dict['parallel_groups_count']}")
    print(f"  串行批次数量: {result_dict['serial_batches_count']}")
    print(f"  拓扑排序: {result_dict['topology_order']}")
    
    # 测试用例5：调度结果转字典
    print("\n" + "=" * 70)
    print("\n[测试5] 调度结果转字典")
    dict_data = marker.schedule_to_dict(scheduled)
    print(f"✅ 转换成功")
    print(f"字典键: {list(dict_data.keys())}")
    print(f"原始有效: {dict_data['original_valid']}")
    print(f"节点数量: {dict_data['nodes_count']}")
    print(f"并行组数量: {dict_data['parallel_groups_count']}")
    print(f"串行批次数量: {dict_data['serial_batches_count']}")
    
    print("\n" + "=" * 70)
    print("测试完成！")
    print("=" * 70)


if __name__ == "__main__":
    test_schedule_marker()
