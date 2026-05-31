"""
边界约束识别与写入模块
基于第一性原理的AI Agent任务规划系统
"""

import re
from typing import Optional, List
from dataclasses import dataclass
from .task_struct import Boundary, ScopeBoundary, ResourceBoundary, QualityBoundary


class BoundaryExtractionError(Exception):
    """边界约束提取异常"""
    pass


class BoundaryExtractor:
    """
    边界约束识别与写入单元
    功能：从自然语言描述中自动提取并生成任务边界约束
    """
    
    # 范围边界关键词
    SCOPE_INCLUSION_KEYWORDS = [
        "包含", "包括", "限于", "专注于", "仅", "只", "仅对", "只针对"
    ]
    SCOPE_EXCLUSION_KEYWORDS = [
        "不包含", "不包括", "排除", "除外", "除了", "不涉及", "不考虑"
    ]
    
    # 资源约束关键词
    TIME_KEYWORDS = [
        "最多", "不超过", "不超过", "最多", "至多", "需要", "预计", "大概",
        "小时", "分钟", "秒", "天"
    ]
    COST_KEYWORDS = [
        "预算", "成本", "费用", "花费", "最多", "不超过"
    ]
    ITERATION_KEYWORDS = [
        "最多", "不超过", "最多", "至多", "迭代", "尝试", "循环"
    ]
    
    # 质量约束关键词
    ACCURACY_KEYWORDS = [
        "准确率", "正确率", "精度", "准确度", "最低", "至少"
    ]
    ERROR_RATE_KEYWORDS = [
        "错误率", "故障率", "误差率", "最高", "不超过"
    ]
    
    def __init__(self):
        """初始化边界提取器"""
        pass
    
    def extract(self, description: str) -> Boundary:
        """
        从自然语言描述中提取边界约束
        
        Args:
            description: 用户需求的自然语言描述
            
        Returns:
            Boundary: 完整的边界约束对象
        """
        if not description or not isinstance(description, str):
            raise BoundaryExtractionError("需求描述不能为空")
        
        # 提取各个部分
        scope = self._extract_scope(description)
        resources = self._extract_resources(description)
        quality = self._extract_quality(description)
        
        return Boundary(
            scope=scope,
            resources=resources,
            quality=quality
        )
    
    def _extract_scope(self, description: str) -> ScopeBoundary:
        """
        提取范围边界
        
        Args:
            description: 用户需求描述
            
        Returns:
            ScopeBoundary: 范围边界对象
        """
        inclusions = []
        exclusions = []
        
        # 先处理排除范围（使用更长的关键词，避免被包含关键词优先匹配）
        for keyword in self.SCOPE_EXCLUSION_KEYWORDS:
            # 查找关键词的位置
            idx = 0
            while True:
                idx = description.find(keyword, idx)
                if idx == -1:
                    break
                # 找到关键词后，提取后面的内容直到标点符号
                start = idx + len(keyword)
                end = len(description)
                for punct in ['，', '。', '！', '？', '；', ',', ';', '!', '?', '.']:
                    punct_pos = description.find(punct, start)
                    if punct_pos != -1 and punct_pos < end:
                        end = punct_pos
                content = description[start:end].strip()
                if content:
                    exclusions.append(content)
                idx = end
        
        # 再处理包含范围，同时确保不包含排除关键词
        for keyword in self.SCOPE_INCLUSION_KEYWORDS:
            idx = 0
            while True:
                idx = description.find(keyword, idx)
                if idx == -1:
                    break
                # 检查前面是否是否定词
                is_negative = False
                if idx > 0:
                    for neg_word in ['不', '没']:
                        if idx >= len(neg_word) and description[idx - len(neg_word):idx] == neg_word:
                            is_negative = True
                            break
                if not is_negative:
                    # 提取后面的内容
                    start = idx + len(keyword)
                    end = len(description)
                    for punct in ['，', '。', '！', '？', '；', ',', ';', '!', '?', '.']:
                        punct_pos = description.find(punct, start)
                        if punct_pos != -1 and punct_pos < end:
                            end = punct_pos
                    content = description[start:end].strip()
                    if content:
                        inclusions.append(content)
                idx = end
        
        # 去重
        inclusions = list(set(inclusions))
        exclusions = list(set(exclusions))
        
        # 确保一个项不会同时出现在包含和排除中（排除优先）
        inclusions = [item for item in inclusions if item not in exclusions]
        
        return ScopeBoundary(
            inclusions=inclusions,
            exclusions=exclusions
        )
    
    def _extract_resources(self, description: str) -> ResourceBoundary:
        """
        提取资源约束
        
        Args:
            description: 用户需求描述
            
        Returns:
            ResourceBoundary: 资源约束对象
        """
        max_time_seconds = None
        max_cost = None
        max_iterations = None
        
        # 提取时间约束
        time_patterns = [
            (r'(\d+)\s*小时', 3600),
            (r'(\d+)\s*分钟', 60),
            (r'(\d+)\s*秒', 1),
            (r'(\d+)\s*天', 86400)
        ]
        
        for pattern, multiplier in time_patterns:
            match = re.search(pattern, description)
            if match:
                try:
                    value = float(match.group(1))
                    max_time_seconds = value * multiplier
                    break
                except ValueError:
                    continue
        
        # 如果没有找到明确时间，设置默认值
        if max_time_seconds is None:
            max_time_seconds = 3600.0  # 默认1小时
        
        # 提取成本约束
        cost_pattern = r'(?:预算|成本|费用|花费)\s*(?:最多|不超过)?\s*(\d+)'
        match = re.search(cost_pattern, description)
        if match:
            try:
                max_cost = float(match.group(1))
            except ValueError:
                pass
        
        # 提取迭代次数约束
        iteration_pattern = r'(?:最多|不超过)?\s*(\d+)\s*(?:次|迭代|尝试|循环)'
        match = re.search(iteration_pattern, description)
        if match:
            try:
                max_iterations = int(match.group(1))
            except ValueError:
                pass
        
        # 如果没有找到明确迭代次数，设置默认值
        if max_iterations is None:
            max_iterations = 10
        
        return ResourceBoundary(
            max_time_seconds=max_time_seconds,
            max_cost=max_cost,
            max_iterations=max_iterations
        )
    
    def _extract_quality(self, description: str) -> Optional[QualityBoundary]:
        """
        提取质量约束
        
        Args:
            description: 用户需求描述
            
        Returns:
            Optional[QualityBoundary]: 质量约束对象（可能为None）
        """
        min_accuracy = None
        max_error_rate = None
        other_constraints = []
        
        # 提取准确率约束
        accuracy_patterns = [
            r'(?:准确率|正确率|精度|准确度)\s*(?:至少|不低于|最低)?\s*(\d+(?:\.\d+)?)\s*%',
            r'(\d+(?:\.\d+)?)\s*%\s*(?:准确率|正确率|精度|准确度)'
        ]
        
        for pattern in accuracy_patterns:
            match = re.search(pattern, description)
            if match:
                try:
                    value = float(match.group(1))
                    min_accuracy = value / 100.0
                    break
                except ValueError:
                    continue
        
        # 提取错误率约束
        error_rate_patterns = [
            r'(?:错误率|故障率|误差率)\s*(?:最多|不超过|最高)?\s*(\d+(?:\.\d+)?)\s*%',
            r'(\d+(?:\.\d+)?)\s*%\s*(?:错误率|故障率|误差率)'
        ]
        
        for pattern in error_rate_patterns:
            match = re.search(pattern, description)
            if match:
                try:
                    value = float(match.group(1))
                    max_error_rate = value / 100.0
                    break
                except ValueError:
                    continue
        
        # 如果没有任何质量约束，返回None
        if min_accuracy is None and max_error_rate is None and len(other_constraints) == 0:
            return None
        
        return QualityBoundary(
            min_accuracy=min_accuracy,
            max_error_rate=max_error_rate,
            other_constraints=other_constraints
        )


# 便捷函数
def extract_boundary(description: str) -> Boundary:
    """
    便捷函数：从自然语言描述中提取边界约束
    
    Args:
        description: 用户需求的自然语言描述
        
    Returns:
        Boundary: 完整的边界约束对象
    """
    extractor = BoundaryExtractor()
    return extractor.extract(description)
