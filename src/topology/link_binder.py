"""
第二层：拓扑依赖拆解层 - 链路绑定逻辑
基于第一性原理的AI Agent任务规划系统
"""

from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from subtask_node import (
    SubTaskNode, SubTaskStatus, DependencyType, InputSpec, OutputSpec, Dependency
)
from dag_generator import DAGGenerator, DAGNode, DAGEdge, TopologyStructure


class BindStatus(Enum):
    """绑定状态"""
    VALID = "valid"
    MISSING_OUTPUT = "missing_output"
    MISSING_INPUT = "missing_input"
    TYPE_MISMATCH = "type_mismatch"
    UNNECESSARY_OUTPUT = "unnecessary_output"
    NO_CONNECTION = "no_connection"


@dataclass
class BindIssue:
    """绑定问题"""
    node_id: str
    name: str
    issue_type: BindStatus
    description: str
    related_node: Optional[str] = None
    related_spec: Optional[str] = None


@dataclass
class BoundLink:
    """绑定链路"""
    from_node: str
    from_output: str
    to_node: str
    to_input: str
    bind_type: str
    is_valid: bool


@dataclass
class LinkValidatedTopology:
    """链路验证后的拓扑"""
    original_topology: TopologyStructure
    bound_links: List[BoundLink]
    issues: List[BindIssue]
    is_valid: bool
    valid_count: int
    issue_count: int


