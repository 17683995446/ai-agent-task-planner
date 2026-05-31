"""
冗余过滤模块测试
基于第一性原理的AI Agent任务规划系统
"""

import sys
import os

# 确保能导入模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from redundancy_filter import RedundancyFilter, filter_task_redundancy, filter_and_get_dict
from subtask_splitter import SubTaskSplitter, SplitStrategy
from subtask_node import SubTaskNode, DependencyType, Dependency


def create_test_tasks_with_redundancy() -> List[SubTaskNode]:
    """创建有冗余的测试任务"""
    tasks = []
    
    # 正常任务
    task_a = SubTaskNode(
        node_id="task-a",
        name="需求分析",
        description="分析用户需求",
        sequence=1
    )
    tasks.append(task_a)
    
    # 重复任务
    task_a_dup = SubTaskNode(
        node_id="task-a-duplicate",
        name="需求分析",
        description="分析用户需求",
        sequence=2
    )
    tasks.append(task_a_dup)
    
    task_b = SubTaskNode(
        node_id="task-b",
        name="设计方案",
        description="制定系统设计方案",
        sequence=3
    )
    tasks.append(task_b)
    
    # 无贡献任务
    task_useless = SubTaskNode(
        node_id="task-useless",
        name="无关的杂事",
        description="做一些与目标无关的事情",
        sequence=4
    )
    tasks.append(task_useless)
    
    task_c = SubTaskNode(
        node_id="task-c",
        name="系统开发",
        description="执行系统开发",
        sequence=5
    )
    tasks.append(task_c)
    
    # 添加依赖
    from subtask_node import Dependency
    task_b.dependencies.append(Dependency(
        dependency_id="task-a",
        dependency_type=DependencyType.HARD,
        description="依赖需求分析"
    ))
    
    task_c.dependencies.append(Dependency(
        dependency_id="task-b",
        dependency_type=DependencyType.HARD,
        description="依赖设计方案"
    ))
    
    return tasks


def test_redundancy_filter():
    """测试冗余过滤模块"""
    print("=" * 70)
    print("冗余过滤模块测试")
    print("=" * 70)
    
    filter_obj = RedundancyFilter()
    
    # 测试用例1：过滤有冗余的任务
    print("\n" + "=" * 70)
    print("\n[测试1] 过滤有冗余的任务")
    redundant_tasks = create_test_tasks_with_redundancy()
    print(f"原始任务数量: {len(redundant_tasks)}")
    print("原始任务列表:")
    for i, task in enumerate(redundant_tasks, 1):
        print(f"  {i}. [{task.node_id}] {task.name}")
    
    filtered = filter_obj.filter_redundancy(redundant_tasks)
    print(f"\n✅ 过滤完成")
    print(f"过滤成功: {filtered.is_success}")
    print(f"原始数量: {filtered.original_count}")
    print(f"最终数量: {filtered.final_count}")
    print(f"移除数量: {filtered.original_count - filtered.final_count}")
    
    print("\n保留的任务:")
    for i, task in enumerate(filtered.filtered_nodes, 1):
        print(f"  {i}. [{task.node_id}] {task.name}")
    
    print("\n移除的任务:")
    for i, removed in enumerate(filtered.removed_nodes, 1):
        print(f"  {i}. [{removed.node_id}] {removed.name}")
        print(f"     原因: {removed.reason.value} - {removed.description}")
        if removed.alternative_nodes:
            print(f"     替代: {removed.alternative_nodes}")
    
    # 测试用例2：正常任务过滤（不应该有任何移除）
    print("\n" + "=" * 70)
    print("\n[测试2] 正常任务过滤")
    splitter = SubTaskSplitter()
    normal_tasks = splitter.split_task(
        "开发一个Web应用",
        task_id="task-web",
        strategy=SplitStrategy.BY_PHASE
    )
    print(f"正常任务数量: {len(normal_tasks)}")
    
    filtered_normal = filter_obj.filter_redundancy(normal_tasks)
    print(f"✅ 过滤完成")
    print(f"过滤成功: {filtered_normal.is_success}")
    print(f"原始数量: {filtered_normal.original_count}")
    print(f"最终数量: {filtered_normal.final_count}")
    print(f"移除数量: {filtered_normal.original_count - filtered_normal.final_count}")
    
    # 测试用例3：便捷函数测试
    print("\n" + "=" * 70)
    print("\n[测试3] 便捷函数测试")
    print("测试 filter_task_redundancy...")
    filtered_obj = filter_task_redundancy(redundant_tasks)
    print(f"✅ 调用成功")
    print(f"过滤成功: {filtered_obj.is_success}")
    print(f"最终数量: {filtered_obj.final_count}")
    
    print("\n测试 filter_and_get_dict...")
    result_dict = filter_and_get_dict(redundant_tasks)
    print(f"✅ 调用成功")
    print(f"  原始数量: {result_dict['original_count']}")
    print(f"  最终数量: {result_dict['final_count']}")
    print(f"  移除数量: {result_dict['removed_count']}")
    print(f"  过滤成功: {result_dict['is_success']}")
    
    # 测试用例4：过滤结果转字典
    print("\n" + "=" * 70)
    print("\n[测试4] 过滤结果转字典")
    dict_data = filter_obj.filtered_to_dict(filtered)
    print(f"✅ 转换成功")
    print(f"字典键: {list(dict_data.keys())}")
    print(f"原始数量: {dict_data['original_count']}")
    print(f"最终数量: {dict_data['final_count']}")
    print(f"移除数量: {dict_data['removed_count']}")
    print(f"过滤成功: {dict_data['is_success']}")
    
    print("\n保留的节点:")
    for i, node in enumerate(dict_data['retained_nodes'], 1):
        print(f"  {i}. [{node['node_id']}] {node['name']}")
    
    print("\n移除的节点:")
    for i, node in enumerate(dict_data['removed_nodes'], 1):
        print(f"  {i}. [{node['node_id']}] {node['name']}")
        print(f"     原因: {node['reason']}")
    
    print("\n" + "=" * 70)
    print("测试完成！")
    print("=" * 70)


if __name__ == "__main__":
    test_redundancy_filter()
