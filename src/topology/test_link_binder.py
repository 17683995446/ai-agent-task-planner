"""
链路绑定逻辑测试
基于第一性原理的AI Agent任务规划系统
"""

import sys
import os

# 确保能导入模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from link_binder import LinkBinder, validate_task_links, validate_and_get_dict
from subtask_splitter import SubTaskSplitter, SplitStrategy
from subtask_node import SubTaskNode, DependencyType, Dependency, InputSpec, OutputSpec


def create_test_tasks_with_good_links() -> List[SubTaskNode]:
    """创建有良好链路绑定的测试任务"""
    tasks = []
    
    # 任务1：准备数据
    task1 = SubTaskNode(
        node_id="task-1",
        name="准备数据",
        description="准备处理所需的数据",
        sequence=1
    )
    task1.add_output("raw_data", "dict", "原始数据")
    task1.add_output("config", "dict", "配置信息")
    tasks.append(task1)
    
    # 任务2：处理数据
    task2 = SubTaskNode(
        node_id="task-2",
        name="处理数据",
        description="处理和清洗数据",
        sequence=2
    )
    task2.add_input("raw_data", "dict", required=True, description="原始数据")
    task2.add_output("processed_data", "dict", "处理后的数据")
    tasks.append(task2)
    
    # 任务3：分析结果
    task3 = SubTaskNode(
        node_id="task-3",
        name="分析结果",
        description="分析处理结果",
        sequence=3
    )
    task3.add_input("processed_data", "dict", required=True, description="处理后的数据")
    task3.add_output("analysis_result", "dict", "分析结果")
    tasks.append(task3)
    
    # 设置依赖和来源
    from subtask_node import Dependency
    task2.dependencies.append(Dependency(
        dependency_id="task-1",
        dependency_type=DependencyType.HARD,
        description="依赖数据准备"
    ))
    task2.inputs[0].source = "task-1"
    
    task3.dependencies.append(Dependency(
        dependency_id="task-2",
        dependency_type=DependencyType.HARD,
        description="依赖数据处理"
    ))
    task3.inputs[0].source = "task-2"
    
    return tasks


def create_test_tasks_with_bad_links() -> List[SubTaskNode]:
    """创建有问题链路绑定的测试任务"""
    tasks = []
    
    # 任务1：准备数据
    task1 = SubTaskNode(
        node_id="task-1",
        name="准备数据",
        description="准备处理所需的数据",
        sequence=1
    )
    task1.add_output("raw_data", "dict", "原始数据")
    task1.add_output("unnecessary_data", "list", "不必要的数据")
    tasks.append(task1)
    
    # 任务2：处理数据（缺少输入来源）
    task2 = SubTaskNode(
        node_id="task-2",
        name="处理数据",
        description="处理和清洗数据",
        sequence=2
    )
    task2.add_input("raw_data", "dict", required=True, description="原始数据")
    task2.add_output("processed_data", "dict", "处理后的数据")
    tasks.append(task2)
    
    # 任务3：分析结果（来源错误）
    task3 = SubTaskNode(
        node_id="task-3",
        name="分析结果",
        description="分析处理结果",
        sequence=3
    )
    task3.add_input("wrong_data", "dict", required=True, description="错误的输入")
    task3.add_output("analysis_result", "dict", "分析结果")
    tasks.append(task3)
    
    # 设置依赖但错误地设置来源
    from subtask_node import Dependency
    task2.dependencies.append(Dependency(
        dependency_id="task-1",
        dependency_type=DependencyType.HARD,
        description="依赖数据准备"
    ))
    
    task3.dependencies.append(Dependency(
        dependency_id="task-2",
        dependency_type=DependencyType.HARD,
        description="依赖数据处理"
    ))
    task3.inputs[0].source = "non-existent-task"
    
    return tasks


