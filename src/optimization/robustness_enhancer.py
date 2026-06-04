"""
系统鲁棒性增强模块
基于第一性原理的AI Agent任务规划系统

核心功能：
- 四元组解析容错增强
- 复杂任务拓扑拆解鲁棒性提升
- 原子动作拆分粒度参数精细化
- 动态阈值适配
"""

import re
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass


class RobustnessEnhancer:
    """
    鲁棒性增强器
    
    功能：
    - 优化四元组解析容错、抗歧义能力（阶段66）
    - 提升复杂任务拓扑拆解鲁棒性（阶段67）
    - 精细化原子动作拆分粒度参数（阶段68）
    - 适配简单/中等/复杂任务动态阈值（阶段69）
    """
    
    def __init__(self):
        """初始化鲁棒性增强器"""
        # 动态阈值配置
        self.thresholds = {
            "simple": {
                "max_subtasks": 3,
                "max_atomic_actions": 10,
                "complexity_score": 0.3,
                "parse_tolerance": 0.8
            },
            "medium": {
                "max_subtasks": 8,
                "max_atomic_actions": 25,
                "complexity_score": 0.6,
                "parse_tolerance": 0.6
            },
            "complex": {
                "max_subtasks": 15,
                "max_atomic_actions": 50,
                "complexity_score": 0.9,
                "parse_tolerance": 0.4
            }
        }
    
    def evaluate_complexity(self, requirement: str) -> str:
        """
        评估任务复杂度
        
        Args:
            requirement: 需求描述
            
        Returns:
            str: 复杂度等级 (simple/medium/complex)
        """
        score = 0
        
        # 长度因子
        length = len(requirement)
        if length > 200:
            score += 0.4
        elif length > 100:
            score += 0.2
        
        # 关键词因子
        complex_keywords = ['微服务', '分布式', '高并发', '高可用', '企业级', '完整', '系统', '平台']
        medium_keywords = ['功能', '模块', '管理', '服务', '接口']
        
        for keyword in complex_keywords:
            if keyword in requirement:
                score += 0.1
        
        for keyword in medium_keywords:
            if keyword in requirement:
                score += 0.05
        
        # 标点因子（逗号数量表示复杂度）
        comma_count = requirement.count('，') + requirement.count(',')
        score += min(comma_count * 0.05, 0.3)
        
        # 确定复杂度
        if score >= 0.6:
            return "complex"
        elif score >= 0.3:
            return "medium"
        else:
            return "simple"
    
    def get_thresholds(self, complexity: str) -> Dict[str, Any]:
        """
        获取对应复杂度的阈值
        
        Args:
            complexity: 复杂度等级
            
        Returns:
            Dict[str, Any]: 阈值配置
        """
        return self.thresholds.get(complexity, self.thresholds["medium"])
    
    def enhance_parsing(self, requirement: str) -> Dict[str, Any]:
        """
        增强解析容错能力
        
        Args:
            requirement: 需求描述
            
        Returns:
            Dict[str, Any]: 解析增强结果
        """
        complexity = self.evaluate_complexity(requirement)
        thresholds = self.get_thresholds(complexity)
        
        # 清洗和标准化输入
        cleaned = self._clean_input(requirement)
        
        # 提取关键信息（容错处理）
        target = self._extract_target_robust(cleaned)
        conditions = self._extract_conditions_robust(cleaned)
        boundary = self._extract_boundary_robust(cleaned)
        
        return {
            "complexity": complexity,
            "thresholds": thresholds,
            "cleaned_requirement": cleaned,
            "extracted": {
                "target": target,
                "conditions": conditions,
                "boundary": boundary
            }
        }
    
    def _clean_input(self, requirement: str) -> str:
        """清洗输入"""
        # 去除多余空格
        cleaned = re.sub(r'\s+', ' ', requirement)
        # 去除特殊字符
        cleaned = re.sub(r'[^\w\s\u4e00-\u9fff，。、；：？！""''（）《》【】]', '', cleaned)
        return cleaned.strip()
    
    def _extract_target_robust(self, requirement: str) -> str:
        """鲁棒性目标提取"""
        # 尝试多种提取策略
        patterns = [
            r'(?:开发|设计|实现|创建|构建)\s*一个?\s*(.+?)(?:，|。|$)',
            r'(.+?)(?:系统|平台|功能|模块|服务)',
            r'^(.+?)(?:，|。|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, requirement)
            if match:
                return match.group(1).strip()
        
        return requirement[:50]
    
    def _extract_conditions_robust(self, requirement: str) -> List[str]:
        """鲁棒性条件提取"""
        conditions = []
        
        # 提取包含、支持、需要等关键词后的内容
        patterns = [
            r'(?:支持|包含|需要|要求|必须)\s*(.+?)(?:，|。|$)',
            r'(?:包括|涵盖|涉及)\s*(.+?)(?:，|。|$)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, requirement)
            conditions.extend(matches)
        
        return conditions if conditions else ["无特殊条件"]
    
    def _extract_boundary_robust(self, requirement: str) -> Dict[str, Any]:
        """鲁棒性边界提取"""
        boundary = {
            "time_limit": None,
            "resource_limit": None,
            "scope_limit": None
        }
        
        # 时间限制
        time_patterns = [
            r'(\d+)\s*(?:天|周|月|年)',
            r'(\d+)\s*(?:day|week|month|year)'
        ]
        for pattern in time_patterns:
            match = re.search(pattern, requirement)
            if match:
                boundary["time_limit"] = match.group(0)
                break
        
        # 资源限制
        resource_patterns = [
            r'(?:预算|成本|费用)\s*(\d+)',
            r'(?:人员|团队)\s*(\d+)'
        ]
        for pattern in resource_patterns:
            match = re.search(pattern, requirement)
            if match:
                boundary["resource_limit"] = match.group(0)
                break
        
        return boundary
    
    def enhance_topology_split(self, subtasks: List[Any], complexity: str) -> List[Any]:
        """
        增强拓扑拆解鲁棒性
        
        Args:
            subtasks: 子任务列表
            complexity: 复杂度等级
            
        Returns:
            List[Any]: 增强后的子任务列表
        """
        thresholds = self.get_thresholds(complexity)
        max_subtasks = thresholds["max_subtasks"]
        
        # 如果子任务过多，进行合并
        if len(subtasks) > max_subtasks:
            # 简单的合并策略：将相邻子任务合并
            merged = []
            merge_size = len(subtasks) // max_subtasks + 1
            
            for i in range(0, len(subtasks), merge_size):
                group = subtasks[i:i + merge_size]
                if len(group) > 1:
                    # 合并子任务
                    merged_task = self._merge_subtasks(group)
                    merged.append(merged_task)
                else:
                    merged.extend(group)
            
            return merged
        
        return subtasks
    
    def _merge_subtasks(self, subtasks: List[Any]) -> Any:
        """合并子任务"""
        # 简化实现：返回第一个子任务（实际应该创建新的合并子任务）
        if subtasks:
            return subtasks[0]
        return None
    
    def enhance_atomic_split(self, actions: List[Any], complexity: str) -> List[Any]:
        """
        增强原子拆分粒度
        
        Args:
            actions: 动作列表
            complexity: 复杂度等级
            
        Returns:
            List[Any]: 增强后的动作列表
        """
        thresholds = self.get_thresholds(complexity)
        max_actions = thresholds["max_atomic_actions"]
        
        # 如果动作过多，进行粒度调整
        if len(actions) > max_actions:
            # 简单的调整策略：合并相似动作
            adjusted = []
            
            for action in actions:
                # 检查是否可以合并到已有动作
                merged = False
                for existing in adjusted:
                    if self._is_similar_action(action, existing):
                        merged = True
                        break
                
                if not merged:
                    adjusted.append(action)
            
            return adjusted
        
        return actions
    
    def _is_similar_action(self, action1: Any, action2: Any) -> bool:
        """判断两个动作是否相似"""
        # 简化实现：比较名称相似度
        name1 = getattr(action1, 'name', str(action1))
        name2 = getattr(action2, 'name', str(action2))
        
        # 如果名称相同或包含关系，认为相似
        return name1 == name2 or name1 in name2 or name2 in name1


# 便捷函数
def enhance_requirement(requirement: str) -> Dict[str, Any]:
    """
    增强需求解析
    
    Args:
        requirement: 需求描述
        
    Returns:
        Dict[str, Any]: 增强结果
    """
    enhancer = RobustnessEnhancer()
    return enhancer.enhance_parsing(requirement)


# 使用示例
if __name__ == "__main__":
    print("=" * 60)
    print("鲁棒性增强模块 - 使用示例")
    print("=" * 60)
    
    enhancer = RobustnessEnhancer()
    
    test_cases = [
        "开发一个用户登录系统",
        "设计一个电商网站的完整购物流程，支持商品浏览、搜索、加入购物车、结算、支付、订单跟踪",
        "设计并实现一个完整的微服务架构电商平台，包括用户服务、商品服务、订单服务、支付服务、库存服务、物流服务，要求支持高并发、高可用、数据一致性"
    ]
    
    for requirement in test_cases:
        print(f"\n需求: {requirement[:50]}...")
        
        # 评估复杂度
        complexity = enhancer.evaluate_complexity(requirement)
        print(f"  复杂度: {complexity}")
        
        # 获取阈值
        thresholds = enhancer.get_thresholds(complexity)
        print(f"  阈值: {thresholds}")
        
        # 增强解析
        result = enhancer.enhance_parsing(requirement)
        print(f"  提取目标: {result['extracted']['target'][:30]}...")
        print(f"  条件数: {len(result['extracted']['conditions'])}")
    
    print("\n" + "=" * 60)
    print("鲁棒性增强模块 - 示例完成")
    print("=" * 60)
