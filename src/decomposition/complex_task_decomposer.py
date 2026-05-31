"""
第四层：分段校验收敛层 - 复杂任务分解引擎
基于第一性原理的AI Agent任务规划系统

核心功能：
- 任务解析与标准化
- 智能分解策略（树形/序列/并行）
- 依赖管理与排序
- 任务复杂度评估
"""

import sys
import os
import json
import time
from typing import List, Dict, Any, Optional, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import deque, defaultdict

# 导入现有任务结构
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

from task_modeling.task_struct import (
    Task, Target, Condition, Boundary, EndRule, TaskStatus,
    MeasurableCriterion, ConditionItem, ScopeBoundary,
    ResourceBoundary, QualityBoundary, SuccessCondition
)
from topology.subtask_node import SubTaskNode, SubTaskStatus
from validation.logger_manager import get_logger

logger = get_logger('task.decomposition')


class DecompositionStrategy(Enum):
    """任务分解策略"""
    TREE = "tree"              # 树形分解（层次化）
    SEQUENTIAL = "sequential"  # 序列分解（线性）
    PARALLEL = "parallel"       # 并行分解
    MIXED = "mixed"            # 混合策略
    AUTO = "auto"              # 自动选择策略


class TaskComplexity(Enum):
    """任务复杂度级别"""
    VERY_SIMPLE = 1
    SIMPLE = 2
    MEDIUM = 3
    COMPLEX = 4
    VERY_COMPLEX = 5


@dataclass
class DecompositionRule:
    """分解规则"""
    id: str
    name: str
    description: str
    strategy: DecompositionStrategy
    max_depth: int = 3
    min_subtasks: int = 2
    max_subtasks: int = 10
    parallel_threshold: float = 0.5  # 并行度阈值


@dataclass
class TaskGraphNode:
    """任务图节点"""
    task_id: str
    name: str
    description: str
    complexity: float
    subtasks: List[str] = field(default_factory=list)  # 子任务ID
    dependencies: List[str] = field(default_factory=list)  # 依赖的任务ID
    priority: int = 5
    estimated_duration: float = 0.0
    can_parallelize: bool = False
    is_atomic: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "name": self.name,
            "description": self.description,
            "complexity": self.complexity,
            "subtasks": self.subtasks,
            "dependencies": self.dependencies,
            "priority": self.priority,
            "estimated_duration": self.estimated_duration,
            "can_parallelize": self.can_parallelize,
            "is_atomic": self.is_atomic
        }


@dataclass
class DecompositionResult:
    """分解结果"""
    original_task: Task
    strategy: DecompositionStrategy
    task_graph: Dict[str, TaskGraphNode]
    execution_order: List[str]
    complexity_score: float
    decomposition_depth: int
    validation_passed: bool = True
    warnings: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "original_task": self.original_task.to_dict(),
            "strategy": self.strategy.value,
            "task_graph": {k: v.to_dict() for k, v in self.task_graph.items()},
            "execution_order": self.execution_order,
            "complexity_score": self.complexity_score,
            "decomposition_depth": self.decomposition_depth,
            "validation_passed": self.validation_passed,
            "warnings": self.warnings
        }


