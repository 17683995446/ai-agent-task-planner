"""
第二层：拓扑依赖拆解层 - 一级子任务智能拆分引擎
基于第一性原理的AI Agent任务规划系统
"""

import re
from typing import List, Dict, Any, Optional
from enum import Enum

from .subtask_node import (
    SubTaskNode, SubTaskStatus, DependencyType, InputSpec, OutputSpec, Dependency
)


class SplitStrategy(Enum):
    """拆分策略"""
    BY_CRITERION = "by_criterion"    # 按可衡量标准拆分
    BY_CONDITION = "by_condition"     # 按前置条件拆分
    BY_PHASE = "by_phase"           # 按执行阶段拆分
    BY_PARALLEL = "by_parallel"      # 按可并行部分拆分


class SubTaskSplitter:
    """
    子任务智能拆分引擎
    功能：从Task自动拆解合理子任务
    """
    
    def __init__(self):
        """初始化拆分引擎"""
        self.task_id_counter = 0
    
    def split_task(
        self,
        task_description: str,
        task_id: str = "",
        strategy: SplitStrategy = SplitStrategy.BY_PHASE
    ) -> List[SubTaskNode]:
        """
        拆分任务为一级子任务
        
        Args:
            task_description: 任务描述
            task_id: 任务ID
            strategy: 拆分策略
            
        Returns:
            SubTaskNode列表
        """
        subtasks = []
        self.task_id_counter = 0
        
        if strategy == SplitStrategy.BY_PHASE:
            subtasks = self._split_by_phase(task_description, task_id)
        elif strategy == SplitStrategy.BY_CRITERION:
            subtasks = self._split_by_criterion(task_description, task_id)
        elif strategy == SplitStrategy.BY_CONDITION:
            subtasks = self._split_by_condition(task_description, task_id)
        elif strategy == SplitStrategy.BY_PARALLEL:
            subtasks = self._split_by_parallel(task_description, task_id)
        
        # 设置默认依赖关系（序列依赖）
        subtasks = self._setup_default_dependencies(subtasks)
        
        return subtasks
    
    def _split_by_phase(self, task_description: str, task_id: str) -> List[SubTaskNode]:
        """
        按执行阶段拆分（最通用的策略）
        """
        subtasks = []
        
        # 阶段1：分析与理解
        analyze_task = self._create_subtask(
            parent_task_id=task_id,
            sequence=1,
            name="任务分析",
            description="分析任务要求，理解目标与约束",
            outputs=[("task_requirements", "dict", "任务需求分析结果")]
        )
        subtasks.append(analyze_task)
        
        # 阶段2：准备与规划
        prepare_task = self._create_subtask(
            parent_task_id=task_id,
            sequence=2,
            name="准备规划",
            description="准备执行环境，制定详细执行计划",
            inputs=[("task_requirements", "dict", "任务需求分析结果")],
            outputs=[("execution_plan", "dict", "详细执行计划")]
        )
        subtasks.append(prepare_task)
        
        # 阶段3：执行与处理
        execute_task = self._create_subtask(
            parent_task_id=task_id,
            sequence=3,
            name="核心执行",
            description="执行核心任务逻辑，处理主要工作",
            inputs=[("execution_plan", "dict", "详细执行计划")],
            outputs=[("raw_result", "dict", "原始执行结果")]
        )
        subtasks.append(execute_task)
        
        # 阶段4：验证与优化
        verify_task = self._create_subtask(
            parent_task_id=task_id,
            sequence=4,
            name="验证优化",
            description="验证执行结果，进行必要优化",
            inputs=[("raw_result", "dict", "原始执行结果")],
            outputs=[("verified_result", "dict", "验证后的结果")]
        )
        subtasks.append(verify_task)
        
        # 阶段5：交付与收尾
        deliver_task = self._create_subtask(
            parent_task_id=task_id,
            sequence=5,
            name="交付收尾",
            description="整理结果，完成最终交付",
            inputs=[("verified_result", "dict", "验证后的结果")],
            outputs=[("final_output", "any", "最终交付结果")]
        )
        subtasks.append(deliver_task)
        
        return subtasks
    
    def _split_by_criterion(self, task_description: str, task_id: str) -> List[SubTaskNode]:
        """
        按可衡量标准拆分
        """
        subtasks = []
        
        # 通用可衡量标准的任务拆分
        subtasks.append(self._create_subtask(
            parent_task_id=task_id,
            sequence=1,
            name="标准分析",
            description="分析各项衡量标准，确定优先级",
            outputs=[("criteria_priorities", "dict", "标准优先级")]
        ))
        
        subtasks.append(self._create_subtask(
            parent_task_id=task_id,
            sequence=2,
            name="目标达成",
            description="执行工作以达成各项衡量标准",
            inputs=[("criteria_priorities", "dict", "标准优先级")],
            outputs=[("criteria_fulfillment", "dict", "标准达成情况")]
        ))
        
        subtasks.append(self._create_subtask(
            parent_task_id=task_id,
            sequence=3,
            name="标准验证",
            description="验证所有标准是否已满足",
            inputs=[("criteria_fulfillment", "dict", "标准达成情况")],
            outputs=[("validation_result", "bool", "验证结果")]
        ))
        
        return subtasks
    
    def _split_by_condition(self, task_description: str, task_id: str) -> List[SubTaskNode]:
        """
        按前置条件拆分
        """
        subtasks = []
        
        subtasks.append(self._create_subtask(
            parent_task_id=task_id,
            sequence=1,
            name="条件准备",
            description="检查并准备所有前置条件",
            outputs=[("conditions_ready", "bool", "条件准备状态")]
        ))
        
        subtasks.append(self._create_subtask(
            parent_task_id=task_id,
            sequence=2,
            name="核心执行",
            description="在条件满足的情况下执行任务",
            inputs=[("conditions_ready", "bool", "条件准备状态")],
            outputs=[("execution_result", "dict", "执行结果")]
        ))
        
        return subtasks
    
    def _split_by_parallel(self, task_description: str, task_id: str) -> List[SubTaskNode]:
        """
        按可并行部分拆分
        """
        subtasks = []
        
        # 共同的准备阶段
        subtasks.append(self._create_subtask(
            parent_task_id=task_id,
            sequence=0,
            name="公共准备",
            description="为所有并行任务做准备",
            outputs=[("shared_data", "dict", "共享数据")]
        ))
        
        # 并行分支1
        subtasks.append(self._create_subtask(
            parent_task_id=task_id,
            sequence=1,
            name="并行任务A",
            description="执行可并行的第一部分工作",
            inputs=[("shared_data", "dict", "共享数据")],
            outputs=[("result_a", "any", "并行结果A")],
            priority=5
        ))
        
        # 并行分支2
        subtasks.append(self._create_subtask(
            parent_task_id=task_id,
            sequence=2,
            name="并行任务B",
            description="执行可并行的第二部分工作",
            inputs=[("shared_data", "dict", "共享数据")],
            outputs=[("result_b", "any", "并行结果B")],
            priority=5
        ))
        
        # 合并阶段
        subtasks.append(self._create_subtask(
            parent_task_id=task_id,
            sequence=3,
            name="结果合并",
            description="合并所有并行任务的结果",
            inputs=[
                ("result_a", "any", "并行结果A"),
                ("result_b", "any", "并行结果B")
            ],
            outputs=[("final_result", "any", "合并后的结果")]
        ))
        
        return subtasks
    
    def _create_subtask(
        self,
        parent_task_id: str,
        sequence: int,
        name: str,
        description: str,
        inputs: Optional[List[tuple]] = None,
        outputs: Optional[List[tuple]] = None,
        priority: int = 5,
        weight: float = 1.0
    ) -> SubTaskNode:
        """
        创建子任务节点
        
        Args:
            parent_task_id: 父任务ID
            sequence: 序号
            name: 子任务名称
            description: 描述
            inputs: 输入规格列表 [(name, type, description), ...]
            outputs: 输出规格列表 [(name, type, description), ...]
            priority: 优先级
            weight: 权重
            
        Returns:
            SubTaskNode
        """
        self.task_id_counter += 1
        node_id = f"{parent_task_id}-sub-{self.task_id_counter}" if parent_task_id else f"sub-{self.task_id_counter}"
        
        node = SubTaskNode(
            node_id=node_id,
            name=name,
            description=description,
            parent_task_id=parent_task_id,
            sequence=sequence,
            priority=priority,
            weight=weight
        )
        
        # 添加输入
        if inputs:
            for inp_name, inp_type, inp_desc in inputs:
                node.add_input(inp_name, inp_type, required=True, description=inp_desc)
        
        # 添加输出
        if outputs:
            for out_name, out_type, out_desc in outputs:
                node.add_output(out_name, out_type, description=out_desc)
        
        return node
    
    def _setup_default_dependencies(self, subtasks: List[SubTaskNode]) -> List[SubTaskNode]:
        """
        设置默认的依赖关系（序列依赖）
        
        Args:
            subtasks: 子任务列表
            
        Returns:
            更新后的子任务列表
        """
        for i in range(1, len(subtasks)):
            current = subtasks[i]
            previous = subtasks[i-1]
            current.add_dependency(
                previous.node_id,
                DependencyType.HARD,
                f"依赖于{previous.name}的完成"
            )
        
        return subtasks


# 便捷函数
def split_task_into_subtasks(
    task_description: str,
    task_id: str = "",
    strategy: str = "by_phase"
) -> List[SubTaskNode]:
    """
    便捷函数：拆分任务为子任务
    
    Args:
        task_description: 任务描述
        task_id: 任务ID
        strategy: 拆分策略
        
    Returns:
        SubTaskNode列表
    """
    strategy_map = {
        "by_phase": SplitStrategy.BY_PHASE,
        "by_criterion": SplitStrategy.BY_CRITERION,
        "by_condition": SplitStrategy.BY_CONDITION,
        "by_parallel": SplitStrategy.BY_PARALLEL
    }
    
    splitter = SubTaskSplitter()
    return splitter.split_task(task_description, task_id, strategy_map.get(strategy, SplitStrategy.BY_PHASE))
