"""
第二层：拓扑依赖拆解层 - 子任务节点标准数据结构
基于第一性原理的AI Agent任务规划系统
"""

import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class SubTaskStatus(Enum):
    """子任务状态"""
    PENDING = "pending"        # 待执行
    READY = "ready"            # 就绪（依赖已满足）
    RUNNING = "running"         # 执行中
    COMPLETED = "completed"       # 已完成
    FAILED = "failed"          # 已失败
    SKIPPED = "skipped"         # 已跳过


class DependencyType(Enum):
    """依赖类型"""
    HARD = "hard"            # 强依赖（必须完成才能执行）
    SOFT = "soft"            # 软依赖（推荐但不强制）
    RECOMMENDED = "recommended"  # 推荐依赖


@dataclass
class InputSpec:
    """输入规格"""
    name: str
    type: str
    required: bool = True
    description: str = ""
    default: Any = None
    source: Optional[str] = None  # 来源：某个子任务的输出


@dataclass
class OutputSpec:
    """输出规格"""
    name: str
    type: str
    description: str = ""


@dataclass
class Dependency:
    """依赖关系"""
    dependency_id: str
    dependency_type: DependencyType = DependencyType.HARD
    description: str = ""
    condition: Optional[str] = None  # 依赖满足条件（可选，用于条件依赖）


@dataclass
class SubTaskNode:
    """
    子任务节点标准数据结构
    包含：输入、输出、依赖、权重、状态
    """
    node_id: str
    name: str
    description: str
    
    # 基础信息
    parent_task_id: Optional[str] = None  # 父任务ID
    sequence: int = 0
    
    # 输入输出
    inputs: List[InputSpec] = field(default_factory=list)
    outputs: List[OutputSpec] = field(default_factory=list)
    
    # 依赖关系
    dependencies: List[Dependency] = field(default_factory=list)
    
    # 权重与优先级
    priority: int = 5  # 1-10，越高越优先
    weight: float = 1.0  # 权重，用于调度优化
    
    # 状态管理
    status: SubTaskStatus = SubTaskStatus.PENDING
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    duration_estimated: Optional[float] = None  # 预估耗时
    actual_duration: Optional[float] = None  # 实际耗时
    
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    
    def __post_init__(self):
        """初始化后验证"""
        pass
    
    def is_ready(self) -> bool:
        """判断是否就绪（依赖是否全部满足"""
        # 注意：这里仅做结构定义，实际判断需要外部传入依赖状态
        return self.status in [SubTaskStatus.PENDING, SubTaskStatus.READY]
    
    def mark_started(self):
        """标记为开始执行"""
        self.status = SubTaskStatus.RUNNING
        self.start_time = time.time()
        self.updated_at = time.time()
    
    def mark_completed(self):
        """标记为完成"""
        self.status = SubTaskStatus.COMPLETED
        self.end_time = time.time()
        if self.start_time:
            self.actual_duration = self.end_time - self.start_time
        self.updated_at = time.time()
    
    def mark_failed(self):
        """标记为失败"""
        self.status = SubTaskStatus.FAILED
        self.end_time = time.time()
        if self.start_time:
            self.actual_duration = self.end_time - self.start_time
        self.updated_at = time.time()
    
    def add_input(self, name: str, input_type: str, required: bool = True, description: str = ""):
        """添加输入规格"""
        self.inputs.append(InputSpec(name=name, type=input_type, required=required, description=description))
        self.updated_at = time.time()
    
    def add_output(self, name: str, output_type: str, description: str = ""):
        """添加输出规格"""
        self.outputs.append(OutputSpec(name=name, type=output_type, description=description))
        self.updated_at = time.time()
    
    def add_dependency(self, dependency_id: str, dep_type: DependencyType = DependencyType.HARD, description: str = ""):
        """添加依赖"""
        self.dependencies.append(Dependency(dependency_id=dependency_id, dependency_type=dep_type, description=description))
        self.updated_at = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "node_id": self.node_id,
            "name": self.name,
            "description": self.description,
            "parent_task_id": self.parent_task_id,
            "sequence": self.sequence,
            "inputs": [
                {
                    "name": inp.name,
                    "type": inp.type,
                    "required": inp.required,
                    "description": inp.description,
                    "default": inp.default,
                    "source": inp.source
                }
                for inp in self.inputs
            ],
            "outputs": [
                {
                    "name": out.name,
                    "type": out.type,
                    "description": out.description
                }
                for out in self.outputs
            ],
            "dependencies": [
                {
                    "dependency_id": dep.dependency_id,
                    "dependency_type": dep.dependency_type.value,
                    "description": dep.description,
                    "condition": dep.condition
                }
                for dep in self.dependencies
            ],
            "priority": self.priority,
            "weight": self.weight,
            "status": self.status.value,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_estimated": self.duration_estimated,
            "actual_duration": self.actual_duration,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SubTaskNode':
        """从字典创建对象"""
        node = cls(
            node_id=data["node_id"],
            name=data["name"],
            description=data["description"],
            parent_task_id=data.get("parent_task_id"),
            sequence=data.get("sequence", 0),
            priority=data.get("priority", 5),
            weight=data.get("weight", 1.0),
            status=SubTaskStatus(data.get("status", "pending")),
            start_time=data.get("start_time"),
            end_time=data.get("end_time"),
            duration_estimated=data.get("duration_estimated"),
            actual_duration=data.get("actual_duration"),
            metadata=data.get("metadata", {}),
            created_at=data.get("created_at", time.time()),
            updated_at=data.get("updated_at", time.time())
        )
        
        for inp_data in data.get("inputs", []):
            node.add_input(
                name=inp_data["name"],
                input_type=inp_data["type"],
                required=inp_data.get("required", True),
                description=inp_data.get("description", "")
            )
            if "default" in inp_data:
                node.inputs[-1].default = inp_data["default"]
            if "source" in inp_data:
                node.inputs[-1].source = inp_data["source"]
        
        for out_data in data.get("outputs", []):
            node.add_output(
                name=out_data["name"],
                output_type=out_data["type"],
                description=out_data.get("description", "")
            )
        
        for dep_data in data.get("dependencies", []):
            node.add_dependency(
                dependency_id=dep_data["dependency_id"],
                dep_type=DependencyType(dep_data.get("dependency_type", "hard")),
                description=dep_data.get("description", "")
            )
            if "condition" in dep_data:
                node.dependencies[-1].condition = dep_data["condition"]
        
        return node
