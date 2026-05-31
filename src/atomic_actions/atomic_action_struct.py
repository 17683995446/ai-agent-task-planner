"""
第三层：原子动作收敛层 - 原子动作标准存储结构
基于第一性原理的AI Agent任务规划系统

核心概念：
- 原子动作：最小执行单元，不可再拆分
- 动作输入/输出：明确的输入输出定义
- 动作依赖：前置条件和依赖关系
- 动作约束：执行时间、权限等约束
- 动作判定：三大原子判定条件
"""

from typing import List, Dict, Any, Optional, Set, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class AtomicActionStatus(Enum):
    """原子动作状态"""
    PENDING = "pending"       # 待执行
    READY = "ready"           # 就绪
    RUNNING = "running"       # 执行中
    COMPLETED = "completed"   # 已完成
    FAILED = "failed"         # 失败
    SKIPPED = "skipped"       # 跳过


class AtomicActionType(Enum):
    """原子动作类型"""
    DATA_READ = "data_read"           # 数据读取
    DATA_WRITE = "data_write"         # 数据写入
    TRANSFORM = "transform"           # 数据转换
    API_CALL = "api_call"             # API调用
    FILE_IO = "file_io"               # 文件读写
    NETWORK = "network"               # 网络操作
    COMPUTATION = "computation"       # 计算操作
    VALIDATION = "validation"         # 验证操作
    DECISION = "decision"             # 决策操作
    CUSTOM = "custom"                 # 自定义操作


class AtomicCondition(Enum):
    """原子判定条件"""
    SINGLE_RESPONSIBILITY = "single_responsibility"  # 单一职责原则
    SIDE_EFFECT_FREE = "side_effect_free"           # 无副作用原则
    IDEMPOTENT = "idempotent"                        # 幂等性原则


@dataclass
class ActionInput:
    """原子动作输入定义"""
    name: str                          # 输入名称
    type: str                         # 输入类型
    required: bool = True             # 是否必需
    description: str = ""             # 描述
    default: Optional[Any] = None     # 默认值
    constraints: Optional[Dict] = None  # 约束条件
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "type": self.type,
            "required": self.required,
            "description": self.description,
            "default": self.default,
            "constraints": self.constraints
        }


@dataclass
class ActionOutput:
    """原子动作输出定义"""
    name: str                          # 输出名称
    type: str                         # 输出类型
    description: str = ""             # 描述
    constraints: Optional[Dict] = None  # 约束条件
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "constraints": self.constraints
        }


@dataclass
class ActionConstraint:
    """原子动作约束"""
    max_execution_time: Optional[float] = None  # 最大执行时间（秒）
    required_permissions: List[str] = field(default_factory=list)  # 所需权限
    resource_limits: Optional[Dict] = None     # 资源限制
    retry_policy: Optional[Dict] = None        # 重试策略
    timeout_policy: Optional[Dict] = None      # 超时策略
    
    def to_dict(self) -> Dict:
        return {
            "max_execution_time": self.max_execution_time,
            "required_permissions": self.required_permissions,
            "resource_limits": self.resource_limits,
            "retry_policy": self.retry_policy,
            "timeout_policy": self.timeout_policy
        }


