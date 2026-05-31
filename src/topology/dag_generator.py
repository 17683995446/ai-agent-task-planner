"""
第二层：拓扑依赖拆解层 - 标准DAG有向无环图生成组件
基于第一性原理的AI Agent任务规划系统
"""

from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from subtask_node import (
    SubTaskNode, SubTaskStatus, DependencyType, InputSpec, OutputSpec, Dependency
)
from dependency_calculator import DependencyCalculator


@dataclass
class DAGNode:
    """DAG节点"""
    node_id: str
    name: str
    sequence: int
    priority: int
    weight: float
    inputs: List[Dict[str, Any]]
    outputs: List[Dict[str, Any]]
    dependencies: List[Dict[str, Any]]
    status: str
    metadata: Dict[str, Any]


@dataclass
class DAGEdge:
    """DAG边"""
    from_node: str
    to_node: str
    edge_type: str
    description: str


@dataclass
class TopologyStructure:
    """拓扑结构"""
    nodes: List[DAGNode]
    edges: List[DAGEdge]
    is_valid: bool
    validation_errors: List[str]
    topology_order: List[str]


class DAGGenerator:
    """
    DAG生成器
    功能：输出合法拓扑结构图
    """
    
    def __init__(self):
        """初始化DAG生成器"""
        self.dependency_calculator = DependencyCalculator()
    
    def generate_dag(self, subtasks: List[SubTaskNode]) -> TopologyStructure:
        """
        生成DAG拓扑结构
        
        Args:
            subtasks: 子任务列表
            
        Returns:
            TopologyStructure: 拓扑结构
        """
        # 1. 确保依赖关系已计算
        subtasks_with_deps = self.dependency_calculator.calculate_dependencies(subtasks)
        
        # 2. 构建DAG节点
        nodes = self._build_dag_nodes(subtasks_with_deps)
        
        # 3. 构建DAG边
        edges = self._build_dag_edges(subtasks_with_deps)
        
        # 4. 验证拓扑结构
        is_valid, errors = self._validate_dag(nodes, edges)
        
        # 5. 计算拓扑排序
        topology_order = self._compute_topological_order(nodes, edges) if is_valid else []
        
        return TopologyStructure(
            nodes=nodes,
            edges=edges,
            is_valid=is_valid,
            validation_errors=errors,
            topology_order=topology_order
        )
    
    def _build_dag_nodes(self, subtasks: List[SubTaskNode]) -> List[DAGNode]:
        """
        构建DAG节点
        """
        nodes = []
        for task in subtasks:
            node = DAGNode(
                node_id=task.node_id,
                name=task.name,
                sequence=task.sequence,
                priority=task.priority,
                weight=task.weight,
                inputs=[
                    {
                        "name": inp.name,
                        "type": inp.type,
                        "required": inp.required,
                        "source": inp.source
                    }
                    for inp in task.inputs
                ],
                outputs=[
                    {
                        "name": out.name,
                        "type": out.type
                    }
                    for out in task.outputs
                ],
                dependencies=[
                    {
                        "id": dep.dependency_id,
                        "type": dep.dependency_type.value,
                        "description": dep.description
                    }
                    for dep in task.dependencies
                ],
                status=task.status.value,
                metadata=task.metadata
            )
            nodes.append(node)
        return nodes
    
    def _build_dag_edges(self, subtasks: List[SubTaskNode]) -> List[DAGEdge]:
        """
        构建DAG边
        """
        edges = []
        for task in subtasks:
            for dep in task.dependencies:
                edge = DAGEdge(
                    from_node=dep.dependency_id,
                    to_node=task.node_id,
                    edge_type=dep.dependency_type.value,
                    description=dep.description
                )
                edges.append(edge)
        return edges
    
    def _validate_dag(self, nodes: List[DAGNode], edges: List[DAGEdge]) -> tuple[bool, List[str]]:
        """
        验证DAG拓扑结构
        """
        errors = []
        
        # 1. 检查是否有循环依赖
        if self._has_cycle(nodes, edges):
            errors.append("检测到循环依赖，拓扑结构无效")
        
        # 2. 检查是否有悬空节点（没有依赖且无被依赖）
        self._check_dangling_nodes(nodes, edges, errors)
        
        # 3. 检查所有边的节点是否存在
        self._check_edge_nodes(nodes, edges, errors)
        
        return len(errors) == 0, errors
    
    def _has_cycle(self, nodes: List[DAGNode], edges: List[DAGEdge]) -> bool:
        """
        检查是否有循环依赖
        """
        # 构建邻接表
        adj = {}
        node_ids = set(node.node_id for node in nodes)
        for node_id in node_ids:
            adj[node_id] = []
        for edge in edges:
            if edge.from_node in adj and edge.to_node in adj:
                adj[edge.from_node].append(edge.to_node)
        
        # 访问标记
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
    
    def _check_dangling_nodes(self, nodes: List[DAGNode], edges: List[DAGEdge], errors: List[str]):
        """
        检查悬空节点
        """
        if len(nodes) <= 1:
            return
        
        # 收集所有节点ID
        node_ids = set(node.node_id for node in nodes)
        
        # 收集有依赖或被依赖的节点
        active_nodes = set()
        for edge in edges:
            active_nodes.add(edge.from_node)
            active_nodes.add(edge.to_node)
        
        # 找出悬空节点（有多个节点的情况下）
        for node in nodes:
            if node.node_id not in active_nodes and len(node.dependencies) == 0:
                errors.append(f"节点 {node.name} ({node.node_id}) 是悬空节点")
    
    def _check_edge_nodes(self, nodes: List[DAGNode], edges: List[DAGEdge], errors: List[str]):
        """
        检查边的节点是否存在
        """
        node_ids = set(node.node_id for node in nodes)
        for edge in edges:
            if edge.from_node not in node_ids:
                errors.append(f"边 {edge.from_node} -> {edge.to_node} 的起始节点不存在")
            if edge.to_node not in node_ids:
                errors.append(f"边 {edge.from_node} -> {edge.to_node} 的目标节点不存在")
    
    def _compute_topological_order(self, nodes: List[DAGNode], edges: List[DAGEdge]) -> List[str]:
        """
        计算拓扑排序
        """
        # 构建邻接表和入度
        adj = {}
        in_degree = {}
        node_ids = set(node.node_id for node in nodes)
        
        for node_id in node_ids:
            adj[node_id] = []
            in_degree[node_id] = 0
        
        for edge in edges:
            if edge.from_node in adj and edge.to_node in adj:
                adj[edge.from_node].append(edge.to_node)
                in_degree[edge.to_node] += 1
        
        # Kahn's算法
        queue = []
        for node_id in node_ids:
            if in_degree[node_id] == 0:
                queue.append(node_id)
        
        result = []
        while queue:
            # 按优先级和序号排序
            queue.sort(key=lambda nid: (
                next((n.priority for n in nodes if n.node_id == nid), 0),
                next((n.sequence for n in nodes if n.node_id == nid), 0)
            ))
            
            current = queue.pop(0)
            result.append(current)
            
            for neighbor in adj[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        return result
    
    def topology_to_dict(self, topology: TopologyStructure) -> Dict[str, Any]:
        """
        将拓扑结构转换为字典
        """
        return {
            "is_valid": topology.is_valid,
            "validation_errors": topology.validation_errors,
            "topology_order": topology.topology_order,
            "nodes": [
                {
                    "id": node.node_id,
                    "name": node.name,
                    "sequence": node.sequence,
                    "priority": node.priority,
                    "weight": node.weight,
                    "inputs": node.inputs,
                    "outputs": node.outputs,
                    "dependencies": node.dependencies,
                    "status": node.status
                }
                for node in topology.nodes
            ],
            "edges": [
                {
                    "from": edge.from_node,
                    "to": edge.to_node,
                    "type": edge.edge_type,
                    "description": edge.description
                }
                for edge in topology.edges
            ]
        }


# 便捷函数
def generate_topology(subtasks: List[SubTaskNode]) -> TopologyStructure:
    """
    便捷函数：生成拓扑结构
    
    Args:
        subtasks: 子任务列表
        
    Returns:
        TopologyStructure: 拓扑结构
    """
    generator = DAGGenerator()
    return generator.generate_dag(subtasks)


def generate_topology_dict(subtasks: List[SubTaskNode]) -> Dict[str, Any]:
    """
    便捷函数：生成拓扑结构字典
    
    Args:
        subtasks: 子任务列表
        
    Returns:
        Dict[str, Any]: 拓扑结构字典
    """
    generator = DAGGenerator()
    topology = generator.generate_dag(subtasks)
    return generator.topology_to_dict(topology)
