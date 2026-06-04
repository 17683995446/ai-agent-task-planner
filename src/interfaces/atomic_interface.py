"""
第三层接口封装 - 原子动作收敛层接口
基于第一性原理的AI Agent任务规划系统

核心功能：
- 定义原子层标准接口
- 封装所有原子操作
- 对外提供统一调用方式
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from topology.subtask_node import SubTaskNode
from atomic_actions.atomic_action_struct import AtomicAction
from atomic_actions.action_splitter import split_composite_to_atomic
from atomic_actions.atomic_validator import validate_atomic_actions
from atomic_actions.atomic_queue_generator import generate_atomic_queue_from_subtasks


@dataclass
class AtomicResult:
    """原子结果"""
    success: bool
    actions: List[AtomicAction] = field(default_factory=list)
    error_message: str = ""
    queue_info: Dict[str, Any] = field(default_factory=dict)


class AtomicInterface:
    """
    原子动作收敛层接口
    
    功能：
    - 封装所有原子操作
    - 提供统一调用入口
    - 实现错误处理和日志记录
    """
    
    def __init__(self):
        """初始化原子接口"""
        pass
    
    def split_to_atomic(self, subtasks: List[SubTaskNode]) -> AtomicResult:
        """
        将子任务拆分为原子动作
        
        Args:
            subtasks: 子任务列表
            
        Returns:
            AtomicResult: 原子结果
        """
        try:
            all_actions = []
            
            for subtask in subtasks:
                actions = split_composite_to_atomic(
                    composite_id=subtask.node_id if hasattr(subtask, 'node_id') else str(subtask),
                    name=subtask.name if hasattr(subtask, 'name') else "unnamed",
                    description=subtask.description if hasattr(subtask, 'description') else ""
                )
                all_actions.extend(actions.actions)
            
            # 验证原子动作
            validated_result = validate_atomic_actions(all_actions)
            valid_actions = validated_result.valid_actions if hasattr(validated_result, 'valid_actions') else all_actions
            
            return AtomicResult(
                success=True,
                actions=valid_actions,
                queue_info={
                    "total_actions": len(all_actions),
                    "valid_actions": len(valid_actions)
                }
            )
        except Exception as e:
            return AtomicResult(
                success=False,
                error_message=str(e)
            )
    
    def generate_queue(self, subtasks: List[SubTaskNode]) -> Dict[str, Any]:
        """
        生成执行队列
        
        Args:
            subtasks: 子任务列表
            
        Returns:
            Dict[str, Any]: 队列信息
        """
        try:
            queue = generate_atomic_queue_from_subtasks(subtasks)
            return {
                "success": True,
                "queue_length": len(queue.actions) if hasattr(queue, 'actions') else 0,
                "queue": queue
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
