"""
第三层：原子动作收敛层 - 子任务下沉转为原子队列
基于第一性原理的AI Agent任务规划系统

核心功能：
- 将子任务节点转换为原子动作队列
- 保持子任务间的依赖关系
- 支持优先级和权重排序
- 智能拓扑排序确保执行顺序正确
"""

from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum
import uuid

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from atomic_action_struct import (
    AtomicAction, AtomicActionQueue, AtomicActionStatus, AtomicActionType,
    AtomicCondition, ActionInput, ActionOutput, ActionConstraint,
    create_atomic_action
)
from action_splitter import ActionSplitter, CompositeAction, SplitStrategy
from atomic_validator import AtomicValidator

# 导入上层的子任务节点结构
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'topology'))
from subtask_node import SubTaskNode, DependencyType


class QueueStrategy(Enum):
    """队列生成策略"""
    TOPOLOGICAL = "topological"      # 拓扑排序（依赖优先）
    PRIORITY = "priority"            # 优先级排序
    SEQUENCE = "sequence"            # 原顺序排序
    WEIGHTED = "weighted"            # 加权排序


@dataclass
class SubtaskMapping:
    """子任务到原子动作的映射关系"""
    subtask_node_id: str
    atomic_actions: List[AtomicAction]
    dependency_mappings: Dict[str, List[str]]  # 子任务依赖ID -> 原子动作ID列表