class LinkBinder:
    """
    链路绑定逻辑
    功能：后节点输入 = 前节点输出
    """
    
    def __init__(self):
        """初始化链路绑定器"""
        self.dag_generator = DAGGenerator()
    
    def validate_links(self, subtasks: List[SubTaskNode]) -> LinkValidatedTopology:
        """
        验证链路绑定
        
        Args:
            subtasks: 子任务列表
            
        Returns:
            LinkValidatedTopology: 验证后的拓扑
        """
        # 1. 生成拓扑结构
        topology = self.dag_generator.generate_dag(subtasks)
        
        # 2. 检查输入输出绑定
        bound_links = []
        issues = []
        
        # 构建输出映射
        output_map = self._build_output_map(subtasks)
        
        # 检查每个节点的输入
        for task in subtasks:
            for inp in task.inputs:
                # 检查是否有来源
                if inp.source:
                    # 检查来源是否存在对应的输出
                    source_task = self._find_task(subtasks, inp.source)
                    if source_task:
                        output_found = False
                        for outp in source_task.outputs:
                            if outp.name == inp.name:
                                # 找到匹配的输出
                                bound_links.append(BoundLink(
                                    from_node=source_task.node_id,
                                    from_output=outp.name,
                                    to_node=task.node_id,
                                    to_input=inp.name,
                                    bind_type="explicit_source",
                                    is_valid=True
                                ))
                                output_found = True
                                break
                        
                        if not output_found:
                            issues.append(BindIssue(
                                node_id=task.node_id,
                                name=task.name,
                                issue_type=BindStatus.MISSING_OUTPUT,
                                description=f"输入 '{inp.name}' 来源节点 '{inp.source}' 没有对应的输出",
                                related_node=inp.source,
                                related_spec=inp.name
                            ))
                    else:
                        issues.append(BindIssue(
                            node_id=task.node_id,
                            name=task.name,
                            issue_type=BindStatus.MISSING_OUTPUT,
                            description=f"输入来源节点 '{inp.source}' 不存在",
                            related_node=inp.source,
                            related_spec=inp.name
                        ))
        
        # 检查依赖关系对应的输出输入
        for task in subtasks:
            for dep in task.dependencies:
                source_task = self._find_task(subtasks, dep.dependency_id)
                if source_task:
                    # 检查是否有输出被当前任务使用
                    has_connection = False
                    for outp in source_task.outputs:
                        for inp in task.inputs:
                            if outp.name == inp.name and inp.type == outp.type:
                                if not any(link.from_node == source_task.node_id 
                                          and link.from_output == outp.name 
                                          and link.to_node == task.node_id 
                                          and link.to_input == inp.name 
                                          for link in bound_links):
                                    bound_links.append(BoundLink(
                                        from_node=source_task.node_id,
                                        from_output=outp.name,
                                        to_node=task.node_id,
                                        to_input=inp.name,
                                        bind_type="implied_dependency",
                                        is_valid=True
                                    ))
                                has_connection = True
                    
                    if not has_connection and len(source_task.outputs) > 0 and len(task.inputs) > 0:
                        # 有依赖但没有输出输入连接
                        issues.append(BindIssue(
                            node_id=task.node_id,
                            name=task.name,
                            issue_type=BindStatus.NO_CONNECTION,
                            description=f"依赖节点 '{source_task.name}' 的输出没有被使用",
                            related_node=source_task.node_id
                        ))
        
        # 检查未被使用的输出
        used_outputs = set((link.from_node, link.from_output) for link in bound_links)
        for task in subtasks:
            for outp in task.outputs:
                if (task.node_id, outp.name) not in used_outputs:
                    issues.append(BindIssue(
                        node_id=task.node_id,
                        name=task.name,
                        issue_type=BindStatus.UNNECESSARY_OUTPUT,
                        description=f"输出 '{outp.name}' 没有被其他节点使用",
                        related_spec=outp.name
                    ))
        
        # 统计
        valid_count = len(bound_links)
        issue_count = len(issues)
        is_valid = issue_count == 0
        
        return LinkValidatedTopology(
            original_topology=topology,
            bound_links=bound_links,
            issues=issues,
            is_valid=is_valid,
            valid_count=valid_count,
            issue_count=issue_count
        )
    
    def _build_output_map(self, subtasks: List[SubTaskNode]) -> Dict[Tuple[str, str], OutputSpec]:
        """
        构建输出映射
        """
        output_map = {}
        for task in subtasks:
            for outp in task.outputs:
                key = (task.node_id, outp.name)
                output_map[key] = outp
        return output_map
    
    def _find_task(self, subtasks: List[SubTaskNode], node_id: str) -> Optional[SubTaskNode]:
        """
        查找任务
        """
        for task in subtasks:
            if task.node_id == node_id:
                return task
        return None
    
    def validated_to_dict(self, validated: LinkValidatedTopology) -> Dict[str, Any]:
        """
        将验证后的拓扑转换为字典
        """
        return {
            "is_valid": validated.is_valid,
            "valid_count": validated.valid_count,
            "issue_count": validated.issue_count,
            "original_valid": validated.original_topology.is_valid,
            "bound_links": [
                {
                    "from_node": link.from_node,
                    "from_output": link.from_output,
                    "to_node": link.to_node,
                    "to_input": link.to_input,
                    "bind_type": link.bind_type,
                    "is_valid": link.is_valid
                }
                for link in validated.bound_links
            ],
            "issues": [
                {
                    "node_id": issue.node_id,
                    "name": issue.name,
                    "issue_type": issue.issue_type.value,
                    "description": issue.description,
                    "related_node": issue.related_node,
                    "related_spec": issue.related_spec
                }
                for issue in validated.issues
            ]
        }


# 便捷函数
def validate_task_links(subtasks: List[SubTaskNode]) -> LinkValidatedTopology:
    """
    便捷函数：验证任务链路
    
    Args:
        subtasks: 子任务列表
        
    Returns:
        LinkValidatedTopology: 验证后的拓扑
    """
    binder = LinkBinder()
    return binder.validate_links(subtasks)


def validate_and_get_dict(subtasks: List[SubTaskNode]) -> Dict[str, Any]:
    """
    便捷函数：验证链路并获取字典格式
    
    Args:
        subtasks: 子任务列表
        
    Returns:
        Dict[str, Any]: 验证结果字典
    """
    binder = LinkBinder()
    validated = binder.validate_links(subtasks)
    return binder.validated_to_dict(validated)
