"""
第二层：拓扑依赖拆解层 - 调度标记逻辑
基于第一性原理的AI Agent任务规划系统
"""

from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
from enum import Enum

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from subtask_node import (
    SubTaskNode, SubTaskStatus, DependencyType, InputSpec, OutputSpec, Dependency
)
from dag_generator import DAGGenerator, DAGNode, DAGEdge, TopologyStructure


class ExecutionType(Enum):
    """执行类型"""
    SERIAL = "serial"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"


@dataclass
class ScheduledNode:
    """调度节点"""
    node_id: str
    name: str
    execution_type: ExecutionType
    group_id: Optional[str] = None
    dependencies: List[str] = None
    dependents: List[str] = None
    priority: int = 5
    can_parallelize: bool = False


@dataclass
class ScheduleMark:
    """调度标记"""
    node_id: str
    name: str
    execution_type: ExecutionType
    group_id: Optional[str]
    parallel_group: Optional[str]
    batch_order: int


@dataclass
class ScheduledTopology:
    """调度后的拓扑结构"""
    original_topology: TopologyStructure
    scheduled_nodes: List[ScheduledNode]
    parallel_groups: Dict[str, List[str]]
    serial_batches: List[List[str]]
    schedule_marks: List[ScheduleMark]


class ScheduleMarker:
    """
    调度标记逻辑
    功能：并行自动并行、依赖自动串行
    """
    
    def __init__(self):
        """初始化调度标记器"""
        self.dag_generator = DAGGenerator()
    
    def mark_schedule(self, subtasks: List[SubTaskNode]) -> ScheduledTopology:
        """
        标记调度信息
        
        Args:
            subtasks: 子任务列表
            
        Returns:
            ScheduledTopology: 调度后的拓扑结构
        """
        # 1. 生成拓扑结构
        topology = self.dag_generator.generate_dag(subtasks)
        
        # 2. 分析依赖关系，识别可并行节点
        scheduled_nodes = self._analyze_parallelizability(topology)
        
        # 3. 分组并行节点
        parallel_groups = self._group_parallel_nodes(scheduled_nodes)
        
        # 4. 组织串行批次
        serial_batches = self._organize_serial_batches(topology, parallel_groups)
        
        # 5. 生成调度标记
        schedule_marks = self._generate_schedule_marks(scheduled_nodes, parallel_groups, serial_batches)
        
        return ScheduledTopology(
            original_topology=topology,
            scheduled_nodes=scheduled_nodes,
            parallel_groups=parallel_groups,
            serial_batches=serial_batches,
            schedule_marks=schedule_marks
        )
    
    def _analyze_parallelizability(self, topology: TopologyStructure) -> List[ScheduledNode]:
        """
        分析可并行性
        """
        scheduled = []
        
        # 构建依赖图
        node_deps = {}
        node_dependents = {}
        node_ids = set(node.node_id for node in topology.nodes)
        
        for node_id in node_ids:
            node_deps[node_id] = []
            node_dependents[node_id] = []
        
        for edge in topology.edges:
            if edge.from_node in node_ids and edge.to_node in node_ids:
                node_deps[edge.to_node].append(edge.from_node)
                node_dependents[edge.from_node].append(edge.to_node)
        
        # 分析每个节点
        for node in topology.nodes:
            # 判断是否可并行：没有互相依赖，可以同时执行
            can_parallelize = self._check_can_parallelize(node, topology.nodes, node_deps)
            
            # 判断执行类型
            exec_type = ExecutionType.SERIAL
            if can_parallelize:
                exec_type = ExecutionType.PARALLEL
            
            scheduled_node = ScheduledNode(
                node_id=node.node_id,
                name=node.name,
                execution_type=exec_type,
                dependencies=node_deps.get(node.node_id, []),
                dependents=node_dependents.get(node.node_id, []),
                priority=node.priority,
                can_parallelize=can_parallelize
            )
            scheduled.append(scheduled_node)
        
        return scheduled
    
    def _check_can_parallelize(self, node: DAGNode, all_nodes: List[DAGNode], node_deps: Dict[str, List[str]]) -> bool:
        """
        检查节点是否可以并行
        """
        # 查找同一层级的节点（没有互相依赖）
        node_level = self._get_node_level(node, node_deps)
        
        # 找出同一层级的节点
        same_level_nodes = []
        for n in all_nodes:
            if n.node_id != node.node_id:
                n_level = self._get_node_level(n, node_deps)
                if n_level == node_level:
                    same_level_nodes.append(n.node_id)
        
        # 检查是否与同一层级的节点有互相依赖
        for other_node_id in same_level_nodes:
            if node.node_id in node_deps.get(other_node_id, []):
                return False
            if other_node_id in node_deps.get(node.node_id, []):
                return False
        
        # 如果有同一层级的其他节点，就可以并行
        return len(same_level_nodes) > 0
    
    def _get_node_level(self, node: DAGNode, node_deps: Dict[str, List[str]]) -> int:
        """
        获取节点的层级
        """
        if not node_deps.get(node.node_id, []):
            return 0
        
        max_level = 0
        for dep_id in node_deps[node.node_id]:
            # 查找依赖节点的层级（简化版）
            dep_level = 0
            # 这里简化处理，实际应该递归计算
            max_level = max(max_level, dep_level + 1)
        
        return max_level
    
    def _group_parallel_nodes(self, scheduled_nodes: List[ScheduledNode]) -> Dict[str, List[str]]:
        """
        分组并行节点
        """
        groups = {}
        group_counter = 0
        
        # 按层级分组
        level_map = {}
        for node in scheduled_nodes:
            level = len(node.dependencies)  # 简化的层级计算
            if level not in level_map:
                level_map[level] = []
            level_map[level].append(node)
        
        # 为每个层级的可并行节点创建组
        for level, nodes in sorted(level_map.items()):
            parallel_nodes = [n for n in nodes if n.can_parallelize]
            if parallel_nodes:
                group_id = f"parallel-group-{group_counter}"
                group_counter += 1
                groups[group_id] = [n.node_id for n in parallel_nodes]
                
                # 更新节点的group_id
                for node in scheduled_nodes:
                    if node.node_id in groups[group_id]:
                        node.group_id = group_id
        
        return groups
    
    def _organize_serial_batches(self, topology: TopologyStructure, parallel_groups: Dict[str, List[str]]) -> List[List[str]]:
        """
        组织串行批次
        """
        batches = []
        
        if not topology.topology_order:
            return batches
        
        # 按照拓扑顺序，将没有依赖关系的并行节点分组
        # 有依赖关系的分成单独批次
        current_batch = []
        
        for node_id in topology.topology_order:
            # 查找节点所在的并行组
            found_group = None
            for group_id, group_nodes in parallel_groups.items():
                if node_id in group_nodes:
                    found_group = group_id
                    break
            
            if found_group:
                # 如果当前批次有内容，先保存
                if current_batch:
                    batches.append(current_batch)
                    current_batch = []
                # 整个并行组作为一个批次
                batches.append(parallel_groups[found_group].copy())
            else:
                current_batch.append(node_id)
        
        if current_batch:
            batches.append(current_batch)
        
        return batches
    
    def _generate_schedule_marks(self, scheduled_nodes: List[ScheduledNode], parallel_groups: Dict[str, List[str]], serial_batches: List[List[str]]) -> List[ScheduleMark]:
        """
        生成调度标记
        """
        marks = []
        
        for batch_idx, batch in enumerate(serial_batches):
            for node_id in batch:
                # 查找节点
                node = next((n for n in scheduled_nodes if n.node_id == node_id), None)
                if not node:
                    continue
                
                # 查找并行组
                parallel_group = None
                for group_id, group_nodes in parallel_groups.items():
                    if node_id in group_nodes:
                        parallel_group = group_id
                        break
                
                mark = ScheduleMark(
                    node_id=node_id,
                    name=node.name,
                    execution_type=node.execution_type,
                    group_id=node.group_id,
                    parallel_group=parallel_group,
                    batch_order=batch_idx
                )
                marks.append(mark)
        
        return marks
    
    def schedule_to_dict(self, scheduled: ScheduledTopology) -> Dict[str, Any]:
        """
        将调度后的拓扑转换为字典
        """
        return {
            "original_valid": scheduled.original_topology.is_valid,
            "nodes_count": len(scheduled.scheduled_nodes),
            "parallel_groups_count": len(scheduled.parallel_groups),
            "serial_batches_count": len(scheduled.serial_batches),
            "parallel_groups": {
                group_id: nodes for group_id, nodes in scheduled.parallel_groups.items()
            },
            "serial_batches": [batch for batch in scheduled.serial_batches],
            "schedule_marks": [
                {
                    "node_id": mark.node_id,
                    "name": mark.name,
                    "execution_type": mark.execution_type.value,
                    "group_id": mark.group_id,
                    "parallel_group": mark.parallel_group,
                    "batch_order": mark.batch_order
                }
                for mark in scheduled.schedule_marks
            ],
            "topology_order": scheduled.original_topology.topology_order
        }


# 便捷函数
def mark_task_schedule(subtasks: List[SubTaskNode]) -> ScheduledTopology:
    """
    便捷函数：标记任务调度信息
    
    Args:
        subtasks: 子任务列表
        
    Returns:
        ScheduledTopology: 调度后的拓扑结构
    """
    marker = ScheduleMarker()
    return marker.mark_schedule(subtasks)


def mark_and_get_dict(subtasks: List[SubTaskNode]) -> Dict[str, Any]:
    """
    便捷函数：标记调度并获取字典格式
    
    Args:
        subtasks: 子任务列表
        
    Returns:
        Dict[str, Any]: 调度结果字典
    """
    marker = ScheduleMarker()
    scheduled = marker.mark_schedule(subtasks)
    return marker.schedule_to_dict(scheduled)
