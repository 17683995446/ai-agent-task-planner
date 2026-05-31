"""
第二层：拓扑依赖拆解层 - 冗余过滤模块
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
from schedule_marker import ScheduledTopology, ScheduledNode


class FilterReason(Enum):
    """过滤原因"""
    REDUNDANT = "redundant"
    NO_CONTRIBUTION = "no_contribution"
    DUPLICATE = "duplicate"
    DEPENDENCY_BROKEN = "dependency_broken"
    NOT_REACHABLE = "not_reachable"


@dataclass
class FilteredNode:
    """被过滤的节点"""
    node_id: str
    name: str
    reason: FilterReason
    description: str
    alternative_nodes: Optional[List[str]] = None


@dataclass
class FilteredTopology:
    """过滤后的拓扑结构"""
    original_topology: TopologyStructure
    original_count: int
    filtered_nodes: List[SubTaskNode]
    removed_nodes: List[FilteredNode]
    is_success: bool
    final_count: int


class RedundancyFilter:
    """
    冗余过滤模块
    功能：所有子任务100%服务最终目标
    """
    
    def __init__(self):
        """初始化冗余过滤器"""
        self.dag_generator = DAGGenerator()
    
    def filter_redundancy(self, subtasks: List[SubTaskNode]) -> FilteredTopology:
        """
        过滤冗余任务
        
        Args:
            subtasks: 子任务列表
            
        Returns:
            FilteredTopology: 过滤后的拓扑结构
        """
        original_count = len(subtasks)
        
        # 1. 生成拓扑结构
        topology = self.dag_generator.generate_dag(subtasks)
        
        # 2. 识别不可达节点
        unreachable = self._identify_unreachable_nodes(topology)
        
        # 3. 识别重复节点
        duplicates = self._identify_duplicate_nodes(subtasks)
        
        # 4. 识别无贡献节点
        no_contribution = self._identify_no_contribution_nodes(topology)
        
        # 5. 过滤冗余节点
        filtered = self._filter_nodes(subtasks, unreachable, duplicates, no_contribution)
        
        # 6. 构建被移除节点列表
        removed = []
        
        # 不可达节点
        for node_id in unreachable:
            node = self._find_node(subtasks, node_id)
            if node:
                removed.append(FilteredNode(
                    node_id=node_id,
                    name=node.name,
                    reason=FilterReason.NOT_REACHABLE,
                    description="无法从起始节点到达该节点"
                ))
        
        # 重复节点
        for node_id, duplicates_list in duplicates.items():
            for dup_id in duplicates_list:
                node = self._find_node(subtasks, dup_id)
                if node:
                    removed.append(FilteredNode(
                        node_id=dup_id,
                        name=node.name,
                        reason=FilterReason.DUPLICATE,
                        description=f"与{node_id}功能重复",
                        alternative_nodes=[node_id]
                    ))
        
        # 无贡献节点
        for node_id in no_contribution:
            node = self._find_node(subtasks, node_id)
            if node:
                removed.append(FilteredNode(
                    node_id=node_id,
                    name=node.name,
                    reason=FilterReason.NO_CONTRIBUTION,
                    description="不影响最终目标实现"
                ))
        
        # 7. 检查结果
        is_success = True
        if len(filtered) == 0 and original_count > 0:
            is_success = False
        
        return FilteredTopology(
            original_topology=topology,
            original_count=original_count,
            filtered_nodes=filtered,
            removed_nodes=removed,
            is_success=is_success,
            final_count=len(filtered)
        )
    
    def _identify_unreachable_nodes(self, topology: TopologyStructure) -> Set[str]:
        """
        识别不可达节点
        """
        if len(topology.nodes) <= 1:
            return set()
        
        # 找出起始节点（无依赖的节点）
        start_nodes = set()
        node_deps = {}
        
        for edge in topology.edges:
            if edge.to_node not in node_deps:
                node_deps[edge.to_node] = []
            node_deps[edge.to_node].append(edge.from_node)
        
        for node in topology.nodes:
            if node.node_id not in node_deps or len(node_deps[node.node_id]) == 0:
                start_nodes.add(node.node_id)
        
        if not start_nodes:
            # 如果没有明确的起始节点，用第一个节点
            start_nodes.add(topology.nodes[0].node_id)
        
        # BFS查找所有可达节点
        reachable = set(start_nodes)
        queue = list(start_nodes)
        
        # 构建反向依赖图
        reverse_deps = {}
        for edge in topology.edges:
            if edge.from_node not in reverse_deps:
                reverse_deps[edge.from_node] = []
            reverse_deps[edge.from_node].append(edge.to_node)
        
        while queue:
            current = queue.pop(0)
            if current in reverse_deps:
                for neighbor in reverse_deps[current]:
                    if neighbor not in reachable:
                        reachable.add(neighbor)
                        queue.append(neighbor)
        
        # 找出不可达节点
        all_node_ids = set(node.node_id for node in topology.nodes)
        unreachable = all_node_ids - reachable
        
        return unreachable
    
    def _identify_duplicate_nodes(self, subtasks: List[SubTaskNode]) -> Dict[str, List[str]]:
        """
        识别重复节点
        """
        duplicates = {}
        
        # 按名称和描述分组
        name_map = {}
        for task in subtasks:
            key = task.name.lower()
            if key not in name_map:
                name_map[key] = []
            name_map[key].append(task.node_id)
        
        # 找出重复项
        for name, ids in name_map.items():
            if len(ids) > 1:
                # 第一个作为保留，其他作为重复
                duplicates[ids[0]] = ids[1:]
        
        return duplicates
    
    def _identify_no_contribution_nodes(self, topology: TopologyStructure) -> Set[str]:
        """
        识别无贡献节点
        """
        no_contribution = set()
        
        if len(topology.nodes) <= 1:
            return no_contribution
        
        # 找出结束节点（无被依赖的节点）
        end_nodes = set()
        node_dependents = {}
        
        for edge in topology.edges:
            if edge.from_node not in node_dependents:
                node_dependents[edge.from_node] = []
            node_dependents[edge.from_node].append(edge.to_node)
        
        for node in topology.nodes:
            if node.node_id not in node_dependents or len(node_dependents[node.node_id]) == 0:
                end_nodes.add(node.node_id)
        
        # 找出不在任何路径上到结束节点的节点
        # 简化版：没有输出且没有被依赖的节点（除了结束节点）
        all_node_ids = set(node.node_id for node in topology.nodes)
        
        for node in topology.nodes:
            if node.node_id not in end_nodes:
                # 检查是否有输出或被依赖
                has_output = len(node.outputs) > 0
                is_depended_on = node.node_id in node_dependents
                
                if not has_output and not is_depended_on:
                    no_contribution.add(node.node_id)
        
        return no_contribution
    
    def _filter_nodes(self, subtasks: List[SubTaskNode], unreachable: Set[str], duplicates: Dict[str, List[str]], no_contribution: Set[str]) -> List[SubTaskNode]:
        """
        过滤节点
        """
        # 收集所有应该移除的节点
        to_remove = set()
        to_remove.update(unreachable)
        for dup_list in duplicates.values():
            to_remove.update(dup_list)
        to_remove.update(no_contribution)
        
        # 过滤
        filtered = []
        for task in subtasks:
            if task.node_id not in to_remove:
                filtered.append(task)
        
        return filtered
    
    def _find_node(self, subtasks: List[SubTaskNode], node_id: str) -> Optional[SubTaskNode]:
        """
        查找节点
        """
        for task in subtasks:
            if task.node_id == node_id:
                return task
        return None
    
    def filtered_to_dict(self, filtered_topology: FilteredTopology) -> Dict[str, Any]:
        """
        将过滤后的拓扑转换为字典
        """
        return {
            "original_count": filtered_topology.original_count,
            "final_count": filtered_topology.final_count,
            "removed_count": filtered_topology.original_count - filtered_topology.final_count,
            "is_success": filtered_topology.is_success,
            "original_valid": filtered_topology.original_topology.is_valid,
            "removed_nodes": [
                {
                    "node_id": node.node_id,
                    "name": node.name,
                    "reason": node.reason.value,
                    "description": node.description,
                    "alternative_nodes": node.alternative_nodes
                }
                for node in filtered_topology.removed_nodes
            ],
            "retained_nodes": [
                {
                    "node_id": node.node_id,
                    "name": node.name,
                    "description": node.description
                }
                for node in filtered_topology.filtered_nodes
            ]
        }


# 便捷函数
def filter_task_redundancy(subtasks: List[SubTaskNode]) -> FilteredTopology:
    """
    便捷函数：过滤任务冗余
    
    Args:
        subtasks: 子任务列表
        
    Returns:
        FilteredTopology: 过滤后的拓扑结构
    """
    filter_obj = RedundancyFilter()
    return filter_obj.filter_redundancy(subtasks)


def filter_and_get_dict(subtasks: List[SubTaskNode]) -> Dict[str, Any]:
    """
    便捷函数：过滤冗余并获取字典格式
    
    Args:
        subtasks: 子任务列表
        
    Returns:
        Dict[str, Any]: 过滤结果字典
    """
    filter_obj = RedundancyFilter()
    filtered = filter_obj.filter_redundancy(subtasks)
    return filter_obj.filtered_to_dict(filtered)
