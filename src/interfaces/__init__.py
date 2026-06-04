"""
接口层 - 各模块独立接口封装
基于第一性原理的AI Agent任务规划系统

核心功能：
- 定义各层标准接口
- 实现接口适配器
- 彻底解耦各模块
"""

from .modeling_interface import ModelingInterface, ModelingResult
from .topology_interface import TopologyInterface, TopologyResult
from .atomic_interface import AtomicInterface, AtomicResult
from .validation_interface import ValidationInterface, ValidationResult
from .orchestrator_interface import OrchestratorInterface

__all__ = [
    'ModelingInterface',
    'ModelingResult',
    'TopologyInterface',
    'TopologyResult',
    'AtomicInterface',
    'AtomicResult',
    'ValidationInterface',
    'ValidationResult',
    'OrchestratorInterface'
]
