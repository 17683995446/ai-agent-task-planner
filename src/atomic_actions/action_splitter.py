"""
第三层：原子动作收敛层 - 复合动作自动拆分工具
基于第一性原理的AI Agent任务规划系统

核心功能：
- 将复合动作自动拆解为原子动作序列
- 多种拆分策略：流程化、并行化、依赖导向
- 自动建立动作间依赖关系
- 智能输入输出匹配
"""

from typing import List, Dict, Any, Optional, Set, Union
from dataclasses import dataclass
from enum import Enum
import re

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from atomic_action_struct import (
    AtomicAction, AtomicActionQueue, AtomicActionStatus, AtomicActionType,
    AtomicCondition, ActionInput, ActionOutput, ActionConstraint,
    create_atomic_action
)


class SplitStrategy(Enum):
    """拆分策略"""
    SEQUENTIAL = "sequential"     # 顺序拆分
    PARALLEL = "parallel"         # 并行拆分
    DEPENDENCY_BASED = "dependency_based"  # 基于依赖拆分
    DATA_FLOW = "data_flow"       # 基于数据流拆分


@dataclass
class SplitPattern:
    """拆分模式"""
    pattern: str                   # 正则表达式
    strategy: SplitStrategy        # 拆分策略
    action_type: AtomicActionType  # 生成的动作类型
    name_template: str             # 名称模板
    description_template: str      # 描述模板


@dataclass
class CompositeAction:
    """复合动作（待拆分）"""
    composite_id: str
    name: str
    description: str
    steps: List[str] = None  # 拆分步骤描述
    raw_description: str = ""  # 原始描述
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.steps is None:
            self.steps = []
        if self.metadata is None:
            self.metadata = {}