def test_link_binder():
    """测试链路绑定逻辑"""
    print("=" * 70)
    print("链路绑定逻辑测试")
    print("=" * 70)
    
    binder = LinkBinder()
    
    # 测试用例1：良好链路绑定验证
    print("\n" + "=" * 70)
    print("\n[测试1] 良好链路绑定验证")
    good_tasks = create_test_tasks_with_good_links()
    print(f"任务数量: {len(good_tasks)}")
    
    validated_good = binder.validate_links(good_tasks)
    print(f"✅ 验证完成")
    print(f"验证通过: {validated_good.is_valid}")
    print(f"有效绑定数量: {validated_good.valid_count}")
    print(f"问题数量: {validated_good.issue_count}")
    
    print("\n绑定链路:")
    for i, link in enumerate(validated_good.bound_links, 1):
        print(f"  {i}. [{link.from_node}] → {link.from_output}")
        print(f"     ↓")
        print(f"     [{link.to_node}] ← {link.to_input}")
        print(f"     绑定类型: {link.bind_type}")
    
    # 测试用例2：有问题链路绑定验证
    print("\n" + "=" * 70)
    print("\n[测试2] 有问题链路绑定验证")
    bad_tasks = create_test_tasks_with_bad_links()
    print(f"任务数量: {len(bad_tasks)}")
    
    validated_bad = binder.validate_links(bad_tasks)
    print(f"✅ 验证完成")
    print(f"验证通过: {validated_bad.is_valid}")
    print(f"有效绑定数量: {validated_bad.valid_count}")
    print(f"问题数量: {validated_bad.issue_count}")
    
    print("\n发现的问题:")
    for i, issue in enumerate(validated_bad.issues, 1):
        print(f"  {i}. [{issue.node_id}] {issue.name}")
        print(f"     问题类型: {issue.issue_type.value}")
        print(f"     描述: {issue.description}")
        if issue.related_node:
            print(f"     相关节点: {issue.related_node}")
        if issue.related_spec:
            print(f"     相关规格: {issue.related_spec}")
    
    # 测试用例3：正常任务验证
    print("\n" + "=" * 70)
    print("\n[测试3] 正常任务验证")
    splitter = SubTaskSplitter()
    normal_tasks = splitter.split_task(
        "开发一个Web应用",
        task_id="task-web",
        strategy=SplitStrategy.BY_PHASE
    )
    print(f"正常任务数量: {len(normal_tasks)}")
    
    validated_normal = binder.validate_links(normal_tasks)
    print(f"✅ 验证完成")
    print(f"验证通过: {validated_normal.is_valid}")
    print(f"有效绑定数量: {validated_normal.valid_count}")
    print(f"问题数量: {validated_normal.issue_count}")
    
    # 测试用例4：便捷函数测试
    print("\n" + "=" * 70)
    print("\n[测试4] 便捷函数测试")
    print("测试 validate_task_links...")
    validated_obj = validate_task_links(good_tasks)
    print(f"✅ 调用成功")
    print(f"验证通过: {validated_obj.is_valid}")
    print(f"有效绑定数量: {validated_obj.valid_count}")
    
    print("\n测试 validate_and_get_dict...")
    result_dict = validate_and_get_dict(good_tasks)
    print(f"✅ 调用成功")
    print(f"  验证通过: {result_dict['is_valid']}")
    print(f"  有效绑定: {result_dict['valid_count']}")
    print(f"  问题数量: {result_dict['issue_count']}")
    
    # 测试用例5：验证结果转字典
    print("\n" + "=" * 70)
    print("\n[测试5] 验证结果转字典")
    dict_data = binder.validated_to_dict(validated_good)
    print(f"✅ 转换成功")
    print(f"字典键: {list(dict_data.keys())}")
    print(f"验证通过: {dict_data['is_valid']}")
    print(f"有效绑定: {dict_data['valid_count']}")
    
    print("\n绑定链路:")
    for i, link in enumerate(dict_data['bound_links'], 1):
        print(f"  {i}. [{link['from_node']}] → {link['from_output']}")
        print(f"     ↓")
        print(f"     [{link['to_node']}] ← {link['to_input']}")
    
    print("\n" + "=" * 70)
    print("测试完成！")
    print("=" * 70)


if __name__ == "__main__":
    test_link_binder()
