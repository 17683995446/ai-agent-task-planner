"""
终止规则解析器 - EndRule机器可判定终止规则解析器
基于第一性原理的AI Agent任务规划系统
"""
import re
from typing import List
from .task_struct import EndRule, SuccessCondition, FailureCondition


class EndRuleExtractionError(Exception):
    """终止规则提取异常"""
    pass


class EndRuleExtractor:
    """
    EndRule终止规则解析器
    功能：从自然语言需求描述中自动提取成功终止条件和失败终止条件
    """
    
    # 成功终止关键词
    SUCCESS_KEYWORDS = [
        "完成", "成功", "达到", "实现", "生成", "创建", "做好", "做完",
        "满足", "达成", "搞定", "结束", "交付", "输出"
    ]
    
    # 失败终止关键词
    FAILURE_KEYWORDS = [
        "超时", "失败", "错误", "异常", "超过", "中断", "停止", "放弃",
        "无法", "不能", "不行", "出错"
    ]
    
    # 时间相关关键词
    TIME_KEYWORDS = [
        "秒", "分钟", "小时", "天"
    ]
    
    def __init__(self):
        """初始化终止规则提取器"""
        pass
    
    def extract(self, description: str) -> EndRule:
        """
        从自然语言描述中提取终止规则
        
        Args:
            description: 用户需求的自然语言描述
            
        Returns:
            EndRule: 完整的终止规则对象
        """
        if not description or not isinstance(description, str):
            raise EndRuleExtractionError("需求描述不能为空")
        
        # 提取成功条件和失败条件
        success_conditions = self._extract_success_conditions(description)
        failure_conditions = self._extract_failure_conditions(description)
        
        # 生成评估逻辑
        evaluation_logic = self._generate_evaluation_logic(success_conditions, failure_conditions)
        
        return EndRule(
            success_conditions=success_conditions,
            failure_conditions=failure_conditions,
            evaluation_logic=evaluation_logic
        )
    
    def _extract_success_conditions(self, description: str) -> List[SuccessCondition]:
        """
        提取成功终止条件
        
        Args:
            description: 用户需求描述
            
        Returns:
            List[SuccessCondition]: 成功终止条件列表
        """
        conditions = []
        
        # 默认成功条件 - 基于目标描述
        conditions.append(SuccessCondition(
            id="SC_DEFAULT",
            description=f"完成任务：{description[:50]}{'...' if len(description) > 50 else ''}",
            check_rule="task_completed() == True"
        ))
        
        # 尝试从描述中提取更具体的成功条件
        for keyword in self.SUCCESS_KEYWORDS:
            pattern = rf'{keyword}([^，。！？；,;!?.]*)'
            matches = re.findall(pattern, description)
            for match in matches:
                match = match.strip()
                if match and len(match) > 2:  # 确保有实际内容
                    cond_id = f"SC_{len(conditions)}"
                    conditions.append(SuccessCondition(
                        id=cond_id,
                        description=f"{keyword}{match}",
                        check_rule=f"check_{keyword}() == True"
                    ))
        
        # 如果没有提取到额外条件，保留默认条件即可
        return conditions[:3]  # 限制数量，避免过多条件
    
    def _extract_failure_conditions(self, description: str) -> List[FailureCondition]:
        """
        提取失败终止条件
        
        Args:
            description: 用户需求描述
            
        Returns:
            List[FailureCondition]: 失败终止条件列表
        """
        conditions = []
        
        # 1. 时间限制条件（优先级最高）
        time_limit = self._extract_time_limit(description)
        if time_limit:
            conditions.append(FailureCondition(
                id="FC_TIMEOUT",
                description=f"执行超时（{time_limit['text']}）",
                check_rule=f"elapsed_time() > {time_limit['seconds']}",
                priority=1
            ))
        
        # 2. 从描述中提取其他失败条件
        for keyword in self.FAILURE_KEYWORDS:
            pattern = rf'{keyword}([^，。！？；,;!?.]*)'
            matches = re.findall(pattern, description)
            for match in matches:
                match = match.strip()
                if match and len(match) > 2:
                    cond_id = f"FC_{len(conditions)}"
                    conditions.append(FailureCondition(
                        id=cond_id,
                        description=f"{keyword}{match}",
                        check_rule=f"check_{keyword}() == True",
                        priority=min(len(conditions) + 1, 10)
                    ))
        
        # 3. 默认失败条件（如果没有提取到任何条件）
        if len(conditions) == 0:
            conditions.append(FailureCondition(
                id="FC_DEFAULT",
                description="执行失败",
                check_rule="task_failed() == True",
                priority=1
            ))
        
        # 4. 添加迭代次数限制
        conditions.append(FailureCondition(
            id="FC_MAX_ITER",
            description="超过最大迭代次数",
            check_rule="iteration_count() >= 10",
            priority=2
        ))
        
        # 5. 添加连续错误限制
        conditions.append(FailureCondition(
            id="FC_CONSEC_ERRORS",
            description="连续错误超过3次",
            check_rule="consecutive_errors() >= 3",
            priority=3
        ))
        
        return conditions
    
    def _extract_time_limit(self, description: str) -> dict:
        """
        从描述中提取时间限制
        
        Args:
            description: 用户需求描述
            
        Returns:
            dict: 包含时间文本和秒数的字典，没有找到返回None
        """
        time_patterns = [
            (r'(\d+)\s*秒', 1),
            (r'(\d+)\s*分钟', 60),
            (r'(\d+)\s*小时', 3600),
            (r'(\d+)\s*天', 86400)
        ]
        
        for pattern, multiplier in time_patterns:
            match = re.search(pattern, description)
            if match:
                try:
                    value = float(match.group(1))
                    return {
                        'text': match.group(0),
                        'seconds': value * multiplier
                    }
                except ValueError:
                    continue
        
        # 默认1小时
        return {
            'text': '1小时',
            'seconds': 3600.0
        }
    
    def _generate_evaluation_logic(self, success_conditions: List[SuccessCondition], 
                                   failure_conditions: List[FailureCondition]) -> str:
        """
        生成评估逻辑字符串
        
        Args:
            success_conditions: 成功条件列表
            failure_conditions: 失败条件列表
            
        Returns:
            str: 评估逻辑字符串
        """
        success_ids = [sc.id for sc in success_conditions]
        failure_ids = [fc.id for fc in failure_conditions]
        
        success_logic = " AND ".join(success_ids) if success_ids else ""
        failure_logic = " OR ".join(failure_ids) if failure_ids else ""
        
        return f"success: ({success_logic}); failure: ({failure_logic})"


# 便捷函数
def extract_end_rule(description: str) -> EndRule:
    """
    便捷函数：从自然语言描述中提取终止规则
    
    Args:
        description: 用户需求的自然语言描述
        
    Returns:
        EndRule: 完整的终止规则对象
    """
    extractor = EndRuleExtractor()
    return extractor.extract(description)