class ActionSplitter:
    """
    复合动作自动拆分工具
    
    功能：
    - 将粗步骤自动拆解细化为原子动作序列
    - 多种拆分策略支持
    - 自动建立依赖关系
    - 智能输入输出匹配
    """
    
    def __init__(self):
        self.patterns = self._init_default_patterns()
    
    def _init_default_patterns(self) -> List[SplitPattern]:
        """初始化默认拆分模式"""
        return [
            SplitPattern(
                pattern=r'读取|加载|获取|下载',
                strategy=SplitStrategy.SEQUENTIAL,
                action_type=AtomicActionType.DATA_READ,
                name_template="读取{resource}",
                description_template="读取{resource}数据"
            ),
            SplitPattern(
                pattern=r'写入|保存|存储|上传',
                strategy=SplitStrategy.SEQUENTIAL,
                action_type=AtomicActionType.DATA_WRITE,
                name_template="写入{resource}",
                description_template="写入{resource}数据"
            ),
            SplitPattern(
                pattern=r'处理|转换|解析|计算',
                strategy=SplitStrategy.SEQUENTIAL,
                action_type=AtomicActionType.TRANSFORM,
                name_template="处理{resource}",
                description_template="处理和转换{resource}数据"
            ),
            SplitPattern(
                pattern=r'验证|检查|确认|校验',
                strategy=SplitStrategy.SEQUENTIAL,
                action_type=AtomicActionType.VALIDATION,
                name_template="验证{resource}",
                description_template="验证{resource}数据"
            ),
            SplitPattern(
                pattern=r'调用|请求|API|接口',
                strategy=SplitStrategy.SEQUENTIAL,
                action_type=AtomicActionType.API_CALL,
                name_template="调用{resource}",
                description_template="调用{resource}API接口"
            ),
            SplitPattern(
                pattern=r'文件|文档|读写|IO',
                strategy=SplitStrategy.SEQUENTIAL,
                action_type=AtomicActionType.FILE_IO,
                name_template="文件{resource}",
                description_template="执行文件{resource}操作"
            )
        ]
    
    def split_composite_action(
        self,
        composite: CompositeAction,
        strategy: SplitStrategy = SplitStrategy.SEQUENTIAL
    ) -> AtomicActionQueue:
        """
        拆分复合动作为原子动作队列
        
        Args:
            composite: 复合动作对象
            strategy: 拆分策略
        
        Returns:
            AtomicActionQueue: 原子动作队列
        """
        queue = AtomicActionQueue(
            queue_id=f"split_{composite.composite_id}",
            name=f"{composite.name} - 拆分队列"
        )
        
        if composite.steps:
            # 有明确步骤时按步骤拆分
            actions = self._split_by_steps(composite, strategy)
        else:
            # 无明确步骤时从描述推断
            actions = self._split_by_description(composite, strategy)
        
        # 添加到队列
        queue.add_actions(actions)
        
        return queue
    
    def _split_by_steps(
        self,
        composite: CompositeAction,
        strategy: SplitStrategy
    ) -> List[AtomicAction]:
        """按步骤拆分"""
        actions = []
        
        for i, step in enumerate(composite.steps):
            # 解析步骤生成原子动作
            action = self._parse_step_to_action(
                step,
                i,
                composite.composite_id,
                strategy
            )
            
            # 添加依赖关系
            if i > 0:
                prev_action = actions[i-1]
                action.add_dependency(prev_action.action_id)
            
            actions.append(action)
        
        return actions
    
    def _split_by_description(
        self,
        composite: CompositeAction,
        strategy: SplitStrategy
    ) -> List[AtomicAction]:
        """从描述推断拆分"""
        actions = []
        
        # 尝试匹配常见模式
        description = composite.raw_description or composite.description
        
        # 1. 尝试模式匹配
        matched = self._try_pattern_match(description, composite)
        if matched:
            actions.extend(matched)
        
        # 2. 无匹配时创建默认动作
        if not actions:
            default_action = self._create_default_action(
                composite,
                len(actions)
            )
            actions.append(default_action)
        
        # 建立依赖关系
        if strategy == SplitStrategy.SEQUENTIAL:
            for i in range(1, len(actions)):
                prev_action = actions[i-1]
                actions[i].add_dependency(prev_action.action_id)
        
        return actions
    
    def _try_pattern_match(
        self,
        description: str,
        composite: CompositeAction
    ) -> List[AtomicAction]:
        """尝试模式匹配"""
        actions = []
        
        # 简单的分词匹配
        for pattern in self.patterns:
            if re.search(pattern.pattern, description):
                # 找到匹配的模式
                resource = self._extract_resource(description, pattern.pattern)
                
                action_id = f"{composite.composite_id}_step_{len(actions)}"
                action_name = pattern.name_template.format(resource=resource)
                
                action = create_atomic_action(
                    action_id=action_id,
                    name=action_name,
                    description=pattern.description_template.format(resource=resource),
                    action_type=pattern.action_type
                )
                
                # 添加默认输入输出
                if pattern.action_type == AtomicActionType.DATA_READ:
                    action.add_input("source", "string", required=True)
                    action.add_output("data", "any")
                elif pattern.action_type == AtomicActionType.DATA_WRITE:
                    action.add_input("data", "any", required=True)
                    action.add_output("result", "dict")
                elif pattern.action_type == AtomicActionType.TRANSFORM:
                    action.add_input("input", "any", required=True)
                    action.add_output("output", "any")
                
                # 标记原子条件
                action.add_atomic_condition(AtomicCondition.SINGLE_RESPONSIBILITY)
                
                actions.append(action)
        
        return actions
    
    def _extract_resource(self, description: str, pattern: str) -> str:
        """从描述中提取资源名称"""
        # 简单实现：尝试提取关键词
        description = description.strip()
        
        # 尝试匹配常见资源名
        keywords = ['数据', '文件', '配置', '结果', '报告', '消息', '通知']
        for keyword in keywords:
            if keyword in description:
                return keyword
        
        # 尝试提取第一个有意义的词
        words = re.split(r'[,、，\s]+', description)
        for word in words:
            if len(word) > 2 and word not in ['读取', '写入', '调用', '处理']:
                return word
        
        return "数据"
    
    def _parse_step_to_action(
        self,
        step: str,
        step_index: int,
        composite_id: str,
        strategy: SplitStrategy
    ) -> AtomicAction:
        """解析步骤为原子动作"""
        action_id = f"{composite_id}_step_{step_index}"
        
        # 确定动作类型
        action_type = self._infer_action_type(step)
        
        action = create_atomic_action(
            action_id=action_id,
            name=step.strip(),
            description=f"步骤{step_index+1}：{step.strip()}",
            action_type=action_type
        )
        
        # 添加默认输入输出
        action.add_input("input", "any", required=False)
        action.add_output("output", "any")
        
        # 标记原子条件
        action.add_atomic_condition(AtomicCondition.SINGLE_RESPONSIBILITY)
        
        return action
    
    def _infer_action_type(self, step: str) -> AtomicActionType:
        """推断动作类型"""
        for pattern in self.patterns:
            if re.search(pattern.pattern, step):
                return pattern.action_type
        
        return AtomicActionType.CUSTOM
    
    def _create_default_action(
        self,
        composite: CompositeAction,
        index: int
    ) -> AtomicAction:
        """创建默认原子动作"""
        action_id = f"{composite.composite_id}_default"
        
        action = create_atomic_action(
            action_id=action_id,
            name=composite.name,
            description=composite.description,
            action_type=AtomicActionType.CUSTOM
        )
        
        # 添加默认输入输出
        action.add_input("input", "any", required=False)
        action.add_output("output", "any")
        
        # 标记原子条件
        action.add_atomic_condition(AtomicCondition.SINGLE_RESPONSIBILITY)
        
        return action
    
    def split_with_strategy(
        self,
        composite: CompositeAction,
        strategy: SplitStrategy = SplitStrategy.SEQUENTIAL
    ) -> Dict[str, Any]:
        """
        使用指定策略拆分
        
        Returns:
            Dict包含:
            - queue: AtomicActionQueue
            - strategy: 使用的策略
            - action_count: 动作数量
        """
        queue = self.split_composite_action(composite, strategy)
        
        return {
            "queue": queue,
            "strategy": strategy.value,
            "action_count": len(queue.actions)
        }
    
    def add_custom_pattern(
        self,
        pattern: str,
        strategy: SplitStrategy,
        action_type: AtomicActionType,
        name_template: str,
        description_template: str
    ):
        """添加自定义拆分模式"""
        self.patterns.append(SplitPattern(
            pattern=pattern,
            strategy=strategy,
            action_type=action_type,
            name_template=name_template,
            description_template=description_template
        ))


# 便捷函数
def split_composite_to_atomic(
    composite_id: str,
    name: str,
    description: str,
    steps: Optional[List[str]] = None,
    strategy: SplitStrategy = SplitStrategy.SEQUENTIAL
) -> AtomicActionQueue:
    """
    便捷函数：拆分复合动作为原子动作
    
    Args:
        composite_id: 复合动作ID
        name: 名称
        description: 描述
        steps: 步骤列表
        strategy: 拆分策略
    
    Returns:
        AtomicActionQueue: 原子动作队列
    """
    composite = CompositeAction(
        composite_id=composite_id,
        name=name,
        description=description,
        steps=steps
    )
    
    splitter = ActionSplitter()
    return splitter.split_composite_action(composite, strategy)
