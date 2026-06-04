"""
第二层接口封装 - 拓扑依赖拆解层接口
基于第一性原理的AI Agent任务规划系统

核心功能：
- 定义拓扑层标准接口
- 封装所有拓扑操作
- 对外提供统一调用方式
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from task_modeling.task_struct import Task
from topology.subtask_node import SubTaskNode
from topology.subtask_splitter import split_task_into_subtasks
from topology.dependency_calculator import calculate_task_dependencies
from topology.dag_generator import generate_topology
from topology.topology_corrector import correct_task_topology


@dataclass
class TopologyResult:
    """拓扑结果"""
    success: bool
    subtasks: List[SubTaskNode] = field(default_factory=list)
    error_message: str = ""
    topology_info: Dict[str, Any] = field(default_factory=dict)


class TopologyInterface:
    """
    拓扑依赖拆解层接口
    
    功能：
    - 封装所有拓扑操作
    - 提供统一调用入口
    - 实现错误处理和日志记录
    """
    
    def __init__(self):
        """初始化拓扑接口"""
        pass
    
    def decompose_task(self, task: Task) -> TopologyResult:
        """
        分解任务为子任务拓扑
        
        Args:
            task: 任务对象
            
        Returns:
            TopologyResult: 拓扑结果
        """
        try:
            # 1. 子任务拆分
            subtasks = split_task_into_subtasks(task)
            
            # 2. 依赖计算
            subtasks = calculate_task_dependencies(subtasks)
            
            # 3. DAG生成
            topology = generate_topology(subtasks)
            
            # 4. 拓扑纠错
            corrected = correct_task_topology(subtasks)
            
            return TopologyResult(
                success=True,
                subtasks=subtasks,
                topology_info={
                    "subtasks_count": len(subtasks),
                    "topology_valid": topology.is_valid if hasattr(topology, 'is_valid') else True,
                    "corrections_applied": len(corrected.corrections_applied) if hasattr(corrected, 'corrections_applied') else 0
                }
            )
        except Exception as e:
            return TopologyResult(
                success=False,
                error_message=str(e)
            )
    
    def get_execution_order(self, subtasks: List[SubTaskNode]) -> List[str]:
        """
        获取执行顺序
        
        Args:
            subtasks: 子任务列表
            
        Returns:
            List[str]: 执行顺序（节点ID列表）
        """
        try:
            # 拓扑排序
            in_degree = {}
            for subtask in subtasks:
                if subtask.node_id not in in_degree:
                    in_degree[subtask.node_id] = 0
                for dep in subtask.dependencies:
                    in_degree[subtask.node_id] = in_degree.get(subtask.node_id, 0) + 1
            
            # Kahn算法
            queue = [node_id for node_id, degree in in_degree.items() if degree == 0]
            result = []
            
            while queue:
                node_id = queue.pop(0)
                result.append(node_id)
                
                # 找到依赖于此节点的其他节点
                for subtask in subtasks:
                    for dep in subtask.dependencies:
                        if dep.source_id == node_id:
                            in_degree[subtask.node_id] -= 1
                            if in_degree[subtask.node_id] == 0:
                                queue.append(subtask.node_id)
            
            return result
        except Exception:
            # 返回原始顺序
            return [s.node_id for s in subtasks]
