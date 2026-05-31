"""
目标提取与归一化模块
基于第一性原理的AI Agent任务规划系统
"""

import re
import uuid
from typing import Dict, List, Any, Tuple, Optional
from .task_struct import Target, MeasurableCriterion


class TargetExtractionError(Exception):
    """目标提取错误异常"""
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


class TargetExtractor:
    """唯一目标提取器 - 实现歧义剔除和目标归一"""
    
    def __init__(self):
        """初始化目标提取器"""
        self.vague_patterns = self._init_vague_patterns()
        self.ambiguity_patterns = self._init_ambiguity_patterns()
        self.normalization_rules = self._init_normalization_rules()
    
    def _init_vague_patterns(self) -> List[Dict[str, Any]]:
        """初始化模糊词模式"""
        return [
            {
                "pattern": r'[大小]概|可能|也许|大概|大约',
                "type": "模糊程度",
                "suggestion": "使用精确的描述替代模糊词"
            },
            {
                "pattern": r'[尽]量|尽可能|尽力',
                "type": "模糊努力",
                "suggestion": "明确具体的完成标准"
            },
            {
                "pattern": r'[合]适|[正]好|适当',
                "type": "模糊标准",
                "suggestion": "使用可量化的标准"
            },
            {
                "pattern": r'好[一]点|好[些]',
                "type": "模糊质量",
                "suggestion": "明确质量要求的具体数值"
            },
            {
                "pattern": r'[尽]快|尽快|马上|立刻',
                "type": "模糊时间",
                "suggestion": "明确具体的时间要求"
            }
        ]
    
    def _init_ambiguity_patterns(self) -> List[Dict[str, Any]]:
        """初始化歧义模式"""
        return [
            {
                "keywords": ["和", "以及", "与", "并且"],
                "type": "并列多目标",
                "action": "split"
            },
            {
                "keywords": ["然后"],
                "type": "顺序多目标",
                "action": "sequence"
            }
        ]
    
    def _init_normalization_rules(self) -> List[Dict[str, Any]]:
        """初始化归一化规则"""
        return [
            {
                "from": r'创建\s*',
                "to": '创建'
            },
            {
                "from": r'生成\s*',
                "to": '生成'
            },
            {
                "from": r'完成\s*',
                "to": '完成'
            },
            {
                "from": r'制作\s*',
                "to": '制作'
            },
            {
                "from": r'编写\s*',
                "to": '编写'
            },
            {
                "from": r'\s+',
                "to": ' '
            }
        ]
    
    def extract(self, description: str) -> Tuple[Target, List[Dict[str, Any]]]:
        """
        提取唯一目标
        
        Args:
            description: 目标描述文本
            
        Returns:
            Tuple[Target, List[Dict]]: (提取的目标对象, 处理记录列表)
            
        Raises:
            TargetExtractionError: 提取失败时抛出
        """
        if not description or not description.strip():
            raise TargetExtractionError(
                "目标描述不能为空",
                {"field": "description", "value": description}
            )
        
        processing_records = []
        
        cleaned_description = description.strip()
        
        ambiguities = self._detect_ambiguity(cleaned_description)
        if ambiguities:
            processing_records.append({
                "step": "歧义检测",
                "detected": ambiguities
            })
            cleaned_description = self._resolve_ambiguity(cleaned_description, ambiguities)
        
        vague_words = self._detect_vague_words(cleaned_description)
        if vague_words:
            processing_records.append({
                "step": "模糊词检测",
                "detected": vague_words
            })
            cleaned_description = self._remove_vague_words(cleaned_description, vague_words)
        
        normalized_description = self._normalize(cleaned_description)
        if normalized_description != cleaned_description:
            processing_records.append({
                "step": "归一化处理",
                "before": cleaned_description,
                "after": normalized_description
            })
            cleaned_description = normalized_description
        
        unique_target = self._extract_unique_target(cleaned_description)
        
        target_id = f"T-{uuid.uuid4().hex[:8].upper()}"
        measurable_criteria = self._extract_measurable_criteria(cleaned_description)
        
        target = Target(
            id=target_id,
            description=unique_target,
            measurable_criteria=measurable_criteria,
            priority=5
        )
        
        processing_records.append({
            "step": "最终目标",
            "value": unique_target,
            "criteria_count": len(measurable_criteria)
        })
        
        return target, processing_records
    
    def _detect_ambiguity(self, description: str) -> List[Dict[str, Any]]:
        """
        检测歧义
        
        Args:
            description: 目标描述
            
        Returns:
            List[Dict]: 检测到的歧义列表
        """
        ambiguities = []
        
        for pattern_info in self.ambiguity_patterns:
            for keyword in pattern_info["keywords"]:
                if keyword in description:
                    idx = description.index(keyword)
                    before = description[:idx].strip()
                    after = description[idx + len(keyword):].strip()
                    
                    ambiguities.append({
                        "type": pattern_info["type"],
                        "action": pattern_info["action"],
                        "keyword": keyword,
                        "before": before,
                        "after": after,
                        "position": idx
                    })
        
        return ambiguities
    
    def _resolve_ambiguity(self, description: str, ambiguities: List[Dict[str, Any]]) -> str:
        """
        解决歧义
        
        Args:
            description: 原始描述
            ambiguities: 检测到的歧义列表
            
        Returns:
            str: 解决歧义后的描述
        """
        resolved = description
        
        for ambiguity in ambiguities:
            if ambiguity["action"] == "split":
                before = ambiguity["before"]
                if before:
                    resolved = before
                    
            elif ambiguity["action"] == "sequence":
                before = ambiguity["before"]
                if before:
                    resolved = before
        
        return resolved.strip()
    
    def _detect_vague_words(self, description: str) -> List[Dict[str, Any]]:
        """
        检测模糊词
        
        Args:
            description: 目标描述
            
        Returns:
            List[Dict]: 检测到的模糊词列表
        """
        vague_words = []
        
        for pattern_info in self.vague_patterns:
            matches = re.finditer(pattern_info["pattern"], description)
            for match in matches:
                vague_words.append({
                    "word": match.group(0),
                    "type": pattern_info["type"],
                    "suggestion": pattern_info["suggestion"],
                    "position": match.span()
                })
        
        return vague_words
    
    def _remove_vague_words(self, description: str, vague_words: List[Dict[str, Any]]) -> str:
        """
        移除模糊词
        
        Args:
            description: 原始描述
            vague_words: 检测到的模糊词列表
            
        Returns:
            str: 移除模糊词后的描述
        """
        cleaned = description
        
        for vague in vague_words:
            cleaned = cleaned.replace(vague["word"], "")
        
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        return cleaned
    
    def _normalize(self, description: str) -> str:
        """
        目标归一化
        
        Args:
            description: 描述文本
            
        Returns:
            str: 归一化后的描述
        """
        normalized = description
        
        for rule in self.normalization_rules:
            normalized = re.sub(rule["from"], rule["to"], normalized)
        
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def _extract_unique_target(self, description: str) -> str:
        """
        提取唯一目标
        
        Args:
            description: 归一化后的描述
            
        Returns:
            str: 唯一目标描述
        """
        action_verbs = ["生成", "创建", "完成", "制作", "编写", "分析", "处理", "获取", "提取"]
        
        target = description
        for verb in action_verbs:
            if verb in description:
                idx = description.index(verb)
                target = description[idx:]
                break
        
        return target
    
    def _extract_measurable_criteria(self, description: str) -> List[MeasurableCriterion]:
        """
        提取可衡量标准
        
        Args:
            description: 目标描述
            
        Returns:
            List[MeasurableCriterion]: 可衡量标准列表
        """
        criteria = []
        
        page_match = re.search(r'(\d+)\s*页', description)
        if page_match:
            page_count = int(page_match.group(1))
            criteria.append(MeasurableCriterion(
                id=f"MC-{uuid.uuid4().hex[:6].upper()}",
                description=f"报告页数>={page_count}页",
                type="numeric",
                threshold=page_count,
                unit="页"
            ))
        
        data_keywords = ["数据", "信息", "内容", "资料"]
        if any(kw in description for kw in data_keywords):
            criteria.append(MeasurableCriterion(
                id=f"MC-{uuid.uuid4().hex[:6].upper()}",
                description="包含完整必要数据",
                type="boolean",
                threshold=True
            ))
        
        chart_match = re.search(r'(\d+)\s*[张幅]?\s*图', description)
        if chart_match:
            chart_count = int(chart_match.group(1))
            criteria.append(MeasurableCriterion(
                id=f"MC-{uuid.uuid4().hex[:6].upper()}",
                description=f"包含至少{chart_count}张图表",
                type="numeric",
                threshold=chart_count,
                unit="张"
            ))
        
        if not criteria:
            criteria.append(MeasurableCriterion(
                id=f"MC-{uuid.uuid4().hex[:6].upper()}",
                description="任务完成",
                type="boolean",
                threshold=True
            ))
        
        return criteria


def extract_target(description: str) -> Tuple[Target, List[Dict[str, Any]]]:
    """
    提取唯一目标的便捷函数
    
    Args:
        description: 目标描述
        
    Returns:
        Tuple[Target, List[Dict]]: (目标对象, 处理记录)
    """
    extractor = TargetExtractor()
    return extractor.extract(description)


def create_extractor() -> TargetExtractor:
    """
    创建目标提取器的工厂函数
    
    Returns:
        TargetExtractor: 配置好的提取器实例
    """
    return TargetExtractor()