class AtomicQueueGenerator:
    """
    子任务下沉转为原子队列逻辑
    
    功能：
    - 将子任务节点转换为原子动作
    - 保持子任务间的依赖关系
    - 生成有序可执行的原子动作队列
    """
    
    def __init__(self):
        self.action_splitter = ActionSplitter()
        self.atomic_validator = AtomicValidator()
    
    def subtasks_to_atomic_queue(
        self,
        subtasks: List[SubTaskNode],
        strategy: QueueStrategy = QueueStrategy.TOPOLOGICAL,
        queue_name: str = "原子动作队列"
    ) -> Tuple[AtomicActionQueue, List[SubtaskMapping]]:
        """
        将子任务列表转换为原子动作队列
        
        Args:
            subtasks: 子任务节点列表
            strategy: 队列排序策略
            queue_name: 队列名称
        
        Returns:
            (AtomicActionQueue, List[SubtaskMapping]): 原子动作队列和映射关系
        """
        queue_id = f"queue_{uuid.uuid4().hex[:8]}"
        queue = AtomicActionQueue(
            queue_id=queue_id,
            name=queue_name
        )
        
        mappings = []
        all_actions = []
        
        # 1. 将每个子任务转换为原子动作
        for subtask in subtasks:
            mapping = self._map_subtask_to_atomics(subtask)
            mappings.append(mapping)
            all_actions.extend(mapping.atomic_actions)
        
        # 2. 建立跨子任务的依赖关系
        self._establish_cross_subtask_dependencies(mappings)
        
        # 3. 根据策略排序
        sorted_actions = self._sort_actions_by_strategy(all_actions, strategy, subtasks)
        
        # 4. 添加到队列
        queue.add_actions(sorted_actions)
        
        return queue, mappings
    
    def _map_subtask_to_atomics(
        self,
        subtask: SubTaskNode
    ) -> SubtaskMapping:
        """
        将单个子任务映射为原子动作
        
        Args:
            subtask: 子任务节点
        
        Returns:
            SubtaskMapping: 映射关系
        """
        # 创建复合动作
        composite = CompositeAction(
            composite_id=subtask.node_id,
            name=subtask.name,
            description=subtask.description,
            raw_description=subtask.description,
            metadata={
                "parent_task_id": subtask.parent_task_id,
                "subtask_sequence": subtask.sequence,
                "priority": subtask.priority,
                "weight": subtask.weight
            }
        )
        
        # 拆分为原子动作
        atomic_queue = self.action_splitter.split_composite_action(
            composite,
            strategy=SplitStrategy.SEQUENTIAL
        )
        
        # 继承子任务的优先级和权重
        for action in atomic_queue.actions:
            action.priority = subtask.priority
            action.metadata["subtask_node_id"] = subtask.node_id
            action.metadata["subtask_sequence"] = subtask.sequence
            action.metadata["subtask_weight"] = subtask.weight
            
            # 从子任务的输入输出继承
            for inp in subtask.inputs:
                action.add_input(
                    name=inp.name,
                    type=inp.type,
                    required=inp.required,
                    description=inp.description,
                    default=inp.default
                )
            
            for out in subtask.outputs:
                action.add_output(
                    name=out.name,
                    type=out.type,
                    description=out.description
                )
            
            # 标记原子条件
            action.add_atomic_condition(AtomicCondition.SINGLE_RESPONSIBILITY)
        
        # 建立依赖映射
        dependency_mappings = {}
        for dep in subtask.dependencies:
            dependency_mappings[dep.dependency_id] = []
        
        return SubtaskMapping(
            subtask_node_id=subtask.node_id,
            atomic_actions=atomic_queue.actions,
            dependency_mappings=dependency_mappings
        )
    
    def _establish_cross_subtask_dependencies(
        self,
        mappings: List[SubtaskMapping]
    ):
        """
        建立跨子任务的依赖关系
        
        Args:
            mappings: 子任务映射列表
        """
        # 创建子任务ID到映射的索引
        subtask_map = {m.subtask_node_id: m for m in mappings}
        
        for mapping in mappings:
            for dep_subtask_id, atomic_ids in mapping.dependency_mappings.items():
                if dep_subtask_id in subtask_map:
                    # 找到依赖子任务的最后一个原子动作
                    dep_mapping = subtask_map[dep_subtask_id]
                    if dep_mapping.atomic_actions:
                        last_dep_action = dep_mapping.atomic_actions[-1]
                        
                        # 将当前子任务的第一个原子动作依赖于它
                        if mapping.atomic_actions:
                            first_action = mapping.atomic_actions[0]
                            first_action.add_dependency(last_dep_action.action_id)
    
    def _sort_actions_by_strategy(
        self,
        actions: List[AtomicAction],
        strategy: QueueStrategy,
        subtasks: List[SubTaskNode]
    ) -> List[AtomicAction]:
        """
        根据策略排序原子动作
        
        Args:
            actions: 原子动作列表
            strategy: 排序策略
            subtasks: 原始子任务列表
        
        Returns:
            List[AtomicAction]: 排序后的动作列表
        """
        if strategy == QueueStrategy.TOPOLOGICAL:
            return self._topological_sort(actions)
        elif strategy == QueueStrategy.PRIORITY:
            return sorted(actions, key=lambda a: a.priority)
        elif strategy == QueueStrategy.SEQUENCE:
            return sorted(actions, key=lambda a: a.metadata.get("subtask_sequence", 0))
        elif strategy == QueueStrategy.WEIGHTED:
            return sorted(actions, key=lambda a: (
                a.metadata.get("subtask_weight", 1.0),
                a.priority
            ), reverse=True)
        else:
            return actions
    
    def _topological_sort(
        self,
        actions: List[AtomicAction]
    ) -> List[AtomicAction]:
        """
        拓扑排序算法
        
        Args:
            actions: 原子动作列表
        
        Returns:
            List[AtomicAction]: 拓扑排序后的动作列表
        """
        # 创建动作ID到动作的映射
        action_map = {a.action_id: a for a in actions}
        
        # 构建入度表
        in_degree = {a.action_id: 0 for a in actions}
        adjacency = {a.action_id: [] for a in actions}
        
        for action in actions:
            for dep_id in action.dependencies:
                if dep_id in action_map:
                    adjacency[dep_id].append(action.action_id)
                    in_degree[action.action_id] += 1
        
        # Kahn算法进行拓扑排序
        queue = [a.action_id for a in actions if in_degree[a.action_id] == 0]
        result = []
        
        while queue:
            # 按优先级选择
            queue.sort(key=lambda aid: action_map[aid].priority)
            current_id = queue.pop(0)
            result.append(action_map[current_id])
            
            for neighbor_id in adjacency[current_id]:
                in_degree[neighbor_id] -= 1
                if in_degree[neighbor_id] == 0:
                    queue.append(neighbor_id)
        
        # 检查是否有环
        if len(result) != len(actions):
            # 有环，剩余动作追加到末尾
            remaining = [a for a in actions if a not in result]
            result.extend(remaining)
        
        return result
    
    def validate_atomic_queue(
        self,
        queue: AtomicActionQueue
    ) -> Dict[str, Any]:
        """
        验证原子队列的正确性
        
        Args:
            queue: 原子动作队列
        
        Returns:
            Dict: 验证结果
        """
        results = self.atomic_validator.validate_atomic_queue(queue)
        summary = self.atomic_validator.get_validation_summary(results)
        
        # 检查依赖关系
        dependency_check = self._check_dependency_chain(queue)
        
        return {
            "atomic_validation": summary,
            "dependency_check": dependency_check,
            "is_valid": summary["valid_actions"] == summary["total_actions"] and dependency_check["is_valid"]
        }
    
    def _check_dependency_chain(
        self,
        queue: AtomicActionQueue
    ) -> Dict[str, Any]:
        """
        检查依赖链的有效性
        
        Args:
            queue: 原子动作队列
        
        Returns:
            Dict: 检查结果
        """
        action_map = {a.action_id: a for a in queue.actions}
        issues = []
        
        for action in queue.actions:
            for dep_id in action.dependencies:
                if dep_id not in action_map:
                    issues.append({
                        "action_id": action.action_id,
                        "action_name": action.name,
                        "issue": f"依赖的动作不存在: {dep_id}"
                    })
        
        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "total_dependencies": sum(len(a.dependencies) for a in queue.actions)
        }
    
    def get_execution_plan(
        self,
        queue: AtomicActionQueue
    ) -> List[Dict[str, Any]]:
        """
        生成执行计划
        
        Args:
            queue: 原子动作队列
        
        Returns:
            List[Dict]: 执行计划列表
        """
        plan = []
        
        for i, action in enumerate(queue.actions):
            plan.append({
                "step": i + 1,
                "action_id": action.action_id,
                "name": action.name,
                "description": action.description,
                "type": action.action_type.value,
                "priority": action.priority,
                "dependencies": action.dependencies,
                "subtask_node_id": action.metadata.get("subtask_node_id"),
                "status": action.status.value
            })
        
        return plan


