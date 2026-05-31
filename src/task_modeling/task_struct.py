"""
Task四元组结构体定义
基于第一性原理的AI Agent任务规划系统
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
import json
import time


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class MeasurableCriterion:
    """可衡量标准"""
    id: str
    description: str
    type: str  # "boolean" | "numeric" | "qualitative"
    threshold: Any
    unit: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "description": self.description,
            "type": self.type,
            "threshold": self.threshold,
            "unit": self.unit
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MeasurableCriterion':
        """从字典创建"""
        return cls(**data)


@dataclass
class Target:
    """目标 - Task四元组之一"""
    id: str
    description: str
    measurable_criteria: List[MeasurableCriterion]
    priority: int = 1  # 1-10, 10最高
    
    def is_valid(self) -> bool:
        """验证目标是否有效"""
        if not self.id or not self.description:
            return False
        if len(self.measurable_criteria) == 0:
            return False
        if self.priority < 1 or self.priority > 10:
            return False
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "description": self.description,
            "measurable_criteria": [c.to_dict() for c in self.measurable_criteria],
            "priority": self.priority
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Target':
        """从字典创建"""
        criteria = [MeasurableCriterion.from_dict(c) for c in data.get("measurable_criteria", [])]
        return cls(
            id=data["id"],
            description=data["description"],
            measurable_criteria=criteria,
            priority=data.get("priority", 1)
        )


@dataclass
class ConditionItem:
    """前置条件项"""
    id: str
    description: str
    type: str  # "existence" | "value" | "state"
    check_rule: str  # 机器可执行的检查规则
    required: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "description": self.description,
            "type": self.type,
            "check_rule": self.check_rule,
            "required": self.required
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConditionItem':
        """从字典创建"""
        return cls(**data)


@dataclass
class Condition:
    """前置条件 - Task四元组之二"""
    conditions: List[ConditionItem]
    logical_operator: str = "AND"  # "AND" | "OR"
    
    def is_valid(self) -> bool:
        """验证前置条件是否有效"""
        for cond in self.conditions:
            if not cond.id or not cond.description or not cond.check_rule:
                return False
        return self.logical_operator in ["AND", "OR"]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "conditions": [c.to_dict() for c in self.conditions],
            "logical_operator": self.logical_operator
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Condition':
        """从字典创建"""
        conditions = [ConditionItem.from_dict(c) for c in data.get("conditions", [])]
        return cls(
            conditions=conditions,
            logical_operator=data.get("logical_operator", "AND")
        )


@dataclass
class ScopeBoundary:
    """范围边界"""
    inclusions: List[str] = field(default_factory=list)
    exclusions: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "inclusions": self.inclusions,
            "exclusions": self.exclusions
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScopeBoundary':
        """从字典创建"""
        return cls(**data)


@dataclass
class ResourceBoundary:
    """资源约束"""
    max_time_seconds: Optional[float] = None
    max_cost: Optional[float] = None
    max_iterations: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "max_time_seconds": self.max_time_seconds,
            "max_cost": self.max_cost,
            "max_iterations": self.max_iterations
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ResourceBoundary':
        """从字典创建"""
        return cls(**data)


@dataclass
class QualityBoundary:
    """质量约束"""
    min_accuracy: Optional[float] = None
    max_error_rate: Optional[float] = None
    other_constraints: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "min_accuracy": self.min_accuracy,
            "max_error_rate": self.max_error_rate,
            "other_constraints": self.other_constraints
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QualityBoundary':
        """从字典创建"""
        return cls(**data)


@dataclass
class Boundary:
    """边界约束 - Task四元组之三"""
    scope: ScopeBoundary
    resources: ResourceBoundary
    quality: Optional[QualityBoundary] = None
    
    def is_valid(self) -> bool:
        """验证边界是否有效"""
        if not self.scope or not self.resources:
            return False
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            "scope": self.scope.to_dict(),
            "resources": self.resources.to_dict()
        }
        if self.quality:
            result["quality"] = self.quality.to_dict()
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Boundary':
        """从字典创建"""
        scope = ScopeBoundary.from_dict(data["scope"]) if "scope" in data else ScopeBoundary()
        resources = ResourceBoundary.from_dict(data["resources"]) if "resources" in data else ResourceBoundary()
        quality = QualityBoundary.from_dict(data["quality"]) if "quality" in data else None
        return cls(scope=scope, resources=resources, quality=quality)


@dataclass
class SuccessCondition:
    """成功终止条件"""
    id: str
    description: str
    check_rule: str  # 机器可执行的检查规则
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "description": self.description,
            "check_rule": self.check_rule
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SuccessCondition':
        """从字典创建"""
        return cls(**data)


@dataclass
class FailureCondition:
    """失败终止条件"""
    id: str
    description: str
    check_rule: str  # 机器可执行的检查规则
    priority: int = 1
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "description": self.description,
            "check_rule": self.check_rule,
            "priority": self.priority
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FailureCondition':
        """从字典创建"""
        return cls(**data)


@dataclass
class EndRule:
    """终止规则 - Task四元组之四"""
    success_conditions: List[SuccessCondition]
    failure_conditions: List[FailureCondition]
    evaluation_logic: str = ""
    
    def is_valid(self) -> bool:
        """验证终止规则是否有效"""
        if len(self.success_conditions) == 0:
            return False
        for cond in self.success_conditions + self.failure_conditions:
            if not cond.id or not cond.description or not cond.check_rule:
                return False
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "success_conditions": [c.to_dict() for c in self.success_conditions],
            "failure_conditions": [c.to_dict() for c in self.failure_conditions],
            "evaluation_logic": self.evaluation_logic
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EndRule':
        """从字典创建"""
        success_conditions = [SuccessCondition.from_dict(c) for c in data.get("success_conditions", [])]
        failure_conditions = [FailureCondition.from_dict(c) for c in data.get("failure_conditions", [])]
        return cls(
            success_conditions=success_conditions,
            failure_conditions=failure_conditions,
            evaluation_logic=data.get("evaluation_logic", "")
        )


@dataclass
class Task:
    """Task四元组 - 完整的任务结构"""
    id: str
    target: Target
    condition: Condition
    boundary: Boundary
    end_rule: EndRule
    status: TaskStatus = TaskStatus.PENDING
    created_at: float = field(default_factory=lambda: time.time())
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """初始化后验证"""
        if not self.target.is_valid():
            raise ValueError("Invalid target configuration")
        if not self.condition.is_valid():
            raise ValueError("Invalid condition configuration")
        if not self.boundary.is_valid():
            raise ValueError("Invalid boundary configuration")
        if not self.end_rule.is_valid():
            raise ValueError("Invalid endRule configuration")
    
    def is_valid(self) -> bool:
        """验证Task四元组是否完全有效"""
        try:
            return (self.target.is_valid() and 
                    self.condition.is_valid() and 
                    self.boundary.is_valid() and 
                    self.end_rule.is_valid())
        except Exception:
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "target": self.target.to_dict(),
            "condition": self.condition.to_dict(),
            "boundary": self.boundary.to_dict(),
            "end_rule": self.end_rule.to_dict(),
            "status": self.status.value,
            "created_at": self.created_at,
            "metadata": self.metadata
        }
    
    def to_json(self, indent: int = 2) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """从字典创建Task"""
        target = Target.from_dict(data["target"])
        condition = Condition.from_dict(data["condition"])
        boundary = Boundary.from_dict(data["boundary"])
        end_rule = EndRule.from_dict(data["end_rule"])
        status = TaskStatus(data.get("status", "pending"))
        
        return cls(
            id=data["id"],
            target=target,
            condition=condition,
            boundary=boundary,
            end_rule=end_rule,
            status=status,
            created_at=data.get("created_at", time.time()),
            metadata=data.get("metadata", {})
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Task':
        """从JSON字符串创建Task"""
        data = json.loads(json_str)
        return cls.from_dict(data)


# 示例Task创建函数
def create_example_task() -> Task:
    """创建一个示例Task四元组"""
    # 目标
    target = Target(
        id="T-REPORT-2024",
        description="生成2024年度中国区销售分析报告",
        measurable_criteria=[
            MeasurableCriterion(
                id="MC-001",
                description="报告页数>=50页",
                type="numeric",
                threshold=50,
                unit="页"
            ),
            MeasurableCriterion(
                id="MC-002",
                description="包含4个季度完整数据",
                type="boolean",
                threshold=True
            ),
            MeasurableCriterion(
                id="MC-003",
                description="包含至少10张图表",
                type="numeric",
                threshold=10,
                unit="张"
            )
        ],
        priority=9
    )
    
    # 前置条件
    condition = Condition(
        conditions=[
            ConditionItem(
                id="C-001",
                description="Q1销售数据存在",
                type="existence",
                check_rule="file_exists('/data/2024_q1.csv')"
            ),
            ConditionItem(
                id="C-002",
                description="Q2销售数据存在",
                type="existence",
                check_rule="file_exists('/data/2024_q2.csv')"
            ),
            ConditionItem(
                id="C-003",
                description="Q3销售数据存在",
                type="existence",
                check_rule="file_exists('/data/2024_q3.csv')"
            ),
            ConditionItem(
                id="C-004",
                description="Q4销售数据存在",
                type="existence",
                check_rule="file_exists('/data/2024_q4.csv')"
            )
        ],
        logical_operator="AND"
    )
    
    # 边界约束
    boundary = Boundary(
        scope=ScopeBoundary(
            inclusions=["2024年度", "中国区", "销售数据"],
            exclusions=["海外业务", "非销售数据", "2023年及之前数据"]
        ),
        resources=ResourceBoundary(
            max_time_seconds=7200,
            max_cost=500,
            max_iterations=5
        ),
        quality=QualityBoundary(
            min_accuracy=0.98,
            max_error_rate=0.005
        )
    )
    
    # 终止规则
    end_rule = EndRule(
        success_conditions=[
            SuccessCondition(
                id="SC-001",
                description="报告PDF文件已生成",
                check_rule="file_exists('/output/2024_sales_report.pdf') == True"
            ),
            SuccessCondition(
                id="SC-002",
                description="所有可衡量标准满足",
                check_rule="all_measurable_criteria_met() == True"
            ),
            SuccessCondition(
                id="SC-003",
                description="报告文件大小>1MB",
                check_rule="file_size('/output/2024_sales_report.pdf') > 1048576"
            )
        ],
        failure_conditions=[
            FailureCondition(
                id="FC-001",
                description="执行超时",
                check_rule="elapsed_time() > 7200",
                priority=1
            ),
            FailureCondition(
                id="FC-002",
                description="超过最大迭代次数",
                check_rule="iteration_count() >= 5",
                priority=2
            ),
            FailureCondition(
                id="FC-003",
                description="连续错误超过3次",
                check_rule="consecutive_errors() >= 3",
                priority=3
            )
        ],
        evaluation_logic="success: (SC-001 AND SC-002 AND SC-003); failure: (FC-001 OR FC-002 OR FC-003)"
    )
    
    return Task(
        id="TASK-20240526-001",
        target=target,
        condition=condition,
        boundary=boundary,
        end_rule=end_rule
    )
