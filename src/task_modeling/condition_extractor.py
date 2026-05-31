"""
前置条件自动识别模块
基于第一性原理的AI Agent任务规划系统
"""

import re
import uuid
from typing import Dict, List, Any, Tuple, Optional
from .task_struct import Condition, ConditionItem


class ConditionExtractionError(Exception):
    """前置条件提取错误异常"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "message": self.message,
            "details": self.details
        }


class ConditionExtractor:
    """前置条件自动识别器"""
    
    def __init__(self):
        """初始化前置条件提取器"""
        self.trigger_keywords = self._init_trigger_keywords()
        self.condition_patterns = self._init_condition_patterns()
        self.type_classifiers = self._init_type_classifiers()
    
    def _init_trigger_keywords(self) -> List[Dict[str, Any]]:
        """初始化触发关键词"""
        return [
            {
                "keywords": ["需要先", "需要提前", "必须先"],
                "type": "时间前置",
                "priority": 3
            },
            {
                "keywords": ["需要", "需要的", "需要有"],
                "type": "资源前置",
                "priority": 2
            },
            {
                "keywords": ["必须", "必须满足", "必须要有"],
                "type": "强制前置",
                "priority": 3
            },
            {
                "keywords": ["前提", "前提是", "前提条件"],
                "type": "逻辑前置",
                "priority": 3
            },
            {
                "keywords": ["依赖", "依赖于"],
                "type": "依赖前置",
                "priority": 3
            }
        ]
    
    def _init_condition_patterns(self) -> List[Dict[str, Any]]:
        """初始化条件模式"""
        return [
            {
                "pattern": r'需要(.+?)(?:[,，。]|$)',
                "type": "存在",
                "description_template": "需要{content}"
            },
            {
                "pattern": r'必须有(.+?)(?:[,，。]|$)',
                "type": "存在",
                "description_template": "必须有{content}"
            },
            {
                "pattern": r'需要先(.+?)(?:[,，。]|$)',
                "type": "时间",
                "description_template": "需要先{content}"
            },
            {
                "pattern": r'前提是(.+?)(?:[,，。]|$)',
                "type": "逻辑",
                "description_template": "前提是{content}"
            },
            {
                "pattern": r'依赖(.+?)(?:[,，。]|$)',
                "type": "依赖",
                "description_template": "依赖{content}"
            }
        ]
    
    def _init_type_classifiers(self) -> List[Dict[str, Any]]:
        """初始化类型分类器"""
        return [
            {
                "type": "existence",
                "name": "存在性检查",
                "keywords": ["文件", "数据", "资源", "内容", "资料"],
                "rule_template": "check_existence('{content}')"
            },
            {
                "type": "value",
                "name": "值检查",
                "keywords": ["大于", "小于", "等于", "超过", "至少", "最多"],
                "rule_template": "check_value('{content}')"
            },
            {
                "type": "state",
                "name": "状态检查",
                "keywords": ["完成", "准备好", "就绪", "可用", "连接"],
                "rule_template": "check_state('{content}')"
            }
        ]
    
    def extract(self, description: str) -> Tuple[Condition, List[Dict[str, Any]]]:
        """
        提取前置条件
        
        Args:
            description: 任务描述文本
            
        Returns:
            Tuple[Condition, List[Dict]]: (提取的前置条件对象, 处理记录列表)
            
        Raises:
            ConditionExtractionError: 提取失败时抛出
        """
        if not description or not description.strip():
            raise ConditionExtractionError(
                "任务描述不能为空",
                {"field": "description", "value": description}
            )
        
        processing_records = []
        
        cleaned_description = description.strip()
        
        conditions = self._extract_conditions(cleaned_description)
        
        if not conditions:
            default_condition = self._create_default_condition()
            conditions.append(default_condition)
            processing_records.append({
                "step": "默认条件",
                "action": "无明确前置条件，使用默认条件"
            })
        
        condition = Condition(
            conditions=conditions,
            logical_operator="AND"
        )
        
        processing_records.append({
            "step": "最终条件",
            "condition_count": len(conditions),
            "logical_operator": "AND"
        })
        
        return condition, processing_records
    
    def _extract_conditions(self, description: str) -> List[ConditionItem]:
        """
        提取条件列表
        
        Args:
            description: 任务描述
            
        Returns:
            List[ConditionItem]: 提取的条件列表
        """
        conditions = []
        
        for pattern_info in self.condition_patterns:
            matches = re.finditer(pattern_info["pattern"], description)
            for match in matches:
                content = match.group(1).strip()
                if content and len(content) > 0:
                    condition_type = self._classify_type(content)
                    check_rule = self._generate_check_rule(content, condition_type)
                    
                    condition_item = ConditionItem(
                        id=f"C-{uuid.uuid4().hex[:6].upper()}",
                        description=pattern_info["description_template"].format(content=content),
                        type=condition_type,
                        check_rule=check_rule,
                        required=True
                    )
                    conditions.append(condition_item)
        
        unique_conditions = []
        seen_descriptions = set()
        for cond in conditions:
            if cond.description not in seen_descriptions:
                unique_conditions.append(cond)
                seen_descriptions.add(cond.description)
        
        return unique_conditions
    
    def _classify_type(self, content: str) -> str:
        """
        分类条件类型
        
        Args:
            content: 条件内容
            
        Returns:
            str: 条件类型 ('existence' | 'value' | 'state')
        """
        for classifier in self.type_classifiers:
            for keyword in classifier["keywords"]:
                if keyword in content:
                    return classifier["type"]
        
        return "existence"
    
    def _generate_check_rule(self, content: str, condition_type: str) -> str:
        """
        生成机器可判定规则
        
        Args:
            content: 条件内容
            condition_type: 条件类型
            
        Returns:
            str: 检查规则字符串
        """
        for classifier in self.type_classifiers:
            if classifier["type"] == condition_type:
                return classifier["rule_template"].format(content=content)
        
        return f"check_condition('{content}')"
    
    def _create_default_condition(self) -> ConditionItem:
        """
        创建默认条件
        
        Returns:
            ConditionItem: 默认条件项
        """
        return ConditionItem(
            id=f"C-{uuid.uuid4().hex[:6].upper()}",
            description="任务开始执行",
            type="state",
            check_rule="True",
            required=False
        )


def extract_condition(description: str) -> Tuple[Condition, List[Dict[str, Any]]]:
    """
    提取前置条件的便捷函数
    
    Args:
        description: 任务描述
        
    Returns:
        Tuple[Condition, List[Dict]]: (条件对象, 处理记录)
    """
    extractor = ConditionExtractor()
    return extractor.extract(description)


def create_condition_extractor() -> ConditionExtractor:
    """
    创建前置条件提取器的工厂函数
    
    Returns:
        ConditionExtractor: 配置好的提取器实例
    """
    return ConditionExtractor()