# 便捷函数
def generate_atomic_queue_from_subtasks(
    subtasks: List[SubTaskNode],
    strategy: QueueStrategy = QueueStrategy.TOPOLOGICAL,
    queue_name: str = "原子动作队列"
) -> Tuple[AtomicActionQueue, List[SubtaskMapping], Dict[str, Any]]:
    """
    便捷函数：从子任务生成原子队列并验证
    
    Args:
        subtasks: 子任务列表
        strategy: 排序策略
        queue_name: 队列名称
    
    Returns:
        (queue, mappings, validation): 队列、映射、验证结果
    """
    generator = AtomicQueueGenerator()
    queue, mappings = generator.subtasks_to_atomic_queue(
        subtasks,
        strategy,
        queue_name
    )
    validation = generator.validate_atomic_queue(queue)
    
    return queue, mappings, validation


def get_execution_plan_from_subtasks(
    subtasks: List[SubTaskNode],
    strategy: QueueStrategy = QueueStrategy.TOPOLOGICAL
) -> List[Dict[str, Any]]:
    """
    便捷函数：从子任务生成执行计划
    
    Args:
        subtasks: 子任务列表
        strategy: 排序策略
    
    Returns:
        List[Dict]: 执行计划
    """
    generator = AtomicQueueGenerator()
    queue, _ = generator.subtasks_to_atomic_queue(subtasks, strategy)
    return generator.get_execution_plan(queue)
