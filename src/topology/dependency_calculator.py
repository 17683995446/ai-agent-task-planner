"""
第二层：拓扑依赖拆解层 - 任务依赖关系自动计算算法
基于第一性原理的AI Agent任务规划系统
"""

from typing import List, Dict, Any, Optional, Set

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from subtask_node import (
    SubTaskNode, SubTaskStatus, DependencyType, InputSpec, OutputSpec, Dependency
)


class DependencyRelation:
    """依赖关系"""
    def __init__(self, from_node: str, to_node: str, relation_type: str, description: str = ""):
        self.from_node = from_node
        self.to_node = to_node
        self.relation_type = relation_type
        self.description = description
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "from": self.from_node,
            "to": self.to_node,
            "type": self.relation_type,
            "description": self.description
        }


class DependencyCalculator:
    """
    依赖计算单元
    功能：自动识别前后依赖关系
    """
    
    def __init__(self):
        """初始化依赖计算器"""
        pass
    
    def calculate_dependencies(self, subtasks: List[SubTaskNode]) -> List[SubTaskNode]:
        """
        计算子任务之间的依赖关系
        
        Args:
            subtasks: 子任务列表
            
        Returns:
            更新后的子任务列表
        """
        # 基于输入-输出匹配计算依赖
        subtasks = self._calculate_by_input_output(subtasks)
        
        # 基于时间序列计算依赖
        subtasks = self._calculate_by_sequence(subtasks)
        
        # 基于内容语义计算依赖
        subtasks = self._calculate_by_semantics(subtasks)
        
        # 优化依赖关系（移除冗余依赖）
        subtasks = self._optimize_dependencies(subtasks)
        
        return subtasks
    
    def _calculate_by_input_output(self, subtasks: List[SubTaskNode]) -> List[SubTaskNode]:
        """
        基于输入-输出匹配计算依赖
        """
        # 创建输出映射
        output_map = {}
        for task in subtasks:
            for output in task.outputs:
                output_key = f"{task.node_id}:{output.name}"
                output_map[output_key] = {
                    "task_id": task.node_id,
                    "output": output
                }
        
        # 为每个任务查找可能的输入来源
        for current_task in subtasks:
            for input_spec in current_task.inputs:
                # 查找能提供此输入的任务
                for potential_source in subtasks:
                    if potential_source.node_id == current_task.node_id:
                        continue
                    
                    # 检查输出是否匹配
                    for output_spec in potential_source.outputs:
                        if self._is_compatible(input_spec, output_spec):
                            # 添加依赖
                            current_task.add_dependency(
                                potential_source.node_id,
                                DependencyType.HARD,
                                f"需要{potential_source.name}的{output_spec.name}作为输入"
                            )
                            # 设置输入来源
                            input_spec.source = potential_source.node_id
        
        return subtasks
    
    def _calculate_by_sequence(self, subtasks: List[SubTaskNode]) -> List[SubTaskNode]:
        """
        基于时间序列计算依赖
        """
        # 按sequence排序
        sorted_tasks = sorted(subtasks, key=lambda t: t.sequence)
        
        # 设置序列依赖
        for i in range(1, len(sorted_tasks)):
            current = sorted_tasks[i]
            previous = sorted_tasks[i-1]
            
            # 检查是否已有依赖
            has_dependency = False
            for dep in current.dependencies:
                if dep.dependency_id == previous.node_id:
                    has_dependency = True
                    break
            
            # 如果没有依赖且没有并行标记，则添加序列依赖
            if not has_dependency and len(current.dependencies) == 0:
                current.add_dependency(
                    previous.node_id,
                    DependencyType.SOFT,
                    f"建议在{previous.name}完成后执行"
                )
        
        return subtasks
    
    def _calculate_by_semantics(self, subtasks: List[SubTaskNode]) -> List[SubTaskNode]:
        """
        基于内容语义计算依赖
        """
        # 分析任务名称和描述，查找语义关系
        for task in subtasks:
            # 检查是否是"准备"、"分析"类任务（通常是前置任务）
            if any(keyword in task.name.lower() for keyword in ["准备", "分析", "初始化", "setup", "prepare", "analyze"]):
                # 让后续任务依赖于它
                for other_task in subtasks:
                    if other_task.node_id != task.node_id and other_task.sequence > task.sequence:
                        has_dependency = any(dep.dependency_id == task.node_id for dep in other_task.dependencies)
                        if not has_dependency:
                            other_task.add_dependency(
                                task.node_id,
                                DependencyType.RECOMMENDED,
                                f"建议在{task.name}完成后执行"
                            )
        
        return subtasks
    
    def _optimize_dependencies(self, subtasks: List[SubTaskNode]) -> List[SubTaskNode]:
        """
        优化依赖关系（移除冗余依赖）
        """
        # 移除重复的依赖
        for task in subtasks:
            unique_deps = []
            seen = set()
            
            for dep in task.dependencies:
                if dep.dependency_id not in seen:
                    seen.add(dep.dependency_id)
                    unique_deps.append(dep)
            
            task.dependencies = unique_deps
        
        # 移除传递依赖（A->B, B->C, 则不需要A->C）
        for task in subtasks:
            # 构建直接依赖的任务
            direct_deps = set(dep.dependency_id for dep in task.dependencies)
            
            # 找出可以移除的传递依赖
            to_remove = set()
            for dep_id in direct_deps:
                # 查找dep_id的依赖任务
                dep_task = self._find_task(subtasks, dep_id)
                if dep_task:
                    # 如果dep_task的依赖也在当前任务的依赖中，则可以移除
                    for indirect_dep in dep_task.dependencies:
                        if indirect_dep.dependency_id in direct_deps:
                            to_remove.add(indirect_dep.dependency_id)
            
            # 过滤掉传递依赖
            task.dependencies = [
                dep for dep in task.dependencies 
                if dep.dependency_id not in to_remove
            ]
        
        return subtasks
    
    def _is_compatible(self, input_spec: InputSpec, output_spec: OutputSpec) -> bool:
        """
        检查输入和输出是否兼容
        """
        # 名称匹配
        name_match = input_spec.name.lower() == output_spec.name.lower()
        
        # 类型匹配
        type_match = (
            input_spec.type.lower() == output_spec.type.lower() or
            "any" in [input_spec.type.lower(), output_spec.type.lower()]
        )
        
        return name_match or type_match
    
    def _find_task(self, subtasks: List[SubTaskNode], task_id: str) -> Optional[SubTaskNode]:
        """
        查找任务
        """
        for task in subtasks:
            if task.node_id == task_id:
                return task
        return None
    
    def get_dependency_relations(self, subtasks: List[SubTaskNode]) -> List[DependencyRelation]:
        """
        获取依赖关系列表
        """
        relations = []
        
        for task in subtasks:
            for dep in task.dependencies:
                relation = DependencyRelation(
                    from_node=dep.dependency_id,
                    to_node=task.node_id,
                    relation_type=dep.dependency_type.value,
                    description=dep.description
                )
                relations.append(relation)
        
        return relations
    
    def build_dependency_graph(self, subtasks: List[SubTaskNode]) -> Dict[str, Any]:
        """
        构建依赖图结构
        """
        nodes = []
        edges = []
        
        # 添加节点
        for task in subtasks:
            nodes.append({
                "id": task.node_id,
                "name": task.name,
                "sequence": task.sequence,
                "status": task.status.value,
                "priority": task.priority,
                "weight": task.weight
            })
        
        # 添加边
        for task in subtasks:
            for dep in task.dependencies:
                edges.append({
                    "from": dep.dependency_id,
                    "to": task.node_id,
                    "type": dep.dependency_type.value,
                    "description": dep.description
                })
        
        return {
            "nodes": nodes,
            "edges": edges,
            "summary": {
                "total_nodes": len(nodes),
                "total_edges": len(edges)
            }
        }


# 便捷函数
def calculate_task_dependencies(subtasks: List[SubTaskNode]) -> List[SubTaskNode]:
    """
    便捷函数：计算任务依赖关系
    
    Args:
        subtasks: 子任务列表
        
    Returns:
        更新后的子任务列表
    """
    calculator = DependencyCalculator()
    return calculator.calculate_dependencies(subtasks)


def get_dependency_graph(subtasks: List[SubTaskNode]) -> Dict[str, Any]:
    """
    便捷函数：获取依赖图结构
    
    Args:
        subtasks: 子任务列表
        
    Returns:
        依赖图结构
    """
    calculator = DependencyCalculator()
    return calculator.build_dependency_graph(subtasks)
