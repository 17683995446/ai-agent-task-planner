"""
子任务节点数据结构测试
基于第一性原理的AI Agent任务规划系统
"""

import sys
import os

# 确保能导入模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from subtask_node import (
    SubTaskNode, SubTaskStatus, DependencyType, InputSpec, OutputSpec, Dependency
)


def test_subtask_node():
    """测试子任务节点数据结构"""
    print("=" * 70)
    print("子任务节点数据结构测试")
    print("=" * 70)
    
    print("\n[测试1] 创建基本节点创建")
    node = SubTaskNode(
        node_id="subtask-001",
        name="数据预处理",
        description="对输入数据进行清洗和标准化",
        parent_task_id="task-001",
        sequence=1
    )
    print("✅ 节点创建成功")
    print(f"节点ID: {node.node_id}")
    print(f"节点名称: {node.name}")
    print(f"初始状态: {node.status.value}")
    
    print("\n[测试2] 添加输入输出")
    node.add_input("raw_data", "dict", required=True, description="原始输入数据")
    node.add_input("config", "dict", required=False, description="配置参数")
    node.add_output("processed_data", "dict", description="处理后的数据")
    print(f"✅ 输入输出添加成功")
    print(f"输入数量: {len(node.inputs)}")
    print(f"输出数量: {len(node.outputs)}")
    
    print("\n[测试3] 添加依赖关系")
    node.add_dependency("subtask-000", DependencyType.HARD, "前置数据准备")
    print(f"✅ 依赖关系添加成功")
    print(f"依赖数量: {len(node.dependencies)}")
    print(f"依赖ID: {node.dependencies[0].dependency_id}")
    
    print("\n[测试4] 状态管理")
    print(f"当前状态: {node.status.value}")
    node.mark_started()
    print(f"开始执行后: {node.status.value}")
    print(f"开始时间记录: {node.start_time}")
    
    node.mark_completed()
    print(f"完成后: {node.status.value}")
    print(f"结束时间记录: {node.end_time}")
    print(f"实际耗时: {node.actual_duration}秒")
    
    print("\n[测试5] 序列化与反序列化")
    dict_data = node.to_dict()
    print(f"✅ 序列化成功，字典长度: {len(dict_data)}")
    
    restored_node = SubTaskNode.from_dict(dict_data)
    print(f"✅ 反序列化成功")
    print(f"节点ID一致: {restored_node.node_id == node.node_id}")
    print(f"节点名称一致: {restored_node.name == node.name}")
    print(f"状态一致: {restored_node.status == node.status}")
    
    print("\n" + "=" * 70)
    print("测试完成！")
    print("=" * 70)


if __name__ == "__main__":
    test_subtask_node()