class ComplexTaskDecomposer:
    """
    复杂任务分解引擎
    
    功能：
    - 任务解析与标准化
    - 智能分解策略（树形/序列/并行）
    - 依赖管理与排序
    - 任务复杂度评估
    """
    
    def __init__(self, default_strategy: DecompositionStrategy = DecompositionStrategy.AUTO):
        self.default_strategy = default_strategy
        self.atomic_threshold = 0.2  # 原子任务复杂度阈值
        self.max_depth = 5
        self.task_counter = 0
        self.rules = self._init_default_rules()
        
        logger.info(f"✅ 复杂任务分解引擎初始化 (策略: {default_strategy.value})")
    
    def _init_default_rules(self) -> List[DecompositionRule]:
        """初始化默认分解规则"""
        return [
            DecompositionRule(
                id="rule_simple",
                name="简单任务分解",
                description="用于简单任务的序列分解",
                strategy=DecompositionStrategy.SEQUENTIAL,
                max_depth=1,
                min_subtasks=2,
                max_subtasks=5
            ),
            DecompositionRule(
                id="rule_medium",
                name="中等任务分解",
                description="用于中等复杂度的混合分解",
                strategy=DecompositionStrategy.MIXED,
                max_depth=3,
                min_subtasks=3,
                max_subtasks=15
            ),
            DecompositionRule(
                id="rule_complex",
                name="复杂任务分解",
                description="用于复杂任务的树形分解",
                strategy=DecompositionStrategy.TREE,
                max_depth=5,
                min_subtasks=5,
                max_subtasks=30
            )
        ]
    
    def decompose_task(
        self,
        task: Task,
        strategy: Optional[DecompositionStrategy] = None,
        max_depth: Optional[int] = None
    ) -> DecompositionResult:
        """
        分解复杂任务
        
        Args:
            task: 原始任务
            strategy: 分解策略，默认使用自动选择
            max_depth: 最大分解深度
            
        Returns:
            DecompositionResult: 分解结果
        """
        logger.info(f"开始分解任务: {task.id}")
        
        # 1. 评估任务复杂度
        complexity = self._evaluate_complexity(task)
        logger.debug(f"任务复杂度: {complexity.name} (分数: {complexity.value})")
        
        # 2. 选择分解策略
        chosen_strategy = strategy or self._select_strategy(complexity, task)
        logger.debug(f"选择策略: {chosen_strategy.value}")
        
        # 3. 执行分解
        max_d = max_depth or self.max_depth
        task_graph = self._perform_decomposition(task, chosen_strategy, max_d)
        
        # 4. 拓扑排序
        execution_order = self._topological_sort(task_graph)
        
        # 5. 验证分解结果
        validation_result = self._validate_decomposition(task_graph, execution_order)
        
        result = DecompositionResult(
            original_task=task,
            strategy=chosen_strategy,
            task_graph=task_graph,
            execution_order=execution_order,
            complexity_score=complexity.value,
            decomposition_depth=max_d,
            validation_passed=validation_result["valid"],
            warnings=validation_result["warnings"]
        )
        
        logger.info(f"分解完成: {len(task_graph)}个任务，{len(execution_order)}个执行步骤")
        return result
    
    def _evaluate_complexity(self, task: Task) -> TaskComplexity:
        """评估任务复杂度"""
        score = 0.0
        
        # 目标数量（使用可衡量标准数量代替）
        score += len(task.target.measurable_criteria) * 0.5
        
        # 条件数量
        score += len(task.condition.conditions) * 0.3
        
        # 边界约束
        boundary_score = 0
        if task.boundary.resources.max_time_seconds:
            boundary_score += 0.5
        if task.boundary.resources.max_cost:
            boundary_score += 0.3
        if task.boundary.quality:
            boundary_score += 0.4
        score += boundary_score
        
        # 结束规则数量
        if task.end_rule:
            score += len(task.end_rule.success_conditions) * 0.2
        
        # 描述长度
        if len(task.target.description) > 500:
            score += 1.0
        elif len(task.target.description) > 200:
            score += 0.5
        
        # 转换为复杂度级别
        if score < 1.0:
            return TaskComplexity.VERY_SIMPLE
        elif score < 2.0:
            return TaskComplexity.SIMPLE
        elif score < 4.0:
            return TaskComplexity.MEDIUM
        elif score < 6.0:
            return TaskComplexity.COMPLEX
        else:
            return TaskComplexity.VERY_COMPLEX
    
    def _select_strategy(
        self,
        complexity: TaskComplexity,
        task: Task
    ) -> DecompositionStrategy:
        """根据复杂度自动选择策略"""
        if self.default_strategy != DecompositionStrategy.AUTO:
            return self.default_strategy
        
        # 简单任务用序列
        if complexity in [TaskComplexity.VERY_SIMPLE, TaskComplexity.SIMPLE]:
            return DecompositionStrategy.SEQUENTIAL
        # 中等任务用混合
        elif complexity == TaskComplexity.MEDIUM:
            return DecompositionStrategy.MIXED
        # 复杂任务用树形
        else:
            return DecompositionStrategy.TREE
    
    def _perform_decomposition(
        self,
        task: Task,
        strategy: DecompositionStrategy,
        max_depth: int
    ) -> Dict[str, TaskGraphNode]:
        """执行实际的分解"""
        self.task_counter = 0
        task_graph = {}
        
        # 创建根节点
        root_id = self._generate_task_id()
        root_complexity = self._evaluate_complexity(task).value
        root_node = TaskGraphNode(
            task_id=root_id,
            name=f"{task.target.description[:30]}...",
            description=task.target.description,
            complexity=root_complexity,
            priority=task.target.priority or 5
        )
        task_graph[root_id] = root_node
        
        # 根据策略执行分解
        if strategy == DecompositionStrategy.TREE:
            self._decompose_tree(task, root_id, task_graph, 0, max_depth)
        elif strategy == DecompositionStrategy.SEQUENTIAL:
            self._decompose_sequential(task, root_id, task_graph)
        elif strategy == DecompositionStrategy.PARALLEL:
            self._decompose_parallel(task, root_id, task_graph)
        elif strategy == DecompositionStrategy.MIXED:
            self._decompose_mixed(task, root_id, task_graph, max_depth)
        
        return task_graph
    
    def _decompose_tree(
        self,
        task: Task,
        parent_id: str,
        task_graph: Dict[str, TaskGraphNode],
        current_depth: int,
        max_depth: int
    ):
        """树形分解"""
        if current_depth >= max_depth:
            # 达到最大深度，标记为原子
            task_graph[parent_id].is_atomic = True
            return
        
        # 基于可衡量标准分解
        subtask_ids = []
        
        # 每个可衡量标准作为一个子任务
        criteria_count = len(task.target.measurable_criteria)
        if criteria_count == 0:
            # 如果没有可衡量标准，使用默认的分解方式
            subtask_count = max(2, min(5, int(task_graph[parent_id].complexity) + 1))
            for i in range(subtask_count):
                subtask_id = self._generate_task_id()
                subtask_complexity = task_graph[parent_id].complexity / (subtask_count + 1)
                
                subtask_node = TaskGraphNode(
                    task_id=subtask_id,
                    name=f"子任务{i+1}: {task.target.description[:20]}",
                    description=f"完成部分任务: {task.target.description}",
                    complexity=subtask_complexity,
                    dependencies=[parent_id],
                    priority=task.target.priority or 5,
                    is_atomic=subtask_complexity < self.atomic_threshold
                )
                task_graph[subtask_id] = subtask_node
                subtask_ids.append(subtask_id)
        else:
            # 基于可衡量标准分解
            for i, criterion in enumerate(task.target.measurable_criteria):
                subtask_id = self._generate_task_id()
                subtask_complexity = task_graph[parent_id].complexity / (criteria_count + 1)
                
                subtask_node = TaskGraphNode(
                    task_id=subtask_id,
                    name=f"标准{i+1}: {criterion.description[:30]}",
                    description=f"达成标准: {criterion.description}",
                    complexity=subtask_complexity,
                    dependencies=[parent_id],
                    priority=task.target.priority or 5,
                    is_atomic=subtask_complexity < self.atomic_threshold
                )
                task_graph[subtask_id] = subtask_node
                subtask_ids.append(subtask_id)
        
        # 更新父节点的子任务
        task_graph[parent_id].subtasks = subtask_ids
        
        logger.debug(f"树形分解: 父节点 {parent_id} 生成 {len(subtask_ids)} 个子任务")
    
    def _decompose_sequential(
        self,
        task: Task,
        parent_id: str,
        task_graph: Dict[str, TaskGraphNode]
    ):
        """序列分解"""
        phases = self._extract_phases(task.target.description)
        subtask_ids = []
        prev_task_id = parent_id
        
        for i, phase in enumerate(phases):
            subtask_id = self._generate_task_id()
            subtask_complexity = task_graph[parent_id].complexity / len(phases)
            
            subtask_node = TaskGraphNode(
                task_id=subtask_id,
                name=f"阶段{i+1}: {phase[:30]}",
                description=phase,
                complexity=subtask_complexity,
                dependencies=[prev_task_id] if i > 0 else [parent_id],
                priority=task.target.priority or 5,
                is_atomic=True
            )
            task_graph[subtask_id] = subtask_node
            subtask_ids.append(subtask_id)
            prev_task_id = subtask_id
        
        # 更新父节点的子任务
        task_graph[parent_id].subtasks = subtask_ids
        
        logger.debug(f"序列分解: 生成 {len(subtask_ids)} 个阶段")
    
    def _decompose_parallel(
        self,
        task: Task,
        parent_id: str,
        task_graph: Dict[str, TaskGraphNode]
    ):
        """并行分解"""
        # 识别可并行的子任务
        parallel_tasks = self._identify_parallel_tasks(task)
        subtask_ids = []
        
        for i, (name, desc) in enumerate(parallel_tasks):
            subtask_id = self._generate_task_id()
            subtask_complexity = task_graph[parent_id].complexity / len(parallel_tasks)
            
            subtask_node = TaskGraphNode(
                task_id=subtask_id,
                name=name,
                description=desc,
                complexity=subtask_complexity,
                dependencies=[parent_id],
                priority=task.priority or 5,
                can_parallelize=True,
                is_atomic=True
            )
            task_graph[subtask_id] = subtask_node
            subtask_ids.append(subtask_id)
        
        # 更新父节点的子任务
        task_graph[parent_id].subtasks = subtask_ids
        
        logger.debug(f"并行分解: 生成 {len(subtask_ids)} 个并行任务")
    
    def _decompose_mixed(
        self,
        task: Task,
        parent_id: str,
        task_graph: Dict[str, TaskGraphNode],
        max_depth: int
    ):
        """混合分解策略"""
        # 先序列分解为阶段
        phases = self._extract_phases(task.target.description)
        
        # 前30%用树形，中间50%用并行，最后20%用序列
        phase_count = len(phases)
        if phase_count == 0:
            self._decompose_tree(task, parent_id, task_graph, 0, max_depth)
            return
        
        # 简化处理：先阶段分解，每个阶段内部用树形
        subtask_ids = []
        prev_task_id = parent_id
        
        for i, phase in enumerate(phases):
            subtask_id = self._generate_task_id()
            subtask_complexity = task_graph[parent_id].complexity / phase_count
            
            subtask_node = TaskGraphNode(
                task_id=subtask_id,
                name=f"阶段{i+1}: {phase[:30]}",
                description=phase,
                complexity=subtask_complexity,
                dependencies=[prev_task_id] if i > 0 else [parent_id],
                priority=task.target.priority or 5
            )
            task_graph[subtask_id] = subtask_node
            subtask_ids.append(subtask_id)
            prev_task_id = subtask_id
            
            # 每个阶段内部用树形分解（如果复杂度高）
            if subtask_complexity > 0.3 and max_depth > 1:
                simplified_task = Task(
                    id=f"{task.id}_phase_{i}",
                    target=task.target,
                    condition=task.condition,
                    boundary=task.boundary,
                    end_rule=task.end_rule
                )
                self._decompose_tree(
                    simplified_task,
                    subtask_id,
                    task_graph,
                    1,
                    max_depth
                )
        
        # 更新父节点的子任务
        task_graph[parent_id].subtasks = subtask_ids
    
    def _extract_phases(self, description: str) -> List[str]:
        """从描述中提取执行阶段"""
        # 简单启发式：查找关键词
        phase_keywords = [
            "首先", "第一步", "1.", "阶段1",
            "然后", "接着", "第二步", "2.",
            "最后", "最终", "第三步", "3."
        ]
        
        # 基于标点分割
        import re
        parts = re.split(r'[，。；；\n]', description)
        phases = []
        
        for part in parts:
            part = part.strip()
            if len(part) > 10:
                phases.append(part)
        
        # 如果太少，使用默认阶段
        if len(phases) < 3:
            phases = [
                "需求分析与理解",
                "方案设计与规划",
                "具体执行与实施",
                "验证与测试",
                "收尾与交付"
            ]
        
        return phases[:8]  # 最多8个阶段
    
    def _identify_parallel_tasks(self, task: Task) -> List[tuple]:
        """识别可并行的任务"""
        parallel_tasks = []
        
        # 基于每个可衡量标准创建一个并行任务
        for i, criterion in enumerate(task.target.measurable_criteria):
            parallel_tasks.append((
                f"达成标准{i+1}",
                f"完成标准: {criterion.description}"
            ))
        
        # 如果标准太少，创建默认并行任务
        if len(parallel_tasks) < 2:
            parallel_tasks = [
                ("数据收集与准备", "收集所有需要的数据和资源"),
                ("核心处理", "执行主要的处理逻辑"),
                ("结果验证", "验证结果的正确性")
            ]
        
        return parallel_tasks
    
    def _topological_sort(self, task_graph: Dict[str, TaskGraphNode]) -> List[str]:
        """拓扑排序"""
        in_degree = defaultdict(int)
        adj = defaultdict(list)
        
        # 构建图
        for task_id, node in task_graph.items():
            in_degree[task_id] = 0
        
        for task_id, node in task_graph.items():
            for dep in node.dependencies:
                if dep in task_graph:
                    adj[dep].append(task_id)
                    in_degree[task_id] += 1
        
        # Kahn算法
        queue = deque()
        for task_id, degree in in_degree.items():
            if degree == 0:
                queue.append(task_id)
        
        result = []
        while queue:
            current = queue.popleft()
            result.append(current)
            
            for neighbor in adj[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # 检查是否有环
        if len(result) != len(task_graph):
            logger.warning("检测到循环依赖，使用线性顺序")
            return list(task_graph.keys())
        
        return result
    
    def _validate_decomposition(
        self,
        task_graph: Dict[str, TaskGraphNode],
        execution_order: List[str]
    ) -> Dict[str, Any]:
        """验证分解结果"""
        valid = True
        warnings = []
        
        # 检查是否有空图
        if not task_graph:
            return {"valid": False, "warnings": ["任务图为空"]}
        
        # 检查依赖完整性
        for task_id, node in task_graph.items():
            for dep in node.dependencies:
                if dep not in task_graph:
                    valid = False
                    warnings.append(f"任务 {task_id} 依赖不存在的任务 {dep}")
        
        # 检查原子任务比例
        atomic_count = sum(1 for node in task_graph.values() if node.is_atomic)
        atomic_ratio = atomic_count / len(task_graph)
        
        if atomic_ratio < 0.3:
            warnings.append(f"原子任务比例过低: {atomic_ratio:.1%}")
        
        # 检查是否有过长的依赖链
        max_chain = self._calculate_max_dependency_chain(task_graph, execution_order)
        if max_chain > 20:
            warnings.append(f"依赖链过长: {max_chain}")
        
        return {"valid": valid, "warnings": warnings}
    
    def _calculate_max_dependency_chain(
        self,
        task_graph: Dict[str, TaskGraphNode],
        execution_order: List[str]
    ) -> int:
        """计算最长依赖链"""
        max_length = {}
        
        for task_id in execution_order:
            max_len = 1
            for dep in task_graph[task_id].dependencies:
                if dep in max_length:
                    max_len = max(max_len, max_length[dep] + 1)
            max_length[task_id] = max_len
        
        return max(max_length.values()) if max_length else 0
    
    def _generate_task_id(self) -> str:
        """生成任务ID"""
        self.task_counter += 1
        return f"task_{int(time.time())}_{self.task_counter}"


# 便捷函数
def decompose_task_simple(task: Task) -> DecompositionResult:
    """
    便捷函数：快速分解任务
    
    Args:
        task: 要分解的任务
        
    Returns:
        DecompositionResult: 分解结果
    """
    decomposer = ComplexTaskDecomposer()
    return decomposer.decompose_task(task)


# 使用示例
if __name__ == "__main__":
    print("=" * 60)
    print("复杂任务分解引擎 - 快速测试")
    print("=" * 60)
    
    # 创建一个示例任务
    from task_modeling.task_struct import (
        Target, MeasurableCriterion, ConditionItem, Condition,
        ScopeBoundary, ResourceBoundary, QualityBoundary, Boundary,
        EndRule, SuccessCondition
    )
    
    target = Target(
        id="main_target",
        description="开发一个完整的AI应用程序",
        measurable_criteria=[
            MeasurableCriterion(
                id="c_main",
                description="应用程序开发完成",
                type="boolean",
                threshold=True
            ),
            MeasurableCriterion(
                id="c_arch",
                description="系统架构设计完成",
                type="boolean",
                threshold=True
            ),
            MeasurableCriterion(
                id="c_core",
                description="核心功能开发完成",
                type="boolean",
                threshold=True
            ),
            MeasurableCriterion(
                id="c_test",
                description="测试通过并部署完成",
                type="boolean",
                threshold=True
            )
        ],
        priority=5
    )
    
    condition = Condition(
        conditions=[
            ConditionItem(
                id="cond1",
                description="开发环境就绪",
                type="state",
                check_rule="dev_env_ready()",
                required=True
            ),
            ConditionItem(
                id="cond2",
                description="需求文档完整",
                type="existence",
                check_rule="has_requirements()",
                required=True
            )
        ],
        logical_operator="AND"
    )
    
    boundary = Boundary(
        scope=ScopeBoundary(
            inclusions=["完整应用", "所有模块"],
            exclusions=["第三方服务"]
        ),
        resources=ResourceBoundary(
            max_time_seconds=86400 * 7,  # 7天
            max_cost=10000.0
        ),
        quality=QualityBoundary(
            min_accuracy=0.95,
            max_error_rate=0.05
        )
    )
    
    end_rule = EndRule(
        success_conditions=[
            SuccessCondition(
                id="ac1",
                description="所有功能测试通过",
                check_rule="all_tests_passed()"
            )
        ],
        failure_conditions=[],
        evaluation_logic="success: (all); failure: ()"
    )
    
    task = Task(
        id="complex_app_dev",
        description="开发一个完整的AI应用程序，包括设计架构、开发核心功能、测试部署",
        target=target,
        condition=condition,
        boundary=boundary,
        end_rule=end_rule,
        priority=5
    )
    
    # 创建分解器
    decomposer = ComplexTaskDecomposer()
    
    # 执行分解
    print("\n1. 自动分解:")
    result = decomposer.decompose_task(task)
    
    print(f"\n2. 分解结果:")
    print(f"   策略: {result.strategy.value}")
    print(f"   任务数: {len(result.task_graph)}")
    print(f"   复杂度分数: {result.complexity_score}")
    print(f"   验证通过: {result.validation_passed}")
    
    if result.warnings:
        print(f"\n3. 警告:")
        for warning in result.warnings:
            print(f"   - {warning}")
    
    print(f"\n4. 执行顺序 (前10个):")
    for i, task_id in enumerate(result.execution_order[:10]):
        node = result.task_graph[task_id]
        print(f"   {i+1}. {node.name} (复杂度: {node.complexity:.2f})")
    
    print("\n✅ 快速测试完成！")
