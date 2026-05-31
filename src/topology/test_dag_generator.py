"""
DAG生成器测试
基于第一性原理的AI Agent任务规划系统
"""

import sys
import os

# 确保能导入模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dag_generator import DAGGenerator, generate_topology, generate_topology_dict
from subtask_splitter import SubTaskSplitter, SplitStrategy


def test_dag_generator():
    """测试DAG生成器"""
    print("=" * 70)
    print("标准DAG有向无环图生成组件测试")
    print("=" * 70)
    
    generator = DAGGenerator()
    
    # 首先拆分一些子任务并计算依赖
    print("\n[步骤1] 准备测试任务")
    splitter = SubTaskSplitter()
    task_desc = "开发一个完整的Web应用系统"
    subtasks = splitter.split_task(task_desc, "task-webapp", SplitStrategy.BY_PHASE)
    print(f"✅ 拆分完成，共 {len(subtasks)} 个子任务")
    
    # 测试用例1：生成DAG
    print("\n" + "=" * 70)
    print("\n[测试1] 生成DAG拓扑结构")
    topology = generator.generate_dag(subtasks)
    print(f"✅ DAG生成完成")
    
    print(f"拓扑结构有效性: {topology.is_valid}")
    if not topology.is_valid:
        print(f"验证错误: {topology.validation_errors}")
    
    print(f"节点数量: {len(topology.nodes)}")
    print(f"边数量: {len(topology.edges)}")
    print(f"拓扑排序: {topology.topology_order}")
    
    # 测试用例2：查看节点详情
    print("\n" + "=" * 70)
    print("\n[测试2] 节点详情")
    for i, node in enumerate(topology.nodes, 1):
        print(f"\n节点 {i}: {node.name}")
        print(f"  ID: {node.node_id}")
        print(f"  序号: {node.sequence}")
        print(f"  优先级: {node.priority}")
        print(f"  权重: {node.weight}")
        print(f"  状态: {node.status}")
        print(f"  输入: {len(node.inputs)} 个")
        print(f"  输出: {len(node.outputs)} 个")
        print(f"  依赖: {len(node.dependencies)} 个")
    
    # 测试用例3：查看边详情
    print("\n" + "=" * 70)
    print("\n[测试3] 边详情")
    for i, edge in enumerate(topology.edges, 1):
        print(f"边 {i}: {edge.from_node} -> {edge.to_node}")
        print(f"  类型: {edge.edge_type}")
        print(f"  描述: {edge.description}")
    
    # 测试用例4：拓扑排序验证
    print("\n" + "=" * 70)
    print("\n[测试4] 拓扑排序验证")
    print(f"拓扑排序:")
    for i, node_id in enumerate(topology.topology_order, 1):
        node = next((n for n in topology.nodes if n.node_id == node_id), None)
        if node:
            print(f"  {i}. {node.name} (优先级: {node.priority})")
    
    # 测试用例5：便捷函数测试
    print("\n" + "=" * 70)
    print("\n[测试5] 便捷函数测试")
    topology_obj = generate_topology(subtasks)
    print(f"✅ generate_topology 调用成功")
    print(f"拓扑结构有效性: {topology_obj.is_valid}")
    
    topology_dict = generate_topology_dict(subtasks)
    print(f"✅ generate_topology_dict 调用成功")
    print(f"字典键: {list(topology_dict.keys())}")
    print(f"节点数: {len(topology_dict['nodes'])}")
    print(f"边数: {len(topology_dict['edges'])}")
    
    # 测试用例6：拓扑结构转换为字典
    print("\n" + "=" * 70)
    print("\n[测试6] 拓扑结构转换为字典")
    dict_data = generator.topology_to_dict(topology)
    print(f"✅ 转换成功")
    print(f"字典键: {list(dict_data.keys())}")
    print(f"拓扑有效性: {dict_data['is_valid']}")
    print(f"拓扑排序: {dict_data['topology_order']}")
    
    print("\n" + "=" * 70)
    print("测试完成！")
    print("=" * 70)


if __name__ == "__main__":
    test_dag_generator()
