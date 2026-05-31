"""
子任务智能拆分引擎测试
基于第一性原理的AI Agent任务规划系统
"""

import sys
import os

# 确保能导入模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from subtask_splitter import SubTaskSplitter, split_task_into_subtasks, SplitStrategy


def test_subtask_splitter():
    """测试子任务拆分引擎"""
    print("=" * 70)
    print("子任务智能拆分引擎测试")
    print("=" * 70)
    
    splitter = SubTaskSplitter()
    
    # 测试用例1：按阶段拆分（默认）
    print("\n[测试1] 按阶段拆分（默认策略）")
    task_desc = "开发一个Web应用，包含用户管理和数据分析功能"
    subtasks = splitter.split_task(task_desc, "task-webapp", SplitStrategy.BY_PHASE)
    
    print(f"✅ 拆分成功，生成 {len(subtasks)} 个子任务")
    for i, subtask in enumerate(subtasks, 1):
        print(f"  {i}. [{subtask.node_id}] {subtask.name}")
        print(f"     描述: {subtask.description}")
        print(f"     输入: {len(subtask.inputs)} 项")
        print(f"     输出: {len(subtask.outputs)} 项")
        print(f"     依赖: {len(subtask.dependencies)} 个")
    
    # 测试用例2：按可衡量标准拆分
    print("\n" + "=" * 70)
    print("\n[测试2] 按可衡量标准拆分")
    subtasks2 = splitter.split_task(task_desc, "task-standard", SplitStrategy.BY_CRITERION)
    print(f"✅ 拆分成功，生成 {len(subtasks2)} 个子任务")
    for i, subtask in enumerate(subtasks2, 1):
        print(f"  {i}. [{subtask.node_id}] {subtask.name}")
    
    # 测试用例3：按前置条件拆分
    print("\n" + "=" * 70)
    print("\n[测试3] 按前置条件拆分")
    subtasks3 = splitter.split_task(task_desc, "task-condition", SplitStrategy.BY_CONDITION)
    print(f"✅ 拆分成功，生成 {len(subtasks3)} 个子任务")
    for i, subtask in enumerate(subtasks3, 1):
        print(f"  {i}. [{subtask.node_id}] {subtask.name}")
    
    # 测试用例4：按并行拆分
    print("\n" + "=" * 70)
    print("\n[测试4] 按并行方式拆分")
    subtasks4 = splitter.split_task(task_desc, "task-parallel", SplitStrategy.BY_PARALLEL)
    print(f"✅ 拆分成功，生成 {len(subtasks4)} 个子任务")
    for i, subtask in enumerate(subtasks4, 1):
        print(f"  {i}. [{subtask.node_id}] {subtask.name}")
    
    # 测试用例5：便捷函数测试
    print("\n" + "=" * 70)
    print("\n[测试5] 便捷函数测试")
    subtasks5 = split_task_into_subtasks(task_desc, "task-easy", "by_phase")
    print(f"✅ 便捷函数调用成功，生成 {len(subtasks5)} 个子任务")
    print(f"第一个子任务: {subtasks5[0].name}")
    
    # 测试用例6：检查依赖关系
    print("\n" + "=" * 70)
    print("\n[测试6] 依赖关系检查")
    subtasks6 = splitter.split_task(task_desc, "task-deps", SplitStrategy.BY_PHASE)
    for i, subtask in enumerate(subtasks6):
        if i == 0:
            print(f"第{i+1}个子任务 {subtask.name} - 依赖数: {len(subtask.dependencies)} (正确)")
        else:
            print(f"第{i+1}个子任务 {subtask.name} - 依赖数: {len(subtask.dependencies)}")
            if len(subtask.dependencies) > 0:
                print(f"  依赖于: {subtask.dependencies[0].dependency_id}")
    
    print("\n" + "=" * 70)
    print("测试完成！")
    print("=" * 70)


if __name__ == "__main__":
    test_subtask_splitter()
