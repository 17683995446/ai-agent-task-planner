"""
第二层：拓扑依赖拆解层 - 拓扑纠错模块
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


class CorrectionType(Enum):
    """纠错类型"""
    CYCLE_BREAK = "cycle_break"
    DANGLING_REMOVE = "dangling_remove"
    DEPENDENCY_REORDER = "dependency_reorder"
    EDGE_FIX = "edge_fix"


@dataclass
class CorrectionAction:
    """纠错操作"""
    correction_type: CorrectionType
    description: str
    affected_nodes: List[str]
    affected_edges: List[tuple[str, str]]


@dataclass
class CorrectedTopology:
    """纠错后的拓扑结构"""
    original_topology: TopologyStructure
    corrected_topology: TopologyStructure
    corrections_applied: List[CorrectionAction]
    is_successful: bool
    error_messages: List[str]


class TopologyCorrector:
    """
    拓扑纠错模块
    功能：非法拓扑自动拦截重排
    """
    
    def __init__(self):
        """初始化拓扑纠错模块"""
        self.dag_generator = DAGGenerator()
    
    def correct_topology(self, subtasks: List[SubTaskNode]) -> CorrectedTopology:
        """
        纠错拓扑结构
        
        Args:
            subtasks: 子任务列表
            
        Returns:
            CorrectedTopology: 纠错后的拓扑结构
        """
        # 1. 先生成原始拓扑
        original_topology = self.dag_generator.generate_dag(subtasks)
        
        corrections = []
        error_messages = []
        current_subtasks = subtasks.copy()
        
        # 2. 检测并修复循环依赖
        if self._has_cycle_in_subtasks(current_subtasks):
            correction, fixed_subtasks = self._break_cycle(current_subtasks)
            if correction:
                corrections.append(correction)
                current_subtasks = fixed_subtasks
        
        # 3. 检测并修复悬空节点
        dangling_nodes = self._find_dangling_nodes(current_subtasks)
        if dangling_nodes:
            correction, fixed_subtasks = self._handle_dangling_nodes(current_subtasks, dangling_nodes)
            if correction:
                corrections.append(correction)
                current_subtasks = fixed_subtasks
        
        # 4. 重新生成纠错后的拓扑
        corrected_topology = self.dag_generator.generate_dag(current_subtasks)
        
        # 5. 检查是否成功
        is_successful = corrected_topology.is_valid
        
        if not is_successful:
            error_messages.extend(corrected_topology.validation_errors)
        
        return CorrectedTopology(
            original_topology=original_topology,
            corrected_topology=corrected_topology,
            corrections_applied=corrections,
            is_successful=is_successful,
            error_messages=error_messages
        )
    
    def _has_cycle_in_subtasks(self, subtasks: List[SubTaskNode]) -> bool:
        """
        检测子任务中是否有循环依赖
        """
        # 构建邻接表
        adj = {}
        node_ids = set(task.node_id for task in subtasks)
        for node_id in node_ids:
            adj[node_id] = []
        
        for task in subtasks:
            for dep in task.dependencies:
                if dep.dependency_id in node_ids and task.node_id in node_ids:
                    adj[dep.dependency_id].append(task.node_id)
        
        # 检测循环
        visited = set()
        rec_stack = set()
        
        def dfs(node_id: str) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)
            
            for neighbor in adj.get(node_id, []):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            
            rec_stack.remove(node_id)
            return False
        
        for node_id in node_ids:
            if node_id not in visited:
                if dfs(node_id):
                    return True
        
        return False
    
    def _break_cycle(self, subtasks: List[SubTaskNode]) -> tuple[Optional[CorrectionAction], List[SubTaskNode]]:
        """
        打破循环依赖
        """
        # 策略：移除优先级最低的软依赖
        # 或者根据序列号重新组织
        
        # 找出循环中的节点
        cycle_nodes = self._find_cycle_nodes(subtasks)
        
        if not cycle_nodes:
            return None, subtasks
        
        # 打破循环的策略：移除软依赖，或者重新排序
        fixed_subtasks = []
        removed_edges = []
        
        for task in subtasks:
            fixed_task = task
            # 移除循环中的软依赖
            filtered_deps = []
            for dep in task.dependencies:
                if dep.dependency_id in cycle_nodes and task.node_id in cycle_nodes:
                    if dep.dependency_type != DependencyType.HARD:
                        # 移除软依赖
                        removed_edges.append((dep.dependency_id, task.node_id))
                    else:
                        filtered_deps.append(dep)
                else:
                    filtered_deps.append(dep)
            
            fixed_task.dependencies = filtered_deps
            fixed_subtasks.append(fixed_task)
        
        # 构建纠错操作
        if removed_edges:
            action = CorrectionAction(
                correction_type=CorrectionType.CYCLE_BREAK,
                description=f"打破循环依赖，移除了 {len(removed_edges)} 条非强依赖边",
                affected_nodes=list(cycle_nodes),
                affected_edges=removed_edges
            )
            return action, fixed_subtasks
        
        return None, subtasks
    
    def _find_cycle_nodes(self, subtasks: List[SubTaskNode]) -> Set[str]:
        """
        找出循环中的节点
        """
        # 构建邻接表
        adj = {}
        node_ids = set(task.node_id for task in subtasks)
        for node_id in node_ids:
            adj[node_id] = []
        
        for task in subtasks:
            for dep in task.dependencies:
                if dep.dependency_id in node_ids and task.node_id in node_ids:
                    adj[dep.dependency_id].append(task.node_id)
        
        # 查找循环
        visited = set()
        rec_stack = set()
        cycle = set()
        
        def dfs(node_id: str, path: List[str]) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)
            path.append(node_id)
            
            for neighbor in adj.get(node_id, []):
                if neighbor not in visited:
                    if dfs(neighbor, path):
                        return True
                elif neighbor in rec_stack:
                    # 找到循环
                    try:
                        idx = path.index(neighbor)
                        cycle.update(path[idx:])
                        return True
                    except ValueError:
                        # neighbor不在path中，继续处理
                        continue
            
            path.pop()
            rec_stack.remove(node_id)
            return False
        
        for node_id in node_ids:
            if node_id not in visited:
                dfs(node_id, [])
        
        return cycle
    
    def _find_dangling_nodes(self, subtasks: List[SubTaskNode]) -> List[str]:
        """
        找出悬空节点
        """
        if len(subtasks) <= 1:
            return []
        
        node_ids = set(task.node_id for task in subtasks)
        
        # 找出有依赖或被依赖的节点
        active_nodes = set()
        for task in subtasks:
            for dep in task.dependencies:
                active_nodes.add(dep.dependency_id)
                active_nodes.add(task.node_id)
        
        # 找出悬空节点
        dangling = []
        for task in subtasks:
            if task.node_id not in active_nodes and len(task.dependencies) == 0:
                dangling.append(task.node_id)
        
        return dangling
    
    def _handle_dangling_nodes(self, subtasks: List[SubTaskNode], dangling_nodes: List[str]) -> tuple[Optional[CorrectionAction], List[SubTaskNode]]:
        """
        处理悬空节点
        """
        if not dangling_nodes:
            return None, subtasks
        
        # 策略：连接到起始节点或终止节点
        # 如果没有明显的起始/终止，尝试连接到第一个或最后一个节点
        
        if len(subtasks) <= 1:
            return None, subtasks
        
        # 找出最早和最晚的节点
        sorted_tasks = sorted(subtasks, key=lambda t: t.sequence)
        first_node = sorted_tasks[0].node_id
        last_node = sorted_tasks[-1].node_id
        
        fixed_subtasks = []
        added_edges = []
        
        for task in subtasks:
            if task.node_id in dangling_nodes:
                # 连接到合适的节点
                if task.sequence < sorted_tasks[len(sorted_tasks)//2].sequence:
                    # 前面的节点，被第一个节点依赖
                    sorted_tasks[0].dependencies.append(Dependency(
                        dependency_id=task.node_id,
                        dependency_type=DependencyType.SOFT,
                        description=f"连接悬空节点 {task.name}"
                    ))
                    added_edges.append((task.node_id, first_node))
                else:
                    # 后面的节点，依赖最后一个节点
                    task.dependencies.append(Dependency(
                        dependency_id=last_node,
                        dependency_type=DependencyType.SOFT,
                        description=f"连接悬空节点 {task.name}"
                    ))
                    added_edges.append((last_node, task.node_id))
            
            fixed_subtasks.append(task)
        
        action = CorrectionAction(
            correction_type=CorrectionType.DANGLING_REMOVE,
            description=f"连接 {len(dangling_nodes)} 个悬空节点到拓扑图",
            affected_nodes=dangling_nodes,
            affected_edges=added_edges
        )
        
        return action, fixed_subtasks
    
    def corrected_to_dict(self, corrected: CorrectedTopology) -> Dict[str, Any]:
        """
        将纠错后的拓扑结构转换为字典
        """
        return {
            "is_successful": corrected.is_successful,
            "error_messages": corrected.error_messages,
            "corrections_count": len(corrected.corrections_applied),
            "corrections": [
                {
                    "type": corr.correction_type.value,
                    "description": corr.description,
                    "affected_nodes": corr.affected_nodes,
                    "affected_edges": corr.affected_edges
                }
                for corr in corrected.corrections_applied
            ],
            "original_valid": corrected.original_topology.is_valid,
            "corrected_valid": corrected.corrected_topology.is_valid,
            "topology_order": corrected.corrected_topology.topology_order
        }


# 便捷函数
def correct_task_topology(subtasks: List[SubTaskNode]) -> CorrectedTopology:
    """
    便捷函数：纠错任务拓扑结构
    
    Args:
        subtasks: 子任务列表
        
    Returns:
        CorrectedTopology: 纠错后的拓扑结构
    """
    corrector = TopologyCorrector()
    return corrector.correct_topology(subtasks)


def correct_and_get_dict(subtasks: List[SubTaskNode]) -> Dict[str, Any]:
    """
    便捷函数：纠错并获取字典格式
    
    Args:
        subtasks: 子任务列表
        
    Returns:
        Dict[str, Any]: 纠错结果字典
    """
    corrector = TopologyCorrector()
    corrected = corrector.correct_topology(subtasks)
    return corrector.corrected_to_dict(corrected)