@dataclass
class AtomicAction:
    """
    原子动作 - 最小执行单元
    
    特性：
    - 单一职责：只做一件事
    - 无副作用：不改变外部状态（或明确声明）
    - 幂等性：多次执行结果一致
    - 可序列化：可持久化存储
    """
    action_id: str                      # 动作唯一标识
    name: str                          # 动作名称
    description: str                   # 动作描述
    action_type: AtomicActionType      # 动作类型
    
    inputs: List[ActionInput] = field(default_factory=list)   # 输入定义
    outputs: List[ActionOutput] = field(default_factory=list) # 输出定义
    
    dependencies: List[str] = field(default_factory=list)    # 依赖的前置动作ID
    constraints: ActionConstraint = field(default_factory=ActionConstraint)  # 约束条件
    
    atomic_conditions: Set[AtomicCondition] = field(default_factory=set)  # 满足的原子条件
    
    status: AtomicActionStatus = AtomicActionStatus.PENDING  # 当前状态
    priority: int = 5                     # 优先级 (1-10，1最高)
    
    metadata: Dict[str, Any] = field(default_factory=dict)  # 扩展元数据
    created_at: float = field(default_factory=datetime.now().timestamp)
    updated_at: float = field(default_factory=datetime.now().timestamp)
    
    def add_input(self, name: str, type: str, required: bool = True,
                 description: str = "", default: Optional[Any] = None,
                 constraints: Optional[Dict] = None) -> 'AtomicAction':
        """添加输入定义"""
        self.inputs.append(ActionInput(
            name=name,
            type=type,
            required=required,
            description=description,
            default=default,
            constraints=constraints
        ))
        self.updated_at = datetime.now().timestamp
        return self
    
    def add_output(self, name: str, type: str, description: str = "",
                  constraints: Optional[Dict] = None) -> 'AtomicAction':
        """添加输出定义"""
        self.outputs.append(ActionOutput(
            name=name,
            type=type,
            description=description,
            constraints=constraints
        ))
        self.updated_at = datetime.now().timestamp
        return self
    
    def add_dependency(self, dependency_id: str) -> 'AtomicAction':
        """添加依赖"""
        if dependency_id not in self.dependencies:
            self.dependencies.append(dependency_id)
        self.updated_at = datetime.now().timestamp
        return self
    
    def add_atomic_condition(self, condition: AtomicCondition) -> 'AtomicAction':
        """添加原子条件"""
        self.atomic_conditions.add(condition)
        self.updated_at = datetime.now().timestamp
        return self
    
    def update_status(self, status: AtomicActionStatus) -> 'AtomicAction':
        """更新状态"""
        self.status = status
        self.updated_at = datetime.now().timestamp
        return self
    
    def is_ready(self) -> bool:
        """检查是否就绪"""
        return self.status == AtomicActionStatus.READY
    
    def is_completed(self) -> bool:
        """检查是否完成"""
        return self.status == AtomicActionStatus.COMPLETED
    
    def is_failed(self) -> bool:
        """检查是否失败"""
        return self.status == AtomicActionStatus.FAILED
    
    def validate_atomic_conditions(self) -> Dict[str, bool]:
        """验证原子条件"""
        return {
            condition.value: condition in self.atomic_conditions
            for condition in AtomicCondition
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "action_id": self.action_id,
            "name": self.name,
            "description": self.description,
            "action_type": self.action_type.value,
            "inputs": [inp.to_dict() for inp in self.inputs],
            "outputs": [out.to_dict() for out in self.outputs],
            "dependencies": self.dependencies,
            "constraints": self.constraints.to_dict(),
            "atomic_conditions": [cond.value for cond in self.atomic_conditions],
            "status": self.status.value,
            "priority": self.priority,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AtomicAction':
        """从字典创建"""
        action_type = AtomicActionType(data["action_type"])
        atomic_conditions = {
            AtomicCondition(cond) for cond in data.get("atomic_conditions", [])
        }
        status = AtomicActionStatus(data.get("status", "pending"))
        
        constraints = ActionConstraint(**data.get("constraints", {}))
        
        inputs = [ActionInput(**inp) for inp in data.get("inputs", [])]
        outputs = [ActionOutput(**out) for out in data.get("outputs", [])]
        
        return cls(
            action_id=data["action_id"],
            name=data["name"],
            description=data["description"],
            action_type=action_type,
            inputs=inputs,
            outputs=outputs,
            dependencies=data.get("dependencies", []),
            constraints=constraints,
            atomic_conditions=atomic_conditions,
            status=status,
            priority=data.get("priority", 5),
            metadata=data.get("metadata", {}),
            created_at=data.get("created_at", datetime.now().timestamp),
            updated_at=data.get("updated_at", datetime.now().timestamp)
        )


@dataclass
class AtomicActionQueue:
    """原子动作队列"""
    queue_id: str
    name: str
    actions: List[AtomicAction] = field(default_factory=list)
    status: str = "pending"
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=datetime.now().timestamp)
    
    def add_action(self, action: AtomicAction) -> 'AtomicActionQueue':
        """添加动作"""
        self.actions.append(action)
        return self
    
    def add_actions(self, actions: List[AtomicAction]) -> 'AtomicActionQueue':
        """批量添加动作"""
        self.actions.extend(actions)
        return self
    
    def get_action(self, action_id: str) -> Optional[AtomicAction]:
        """获取动作"""
        for action in self.actions:
            if action.action_id == action_id:
                return action
        return None
    
    def get_pending_actions(self) -> List[AtomicAction]:
        """获取待执行动作"""
        return [a for a in self.actions if a.status == AtomicActionStatus.PENDING]
    
    def get_ready_actions(self) -> List[AtomicAction]:
        """获取就绪动作"""
        return [a for a in self.actions if a.status == AtomicActionStatus.READY]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "queue_id": self.queue_id,
            "name": self.name,
            "actions": [a.to_dict() for a in self.actions],
            "status": self.status,
            "metadata": self.metadata,
            "created_at": self.created_at
        }


def create_atomic_action(
    action_id: str,
    name: str,
    description: str,
    action_type: AtomicActionType,
    priority: int = 5
) -> AtomicAction:
    """
    便捷函数：创建原子动作
    
    Args:
        action_id: 动作唯一标识
        name: 动作名称
        description: 动作描述
        action_type: 动作类型
        priority: 优先级 (1-10)
    
    Returns:
        AtomicAction: 原子动作实例
    """
    return AtomicAction(
        action_id=action_id,
        name=name,
        description=description,
        action_type=action_type,
        priority=priority
    )
