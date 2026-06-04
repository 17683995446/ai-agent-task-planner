"""
规划结果结构化可视化输出模块
基于第一性原理的AI Agent任务规划系统

核心功能：
- 规划结果结构化输出
- 支持JSON/Markdown/文本格式
- 可视化展示
- 支持导出
"""

import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime

from task_modeling.task_struct import Task
from topology.subtask_node import SubTaskNode
from atomic_actions.atomic_action_struct import AtomicAction


@dataclass
class PlanResult:
    """规划结果"""
    task_id: str
    requirement: str
    task: Optional[Task] = None
    subtasks: List[SubTaskNode] = field(default_factory=list)
    atomic_actions: List[AtomicAction] = field(default_factory=list)
    validation_passed: bool = False
    execution_time: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)


class ResultVisualizer:
    """
    规划结果可视化器
    
    功能：
    - 结构化输出规划结果
    - 支持多种输出格式
    - 可视化展示
    - 支持导出
    """
    
    def __init__(self):
        """初始化可视化器"""
        pass
    
    def to_json(self, result: PlanResult, indent: int = 2) -> str:
        """
        转换为JSON格式
        
        Args:
            result: 规划结果
            indent: 缩进空格数
            
        Returns:
            str: JSON字符串
        """
        data = self._to_dict(result)
        return json.dumps(data, ensure_ascii=False, indent=indent)
    
    def to_markdown(self, result: PlanResult) -> str:
        """
        转换为Markdown格式
        
        Args:
            result: 规划结果
            
        Returns:
            str: Markdown字符串
        """
        lines = []
        
        # 标题
        lines.append(f"# 任务规划结果")
        lines.append(f"\n**任务ID**: `{result.task_id}`")
        lines.append(f"**时间**: {result.timestamp}")
        lines.append(f"**执行时间**: {result.execution_time:.3f}s")
        lines.append(f"**验证状态**: {'✅ 通过' if result.validation_passed else '❌ 未通过'}")
        
        # 需求
        lines.append(f"\n## 原始需求")
        lines.append(f"\n{result.requirement}")
        
        # 任务目标
        if result.task and result.task.target:
            lines.append(f"\n## 任务目标")
            lines.append(f"\n**目标**: {result.task.target.description}")
            if hasattr(result.task.target, 'measurable_criteria') and result.task.target.measurable_criteria:
                lines.append(f"**可衡量标准**:")
                for criterion in result.task.target.measurable_criteria:
                    lines.append(f"  - {criterion}")
        
        # 子任务
        if result.subtasks:
            lines.append(f"\n## 子任务分解 ({len(result.subtasks)}个)")
            for i, subtask in enumerate(result.subtasks, 1):
                lines.append(f"\n### {i}. {subtask.name if hasattr(subtask, 'name') else f'子任务{i}'}")
                lines.append(f"- **描述**: {subtask.description if hasattr(subtask, 'description') else '无描述'}")
                lines.append(f"- **复杂度**: {subtask.complexity.value if hasattr(subtask, 'complexity') else '未知'}")
                if hasattr(subtask, 'dependencies') and subtask.dependencies:
                    lines.append(f"- **依赖**: {len(subtask.dependencies)}个")
        
        # 原子动作
        if result.atomic_actions:
            lines.append(f"\n## 原子动作队列 ({len(result.atomic_actions)}个)")
            for i, action in enumerate(result.atomic_actions, 1):
                lines.append(f"\n### {i}. {action.name}")
                lines.append(f"- **描述**: {action.description}")
                lines.append(f"- **类型**: {action.action_type.value}")
                if action.inputs:
                    input_names = [i.name if hasattr(i, 'name') else str(i) for i in action.inputs]
                    lines.append(f"- **输入**: {', '.join(input_names)}")
                if action.outputs:
                    output_names = [o.name if hasattr(o, 'name') else str(o) for o in action.outputs]
                    lines.append(f"- **输出**: {', '.join(output_names)}")
        
        # 元数据
        if result.metadata:
            lines.append(f"\n## 元数据")
            for key, value in result.metadata.items():
                lines.append(f"- **{key}**: {value}")
        
        return "\n".join(lines)
    
    def to_text(self, result: PlanResult) -> str:
        """
        转换为纯文本格式
        
        Args:
            result: 规划结果
            
        Returns:
            str: 文本字符串
        """
        lines = []
        
        lines.append("=" * 60)
        lines.append("任务规划结果")
        lines.append("=" * 60)
        lines.append(f"任务ID: {result.task_id}")
        lines.append(f"时间: {result.timestamp}")
        lines.append(f"执行时间: {result.execution_time:.3f}s")
        lines.append(f"验证状态: {'通过' if result.validation_passed else '未通过'}")
        
        lines.append(f"\n原始需求: {result.requirement}")
        
        if result.task and result.task.target:
            lines.append(f"\n任务目标: {result.task.target.description}")
        
        if result.subtasks:
            lines.append(f"\n子任务分解 ({len(result.subtasks)}个):")
            for i, subtask in enumerate(result.subtasks, 1):
                name = subtask.name if hasattr(subtask, 'name') else f'子任务{i}'
                lines.append(f"  {i}. {name}")
        
        if result.atomic_actions:
            lines.append(f"\n原子动作队列 ({len(result.atomic_actions)}个):")
            for i, action in enumerate(result.atomic_actions, 1):
                lines.append(f"  {i}. {action.name} - {action.description}")
        
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    def to_tree(self, result: PlanResult) -> str:
        """
        转换为树形结构
        
        Args:
            result: 规划结果
            
        Returns:
            str: 树形字符串
        """
        lines = []
        
        lines.append("📋 任务规划")
        lines.append(f"├── 🎯 需求: {result.requirement[:50]}...")
        
        if result.task and result.task.target:
            lines.append(f"├── 🎯 目标: {result.task.target.description[:50]}...")
        
        if result.subtasks:
            lines.append(f"├── 📦 子任务 ({len(result.subtasks)}个)")
            for i, subtask in enumerate(result.subtasks):
                is_last = (i == len(result.subtasks) - 1)
                prefix = "└──" if is_last else "├──"
                name = subtask.name if hasattr(subtask, 'name') else f'子任务{i+1}'
                lines.append(f"│   {prefix} 📄 {name}")
        
        if result.atomic_actions:
            lines.append(f"└── ⚡ 原子动作 ({len(result.atomic_actions)}个)")
            for i, action in enumerate(result.atomic_actions):
                is_last = (i == len(result.atomic_actions) - 1)
                prefix = "    └──" if is_last else "    ├──"
                lines.append(f"{prefix} ⚙️  {action.name}")
        
        return "\n".join(lines)
    
    def _to_dict(self, result: PlanResult) -> Dict[str, Any]:
        """
        转换为字典
        
        Args:
            result: 规划结果
            
        Returns:
            Dict[str, Any]: 字典
        """
        return {
            "task_id": result.task_id,
            "requirement": result.requirement,
            "timestamp": result.timestamp,
            "execution_time": result.execution_time,
            "validation_passed": result.validation_passed,
            "task": {
                "target": result.task.target.description if result.task and result.task.target else None,
                "condition": str(result.task.condition) if result.task and result.task.condition else None,
                "boundary": str(result.task.boundary) if result.task and result.task.boundary else None
            } if result.task else None,
            "subtasks": [
                {
                    "name": s.name if hasattr(s, 'name') else f'子任务{i+1}',
                    "description": s.description if hasattr(s, 'description') else '',
                    "complexity": s.complexity.value if hasattr(s, 'complexity') else 'unknown'
                }
                for i, s in enumerate(result.subtasks)
            ],
            "atomic_actions": [
                {
                    "name": a.name,
                    "description": a.description,
                    "type": a.action_type.value
                }
                for a in result.atomic_actions
            ],
            "metadata": result.metadata
        }
    
    def export(self, result: PlanResult, filepath: str, format: str = "json") -> bool:
        """
        导出结果到文件
        
        Args:
            result: 规划结果
            filepath: 文件路径
            format: 格式 (json/markdown/text)
            
        Returns:
            bool: 是否成功
        """
        try:
            if format == "json":
                content = self.to_json(result)
            elif format == "markdown":
                content = self.to_markdown(result)
            elif format == "text":
                content = self.to_text(result)
            else:
                return False
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return True
        except Exception:
            return False


# 使用示例
if __name__ == "__main__":
    print("=" * 60)
    print("规划结果可视化输出 - 使用示例")
    print("=" * 60)
    
    from interfaces.orchestrator_interface import OrchestratorInterface
    
    # 执行规划
    orchestrator = OrchestratorInterface()
    result = orchestrator.plan_task("开发一个用户登录系统")
    
    # 创建可视化器
    visualizer = ResultVisualizer()
    
    # 创建规划结果
    plan_result = PlanResult(
        task_id=result.task_id,
        requirement="开发一个用户登录系统",
        task=result.modeling_result.task if result.modeling_result else None,
        subtasks=result.topology_result.subtasks if result.topology_result else [],
        atomic_actions=result.atomic_result.actions if result.atomic_result else [],
        validation_passed=result.validation_result.is_valid if result.validation_result else False,
        execution_time=result.execution_time
    )
    
    # 1. JSON输出
    print("\n1. JSON格式:")
    json_output = visualizer.to_json(plan_result)
    print(json_output[:500] + "...")
    
    # 2. Markdown输出
    print("\n2. Markdown格式:")
    md_output = visualizer.to_markdown(plan_result)
    print(md_output[:500] + "...")
    
    # 3. 文本输出
    print("\n3. 文本格式:")
    text_output = visualizer.to_text(plan_result)
    print(text_output[:500] + "...")
    
    # 4. 树形输出
    print("\n4. 树形格式:")
    tree_output = visualizer.to_tree(plan_result)
    print(tree_output)
    
    print("\n" + "=" * 60)
    print("规划结果可视化输出 - 示例完成")
    print("=" * 60)
